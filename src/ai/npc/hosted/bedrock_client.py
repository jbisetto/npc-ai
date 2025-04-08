"""
Bedrock client for hosted request processing.

This module provides a client for interacting with AWS Bedrock for
processing requests that require advanced language models.
"""

import logging
import json
import asyncio
import boto3
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from botocore.config import Config
from dotenv import load_dotenv

from src.ai.npc.core.models import (
    ClassifiedRequest,
    CompanionRequest,
    ProcessingTier
)
from src.ai.npc.core.prompt_manager import PromptManager
from src.ai.npc.hosted.usage_tracker import UsageTracker
from src.ai.npc.config import get_config, CLOUD_API_CONFIG

# Determine the project root and load environment variables from .env file
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)
logger = logging.getLogger(__name__)

class BedrockError(Exception):
    """
    Exception raised for errors in the Bedrock client.

    Attributes:
        message: The error message.
        error_type: The type of error.
    """

    # Error types
    CONNECTION_ERROR = "CONNECTION_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    MODEL_ERROR = "MODEL_ERROR"
    CONTENT_ERROR = "CONTENT_ERROR"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    QUOTA_ERROR = "QUOTA_ERROR"  # Added for quota/throttling errors

    def __init__(self, message: str, error_type: Optional[str] = None):
        """Initialize the error."""
        super().__init__(message)
        self.message = message
        self.error_type = error_type or "UNKNOWN_ERROR"

class BedrockClient:
    """Client for interacting with AWS Bedrock."""
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        usage_tracker: Optional['UsageTracker'] = None,
        model_id: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        debug_mode: bool = False
    ):
        """
        Initialize the Bedrock client.
        
        Args:
            config: Optional configuration for the client
            usage_tracker: Optional usage tracker for monitoring API usage
            model_id: The model ID to use
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for response generation
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            stop_sequences: List of sequences to stop generation at
            debug_mode: When True, returns simulated responses instead of calling the actual API
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.usage_tracker = usage_tracker
        
        # Get hosted and bedrock configurations
        hosted_config = get_config('hosted', {})
        bedrock_config = hosted_config.get('bedrock', {})
        
        # Prioritize explicitly passed parameters, then environment variables, then config settings
        self.model_id = model_id or os.getenv('BEDROCK_MODEL_ID') or bedrock_config.get('default_model')
        self.max_tokens = max_tokens or bedrock_config.get('max_tokens')
        self.temperature = temperature or bedrock_config.get('temperature')
        self.top_p = top_p or bedrock_config.get('top_p')
        self.top_k = top_k or bedrock_config.get('top_k')
        self.stop_sequences = stop_sequences or bedrock_config.get('stop_sequences', [])
        self.debug_mode = debug_mode or hosted_config.get('debug_mode', False)
        
        # Get AWS region from environment variables or config
        region_name = os.getenv('AWS_REGION') or os.getenv('AWS_DEFAULT_REGION') or bedrock_config.get('region_name')
        
        # Check if AWS credentials are configured
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        # Detailed logging to help diagnose environment variable issues
        self.logger.info(f"Environment variable check results:")
        self.logger.info(f"  .env file path: {env_path}")
        self.logger.info(f"  .env file exists: {env_path.exists()}")
        self.logger.info(f"  AWS_REGION: {os.getenv('AWS_REGION')}")
        self.logger.info(f"  AWS_DEFAULT_REGION: {os.getenv('AWS_DEFAULT_REGION')}")
        self.logger.info(f"  AWS_ACCESS_KEY_ID found: {aws_access_key_id is not None}")
        self.logger.info(f"  AWS_SECRET_ACCESS_KEY found: {aws_secret_access_key is not None}")
        self.logger.info(f"  BEDROCK_MODEL_ID: {os.getenv('BEDROCK_MODEL_ID')}")
        
        # If credentials are not set and not in debug mode, warn and force debug mode
        if not (aws_access_key_id and aws_secret_access_key) and not self.debug_mode:
            self.logger.warning("AWS credentials not found in environment variables. Forcing debug mode.")
            self.debug_mode = True
        
        # Log the model and region that will be used
        self.logger.info(f"Bedrock configuration: model_id={self.model_id}, region={region_name}")
        
        # Initialize AWS client if not in debug mode
        if not self.debug_mode:
            try:
                # Add detailed logging for debugging credential issues
                self.logger.info(f"Initializing Bedrock client with region: {region_name}")
                
                # Log all credential sources to help diagnose issues
                self.logger.debug("AWS credential sources:")
                self.logger.debug(f"  Environment variables: AWS_ACCESS_KEY_ID={'*****' if aws_access_key_id else 'Not found'}")
                self.logger.debug(f"  Environment variables: AWS_SECRET_ACCESS_KEY={'*****' if aws_secret_access_key else 'Not found'}")
                
                # Check for ~/.aws/credentials and ~/.aws/config
                aws_credentials_path = os.path.expanduser("~/.aws/credentials")
                aws_config_path = os.path.expanduser("~/.aws/config")
                self.logger.debug(f"  AWS credentials file exists: {os.path.exists(aws_credentials_path)}")
                self.logger.debug(f"  AWS config file exists: {os.path.exists(aws_config_path)}")
                
                # Validate credentials aren't hardcoded
                if aws_access_key_id and (aws_access_key_id != "your_access_key_here"):
                    from_code = any(file.endswith(".py") for file in os.environ.get("_", "").split("/"))
                    if from_code:
                        self.logger.warning("SECURITY WARNING: AWS credentials appear to be hardcoded! Credentials should only be in .env or AWS credential files.")
                
                # Create the boto3 client with explicit credentials
                self.logger.info("Creating boto3 client with explicit credentials from environment")
                self.client = boto3.client(
                    'bedrock-runtime',
                    region_name=region_name,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    config=Config(
                        retries={'max_attempts': 3},
                        connect_timeout=5,
                        read_timeout=30
                    )
                )
                
                # Try a simple API call to verify credentials
                try:
                    self.logger.info("Testing AWS credentials with a simple API call...")
                    # Call list_foundation_models which requires minimal permissions
                    # Note: bedrock-runtime doesn't have list_foundation_models, so create a regular bedrock client
                    test_client = boto3.client(
                        'bedrock', 
                        region_name=region_name,
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key
                    )
                    response = test_client.list_foundation_models(
                        byOutputModality='TEXT'
                    )
                    self.logger.info(f"Credential test successful. Found {len(response.get('modelSummaries', []))} text models")
                except Exception as api_test_error:
                    self.logger.error(f"Credential test failed: {api_test_error}")
                
                self.logger.info("Initialized Bedrock client successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Bedrock client: {e}", exc_info=True)
                self.client = None
                self.debug_mode = True
        else:
            self.logger.warning("Running in debug mode - using simulated responses")
            self.client = None
        
    async def generate(
        self,
        prompt: str,
        max_tokens: int = None,
        temperature: float = None,
        model_id: str = None
    ) -> str:
        """
        Generate a response using Bedrock.
        
        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for response generation
            model_id: The model ID to use
            
        Returns:
            The generated response
        """
        # Log the prompt for debugging
        self.logger.debug(f"Sending prompt to Bedrock:\n{prompt}")
        
        # Use provided values or fall back to instance defaults
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature
        model_id = model_id or self.model_id
        
        # Handle debug mode
        if self.debug_mode:
            self.logger.info("Debug mode active - returning simulated response")
            # Return a simulated response that includes both Japanese and English
            return """<thinking>
