"""
Local Processor

This module implements the local processor using Ollama.
"""

import logging
import asyncio
from typing import Dict, Any, Optional

from src.ai.npc.core.models import (
    ClassifiedRequest,
    ProcessingTier
)
from src.ai.npc.core.response_parser import ResponseParser
from src.ai.npc.local.ollama_client import OllamaClient, OllamaError
from src.ai.npc.core.player_history_manager import PlayerHistoryManager
from src.ai.npc.core.prompt_manager import create_prompt

logger = logging.getLogger(__name__)


class LocalProcessor:
    """
    Processes requests using a local Ollama instance.
    """
    
    def __init__(
        self,
        ollama_client: OllamaClient,
        player_history_manager: Optional[PlayerHistoryManager] = None
    ):
        """
        Initialize the local processor.
        
        Args:
            ollama_client: Client for interacting with Ollama
            player_history_manager: Optional manager for conversation history
        """
        self.ollama_client = ollama_client
        self.player_history_manager = player_history_manager
        self.response_parser = ResponseParser()
        self.logger = logging.getLogger(__name__)
        
    async def process(self, request: ClassifiedRequest) -> Dict[str, Any]:
        """
        Process a request using the local model.
        
        Args:
            request: The request to process
            
        Returns:
            Dict containing response text and metadata
        """
        try:
            # Get conversation history if available
            history = []
            conversation_id = request.additional_params.get('conversation_id')
            if conversation_id and self.player_history_manager:
                history = await self.player_history_manager.get_history(conversation_id)

            # Create prompt
            prompt = create_prompt(request, history)

            # Generate response
            response_text = await self._generate_with_retries(prompt)

            # Parse response
            result = self.response_parser.parse_response(response_text, request)

            # Update conversation history if needed
            if conversation_id and self.player_history_manager:
                await self.player_history_manager.add_to_history(
                    conversation_id,
                    request.player_input,
                    result['response_text']
                )

            return result

        except Exception as e:
            self.logger.error(f"Error processing request: {e}", exc_info=True)
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
                self.logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                await asyncio.sleep(delay)

    def _generate_fallback_response(self, request: ClassifiedRequest, error: Exception) -> Dict[str, Any]:
        """
        Generate a fallback response when processing fails.

        Args:
            request: The original request.
            error: The error that occurred.

        Returns:
            A dictionary containing the fallback response and metadata.
        """
        return {
            'response_text': (
                "I apologize, but I'm having trouble processing your request right now. "
                "Could you try rephrasing your question or asking something else?"
            ),
            'processing_tier': ProcessingTier.LOCAL,
            'is_fallback': True
        } 