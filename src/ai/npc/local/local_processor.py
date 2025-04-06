"""
Local processor module.

This module contains the LocalProcessor class, which handles processing requests
using local language models via the Ollama client.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from src.ai.npc.core.models import (
    ClassifiedRequest,
    ProcessingTier
)
from src.ai.npc.core.context_manager import ContextManager
from src.ai.npc.core.player_history_manager import PlayerHistoryManager
from src.ai.npc.local.ollama_client import OllamaClient, OllamaError
from src.ai.npc.local.prompt_engineering import create_prompt
from src.ai.npc.local.response_parser import ResponseParser
from src.ai.npc.config import get_config

logger = logging.getLogger(__name__)

class LocalProcessor:
    """
    Processor that uses local language models via Ollama.
    
    This processor handles requests that can be processed locally using
    the Ollama client to interact with local language models.
    """

    def __init__(self, context_manager: Optional[ContextManager] = None):
        """Initialize the processor."""
        # Get configuration
        config = get_config('local', {})
        self.enabled = config.get('enabled', True)
        
        # Initialize components
        self.ollama_client = OllamaClient(
            base_url=config.get('base_url', 'http://localhost:11434'),
            default_model=config.get('default_model', 'deepseek-r1:latest'),
            cache_enabled=config.get('cache_enabled', True),
            cache_dir=config.get('cache_dir', '/tmp/cache'),
            cache_ttl=config.get('cache_ttl', 86400),
            max_cache_entries=config.get('max_cache_entries', 1000),
            max_cache_size_mb=config.get('max_cache_size_mb', 100)
        )
        self.response_parser = ResponseParser()
        self.context_manager = context_manager or ContextManager()
        self.player_history_manager = PlayerHistoryManager()

    async def process(self, request: ClassifiedRequest) -> Dict[str, Any]:
        """
        Process a request using local language models.

        Args:
            request: The classified request to process.

        Returns:
            A dictionary containing the response text and processing tier.
        """
        if not self.enabled:
            return {
                'response_text': "I apologize, but local processing is currently disabled.",
                'processing_tier': ProcessingTier.LOCAL
            }

        try:
            # Get conversation history if available
            conversation_id = request.additional_params.get('conversation_id')
            if conversation_id:
                history = await self.player_history_manager.get_history(conversation_id)
            else:
                history = []

            # Create prompt
            prompt = create_prompt(request, history)

            # Generate response
            response_text = await self._generate_with_retries(prompt)

            # Parse response
            parsed_response = self.response_parser.parse_response(response_text)

            # Update conversation history if needed
            if conversation_id:
                await self.player_history_manager.add_to_history(
                    conversation_id,
                    request.player_input,
                    parsed_response
                )

            return {
                'response_text': parsed_response,
                'processing_tier': ProcessingTier.LOCAL
            }

        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            return self._generate_fallback_response(request, e)

    async def _generate_with_retries(self, prompt: str) -> str:
        """
        Generate a response with retries on failure.

        Args:
            prompt: The prompt to send to the model.

        Returns:
            The generated response text.

        Raises:
            OllamaError: If all retries fail.
        """
        max_retries = 3
        base_delay = 1.0
        max_delay = 5.0
        backoff_factor = 2.0

        for attempt in range(max_retries):
            try:
                return await self.ollama_client.generate(prompt)
            except OllamaError as e:
                if attempt == max_retries - 1:
                    raise
                delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                await asyncio.sleep(delay)

    def _generate_fallback_response(self, request: ClassifiedRequest, error: Exception) -> Dict[str, Any]:
        """
        Generate a fallback response when processing fails.

        Args:
            request: The original request.
            error: The error that occurred.

        Returns:
            A dictionary containing the fallback response text and processing tier.
        """
        fallback_text = (
            "I apologize, but I'm having trouble processing your request right now. "
            "Could you try rephrasing your question or asking something else?"
        )
        return {
            'response_text': fallback_text,
            'processing_tier': ProcessingTier.LOCAL
        } 