This is a test response for the debug mode. I'll create a response in both English and Japanese that follows the format guidelines.
</thinking>

English: Hello! I'm Hachiko, the dog at the station. How can I help you today?
Japanese: こんにちは！駅の犬のハチコです。今日はどうしましたか？
Pronunciation: kon-ni-chi-wa! e-ki no i-nu no ha-chi-ko de-su. kyo-u wa do-u shi-ma-shi-ta ka?"""
        
        # Check if client is initialized
        if not self.client:
            self.logger.error("Bedrock client not initialized")
            return "Error: Bedrock client not initialized. Check AWS credentials and configuration."
        
        # Create the request body based on the model type
        if not model_id:
            self.logger.warning("No model ID provided, cannot generate response")
            return "Error: No model ID provided for Bedrock"
            
        self.logger.info(f"Generating response with model: {model_id}")
        
        # Placeholder for request body
        request_body = {}
        
        if "anthropic" in model_id or "claude" in model_id:
            # Format for Claude models
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            self.logger.debug(f"Using Claude request format: {json.dumps(request_body, indent=2)}")
        elif "nova" in model_id:
            # Format for Amazon Nova models - verified working format for Nova Micro
            request_body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            self.logger.debug(f"Using Nova request format: {json.dumps(request_body, indent=2)}")
        elif "titan" in model_id or "amazon" in model_id:
            # Format for Amazon Titan models
            request_body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens,
                    "temperature": temperature,
                    "topP": self.top_p
                }
            }
            self.logger.debug(f"Using Titan request format: {json.dumps(request_body, indent=2)}")
        else:
            # Generic format for other models
            self.logger.warning(f"Unknown model type for {model_id}, using generic format")
            request_body = {
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": self.top_p
            }
            self.logger.debug(f"Using generic request format: {json.dumps(request_body, indent=2)}")
        
        try:
            # Call the Bedrock API
            response_body = await self._invoke_model(model_id, request_body)
            
            # Log response structure for debugging
            self.logger.debug(f"Response keys: {list(response_body.keys())}")
            self.logger.debug(f"Response structure: {json.dumps(response_body, default=str)[:500]}...")
            
            # Extract the response text based on the model type
            if "anthropic" in model_id or "claude" in model_id:
                # Claude response format
                return response_body.get("content", [{"text": "No response from model"}])[0].get("text", "")
            elif "nova" in model_id:
                # Nova response format - verified working format for Nova Micro
                try:
                    # Nova models return in format: output.message.content[].text
                    if "output" in response_body:
                        message = response_body.get("output", {}).get("message", {})
                        if "content" in message and isinstance(message["content"], list):
                            text_parts = []
                            for content_item in message["content"]:
                                if "text" in content_item:
                                    text_parts.append(content_item["text"])
                            return "".join(text_parts)
                    
                    # Fallback cases if the format differs
                    self.logger.warning(f"Unexpected Nova response format: {list(response_body.keys())}")
                    if "message" in response_body:
                        message = response_body.get("message", {})
                        if "content" in message and isinstance(message["content"], list):
                            text_parts = []
                            for content_item in message["content"]:
                                if "text" in content_item:
                                    text_parts.append(content_item["text"])
                            return "".join(text_parts)
                    
                    # Last resort fallback
                    return str(response_body)  # Return the whole response if we can't parse it
                except Exception as e:
                    self.logger.error(f"Error parsing Nova response: {e}", exc_info=True)
                    return f"Error parsing Nova response: {str(response_body)}"
            elif "titan" in model_id:
                # Titan response format
                return response_body.get("results", [{"outputText": "No response from model"}])[0].get("outputText", "")
            else:
                # Generic response format
                self.logger.warning(f"Unknown response format for model {model_id}, attempting generic extraction")
                if "generated_text" in response_body:
                    return response_body.get("generated_text")
                elif "completion" in response_body:
                    return response_body.get("completion")
                elif "results" in response_body and len(response_body["results"]) > 0:
                    return response_body["results"][0].get("outputText", "No response extracted")
                else:
                    return str(response_body)  # Return the whole response as a string if we can't parse it
                
        except BedrockError as e:
            self.logger.error(f"Error generating response: {e}")
            return f"Error generating response: {e.message}"
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return "An unexpected error occurred while generating a response."
        
    def process_request(self, request: ClassifiedRequest) -> Dict[str, Any]:
        """
        Process a request using Bedrock.
        
        Args:
            request: The request to process
            
        Returns:
            The processed response
        """
        # Only process hosted requests
        if request.processing_tier != ProcessingTier.HOSTED:
            self.logger.warning(f"Received non-hosted request: {request.processing_tier}")
            return {"error": "Only hosted requests can be processed by Bedrock"}
            
        # Create prompt based on request
        prompt = self._create_prompt(request)
        
        # Process with Bedrock
        response = self.generate_sync(prompt)
        
        return {"response": response}
        
    def generate_sync(self, prompt: str) -> str:
        """
        Generate a response synchronously.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            The generated response
        """
        # Placeholder for synchronous generation
        self.logger.info(f"Would send to Bedrock sync: {prompt[:100]}...")
        return f"Sync response to: {prompt[:50]}..."
        
    def _create_prompt(self, request: ClassifiedRequest) -> str:
        """
        Create a prompt for the request.
        
        Args:
            request: The request to create a prompt for
            
        Returns:
            The prompt to send to the model
        """
        return PromptManager.create_base_prompt(request)

    async def _invoke_model(self, model: str, request_body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke a Bedrock model.

        Args:
            model: The model to invoke.
            request_body: The request body.

        Returns:
            The model's response.

        Raises:
            BedrockError: If an error occurs during invocation.
        """
        try:
            # Convert request body to JSON
            body = json.dumps(request_body)

            # Invoke model
            response = self.client.invoke_model(
                modelId=model,
                contentType='application/json',
                accept='application/json',
                body=body
            )

            # Parse response
            response_body = json.loads(response['body'].read())
            return response_body

        except self.client.exceptions.ValidationException as e:
            logger.error(f"Model validation error: {e}")
            raise BedrockError(f"Model validation error: {e}", BedrockError.MODEL_ERROR)
        except self.client.exceptions.ModelTimeoutException as e:
            logger.error(f"Model timeout: {e}")
            raise BedrockError(f"Model timeout: {e}", BedrockError.TIMEOUT_ERROR)
        except self.client.exceptions.ModelErrorException as e:
            logger.error(f"Model error: {e}")
            raise BedrockError(f"Model error: {e}", BedrockError.MODEL_ERROR)
        except self.client.exceptions.ThrottlingException as e:
            logger.error(f"Throttling error: {e}")
            raise BedrockError(f"Throttling error: {e}", BedrockError.CONNECTION_ERROR)
        except Exception as e:
            logger.error(f"Error invoking model: {e}")
            raise BedrockError(f"Error invoking model: {e}", BedrockError.CONNECTION_ERROR)
