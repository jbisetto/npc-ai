"""
Bedrock client module.

This module provides a client for interacting with AWS Bedrock's language models.
"""

import logging
import json
import asyncio
import boto3
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.ai.npc.core.models import (
    ClassifiedRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)
from src.ai.npc.hosted.prompt_optimizer import create_optimized_prompt
from src.ai.npc.config import get_config

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

    def __init__(self, message: str, error_type: Optional[str] = None):
        """Initialize the error."""
        super().__init__(message)
        self.message = message
        self.error_type = error_type or "UNKNOWN_ERROR"

class BedrockClient:
    """
    Client for interacting with AWS Bedrock's language models.
    """

    def __init__(
        self,
        region_name: Optional[str] = None,
        default_model: Optional[str] = None,
        cache_enabled: bool = True,
        cache_dir: Optional[str] = None,
        cache_ttl: int = 86400,
        max_cache_entries: int = 1000,
        max_cache_size_mb: int = 100
    ):
        """
        Initialize the Bedrock client.

        Args:
            region_name: AWS region name.
            default_model: Default model to use.
            cache_enabled: Whether to enable response caching.
            cache_dir: Directory to store cache files.
            cache_ttl: Cache time-to-live in seconds.
            max_cache_entries: Maximum number of cache entries.
            max_cache_size_mb: Maximum cache size in megabytes.
        """
        # Get configuration
        config = get_config('hosted', {})
        self.region_name = region_name or config.get('region_name', 'us-west-2')
        self.default_model = default_model or config.get('default_model', 'anthropic.claude-v2')
        self.cache_enabled = cache_enabled
        self.cache_dir = cache_dir or config.get('cache_dir', '/tmp/cache')
        self.cache_ttl = cache_ttl
        self.max_cache_entries = max_cache_entries
        self.max_cache_size_mb = max_cache_size_mb

        # Initialize AWS client
        try:
            self.client = boto3.client('bedrock-runtime', region_name=self.region_name)
            logger.info(f"Initialized Bedrock client in region {self.region_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            raise BedrockError(f"Failed to initialize Bedrock client: {e}", BedrockError.CONNECTION_ERROR)

    async def generate(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Generate a response using the specified model.

        Args:
            prompt: The prompt to send to the model.
            model: The model to use (optional).

        Returns:
            The generated response text.

        Raises:
            BedrockError: If an error occurs during generation.
        """
        try:
            # Use default model if none specified
            model = model or self.default_model

            # Create request body
            request_body = {
                "prompt": prompt,
                "max_tokens": 1000,
                "temperature": 0.7,
                "top_p": 0.9,
                "stop_sequences": ["Human:", "Assistant:"]
            }

            # Invoke model
            response = await self._invoke_model(model, request_body)

            # Parse response
            if 'completion' in response:
                return response['completion']
            elif 'generated_text' in response:
                return response['generated_text']
            else:
                raise BedrockError("Invalid response format", BedrockError.INVALID_RESPONSE)

        except BedrockError as e:
            logger.error(f"Bedrock error: {e.message}")
            raise
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise BedrockError(f"Error generating response: {e}", BedrockError.CONNECTION_ERROR)

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
