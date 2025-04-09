"""
Local Processor

This module implements the local processor using Ollama.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List

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
from src.ai.npc.core.history_adapter import DefaultConversationHistoryAdapter
from src.ai.npc.core.knowledge_adapter import DefaultKnowledgeContextAdapter

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
        
        # Initialize adapters
        self.history_adapter = DefaultConversationHistoryAdapter()
        self.knowledge_adapter = DefaultKnowledgeContextAdapter()
        
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
                # Get history in standardized format
                history = await self.conversation_manager.get_player_history(
                    request.game_context.player_id,
                    standardized_format=True
                )
                self.logger.debug(f"Retrieved {len(history)} conversation history entries")
            else:
                self.logger.debug(f"No conversation history retrieved. conversation_id: {conversation_id}")

            # Get relevant knowledge from the knowledge store in standardized format
            try:
                self.logger.debug(f"Retrieving knowledge context for: '{request.player_input}'")
                knowledge_context = await self.knowledge_store.contextual_search(
                    request,
                    standardized_format=True
                )
                self.logger.debug(f"Retrieved {len(knowledge_context)} knowledge context items")
                
                # Log the retrieved knowledge items
                if knowledge_context:
                    for i, item in enumerate(knowledge_context):
                        if hasattr(item, 'text') and hasattr(item, 'metadata'):
                            self.logger.debug(f"Knowledge item {i+1}: {item.text[:100]}... (score: {item.metadata.get('score', 'N/A')})")
                        else:
                            self.logger.debug(f"Knowledge item {i+1}: {str(item)[:100]}...")
                else:
                    self.logger.debug("No knowledge items found")
            except Exception as e:
                self.logger.error(f"Error retrieving knowledge context: {str(e)}")
                knowledge_context = []

            # Create prompt with standardized knowledge context and history
            self.logger.debug(f"Creating prompt with {len(history)} history entries and {len(knowledge_context)} knowledge items")
            prompt = self.prompt_manager.create_prompt(
                request,
                history=history,
                knowledge_context=knowledge_context
            )
            self.logger.debug(f"Created prompt with {self.prompt_manager.estimate_tokens(prompt)} tokens")

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

            # Add diagnostic information
            if not result.get('debug_info'):
                result['debug_info'] = {}
            
            result['debug_info']['knowledge_count'] = len(knowledge_context)
            result['debug_info']['history_count'] = len(history)
            result['debug_info']['prompt_tokens'] = self.prompt_manager.estimate_tokens(prompt)
            result['debug_info']['prompt'] = prompt
            
            # Add knowledge items to debug info (simplified version)
            knowledge_items = []
            for item in knowledge_context:
                if hasattr(item, 'text') and hasattr(item, 'metadata'):
                    knowledge_items.append({
                        'text': item.text,
                        'source': item.metadata.get('source', 'unknown'),
                        'score': item.metadata.get('score', 0)
                    })
            result['debug_info']['knowledge_items'] = knowledge_items

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
            'is_fallback': True,
            'debug_info': {
                'error': str(error),
                'error_type': type(error).__name__
            }
        } 