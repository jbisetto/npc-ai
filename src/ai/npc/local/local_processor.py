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
from src.ai.npc.core.conversation_manager import ConversationManager
from src.ai.npc.core.prompt_manager import PromptManager
from src.ai.npc.core.processor_framework import Processor
from src.ai.npc.core.vector.knowledge_store import KnowledgeStore

logger = logging.getLogger(__name__)


class LocalProcessor(Processor):
    """
    Processes requests using a local Ollama instance.
    """
    
    def __init__(
        self,
        ollama_client: OllamaClient,
        conversation_manager: Optional[ConversationManager] = None,
        knowledge_store: Optional[KnowledgeStore] = None
    ):
        """
        Initialize the local processor.
        
        Args:
            ollama_client: Client for interacting with Ollama
            conversation_manager: Optional manager for conversation history
            knowledge_store: Optional knowledge store instance to pass to base class
        """
        # Initialize base class
        super().__init__(knowledge_store=knowledge_store)
        
        self.ollama_client = ollama_client
        self.conversation_manager = conversation_manager
        self.response_parser = ResponseParser()
        self.prompt_manager = PromptManager()
        
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
            if conversation_id and self.conversation_manager:
                history = await self.conversation_manager.get_player_history(request.game_context.player_id)

            # Get relevant knowledge from the knowledge store
            knowledge_context = await self.knowledge_store.contextual_search(request)

            # Create prompt with knowledge context
            prompt = self.prompt_manager.create_prompt(
                request,
                history=history,
                knowledge_context=knowledge_context
            )

            # Set request_id on the client for prompt capture
            self.ollama_client.request_id = request.request_id

            # Generate response
            response_text = await self.ollama_client.generate(prompt)

            # Clear request_id after generation
            self.ollama_client.request_id = None

            # Parse response
            result = self.response_parser.parse_response(response_text, request)

            # Update conversation history if needed
            if conversation_id and self.conversation_manager:
                await self.conversation_manager.add_to_history(
                    conversation_id=conversation_id,
                    user_query=request.player_input,
                    response=result['response_text'],
                    npc_id=request.game_context.npc_id,
                    player_id=request.game_context.player_id
                )

            return result

        except OllamaError as e:
            self.logger.error(f"Error from Ollama: {e}", exc_info=True)
            return self._generate_fallback_response(request, e)
        except Exception as e:
            self.logger.error(f"Error processing request: {e}", exc_info=True)
            return self._generate_fallback_response(request, e)

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