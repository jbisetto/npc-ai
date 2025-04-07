"""
Ollama client module.

This module provides a client for interacting with Ollama's language models.
"""

import logging
import json
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.ai.npc.core.models import (
    ClassifiedRequest,
    CompanionRequest,
    ProcessingTier
)
from src.ai.npc.core.prompt_manager import PromptManager
from src.ai.npc.config import get_config

logger = logging.getLogger(__name__)

class OllamaError(Exception):
    """
    Exception raised for errors in the Ollama client.

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

class OllamaClient:
    """
    Client for interacting with Ollama's language models.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        cache_enabled: bool = True,
        cache_dir: Optional[str] = None,
        cache_ttl: int = 86400,
        max_cache_entries: int = 1000,
        max_cache_size_mb: int = 100
    ):
        """
        Initialize the Ollama client.

        Args:
            base_url: Base URL for the Ollama API.
            default_model: Default model to use.
            cache_enabled: Whether to enable response caching.
            cache_dir: Directory to store cache files.
            cache_ttl: Cache time-to-live in seconds.
            max_cache_entries: Maximum number of cache entries.
            max_cache_size_mb: Maximum cache size in megabytes.
        """
        # Get configuration
        config = get_config('local', {})
        self.base_url = base_url or config.get('base_url', 'http://localhost:11434')
        self.default_model = default_model or config.get('default_model', 'deepseek-r1:latest')
        self.cache_enabled = cache_enabled
        self.cache_dir = cache_dir or config.get('cache_dir', '/tmp/cache')
        self.cache_ttl = cache_ttl
        self.max_cache_entries = max_cache_entries
        self.max_cache_size_mb = max_cache_size_mb

        # Initialize session
        self.session = None
        logger.info(f"Initialized Ollama client with base URL {self.base_url}")

    async def generate(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Generate a response using the specified model.

        Args:
            prompt: The prompt to send to the model.
            model: The model to use (optional).

        Returns:
            The generated response text.

        Raises:
            OllamaError: If an error occurs during generation.
        """
        try:
            # Use default model if none specified
            model = model or self.default_model

            # Create request body
            request_body = {
                "prompt": prompt,
                "model": model,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "stop": ["Human:", "Assistant:"]
                }
            }

            # Send request
            response = await self._send_request("generate", request_body)

            # Parse response
            if 'response' in response:
                return response['response']
            else:
                raise OllamaError("Invalid response format", OllamaError.INVALID_RESPONSE)

        except OllamaError as e:
            logger.error(f"Ollama error: {e.message}")
            raise
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise OllamaError(f"Error generating response: {e}", OllamaError.CONNECTION_ERROR)

    async def _send_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a request to the Ollama API.

        Args:
            endpoint: The API endpoint to call.
            data: The request data.

        Returns:
            The response data.

        Raises:
            OllamaError: If an error occurs during the request.
        """
        try:
            # Create session if needed
            if self.session is None:
                self.session = aiohttp.ClientSession()

            # Send request
            url = f"{self.base_url}/api/{endpoint}"
            async with self.session.post(url, json=data) as response:
                # Check status code
                if response.status != 200:
                    error_text = await response.text()
                    raise OllamaError(
                        f"HTTP {response.status}: {error_text}",
                        OllamaError.CONNECTION_ERROR
                    )

                # Parse response
                response_data = await response.json()
                return response_data

        except aiohttp.ClientError as e:
            logger.error(f"Connection error: {e}")
            raise OllamaError(f"Connection error: {e}", OllamaError.CONNECTION_ERROR)
        except asyncio.TimeoutError as e:
            logger.error(f"Request timeout: {e}")
            raise OllamaError(f"Request timeout: {e}", OllamaError.TIMEOUT_ERROR)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise OllamaError(f"Invalid JSON response: {e}", OllamaError.INVALID_RESPONSE)
        except Exception as e:
            logger.error(f"Error sending request: {e}")
            raise OllamaError(f"Error sending request: {e}", OllamaError.CONNECTION_ERROR) 