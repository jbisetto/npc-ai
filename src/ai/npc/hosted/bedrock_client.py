"""
Bedrock client for hosted request processing.

This module provides a client for interacting with AWS Bedrock for
processing requests that require advanced language models.
"""

import logging
import json
import asyncio
import boto3
from typing import Dict, Any, Optional, List
from datetime import datetime
from botocore.config import Config

from src.ai.npc.core.models import (
    ClassifiedRequest,
    CompanionRequest,
    ProcessingTier
)
from src.ai.npc.core.prompt_manager import PromptManager
from src.ai.npc.hosted.usage_tracker import UsageTracker
from src.ai.npc.config import get_config, CLOUD_API_CONFIG

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
        stop_sequences: Optional[List[str]] = None
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
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.usage_tracker = usage_tracker
        self.model_id = model_id or self.config.get('model_id', 'anthropic.claude-3-sonnet-20240229-v1:0')
        self.max_tokens = max_tokens or self.config.get('max_tokens', 1000)
        self.temperature = temperature or self.config.get('temperature', 0.7)
        self.top_p = top_p or self.config.get('top_p', 0.95)
        self.top_k = top_k or self.config.get('top_k', 40)
        self.stop_sequences = stop_sequences or self.config.get('stop_sequences', [])
        
        # Initialize AWS client
        self.client = boto3.client(
            'bedrock-runtime',
            region_name=self.config.get('region_name', 'us-west-2'),
            config=Config(
                retries={'max_attempts': 3},
                connect_timeout=5,
                read_timeout=30
            )
        )
        
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
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
        
        # Placeholder for actual Bedrock integration
        self.logger.info(f"Would send to Bedrock: {prompt[:100]}...")
        return f"Response to: {prompt[:50]}..."
        
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
