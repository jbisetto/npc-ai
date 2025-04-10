"""
Local Processor

This module implements the local processor using Ollama.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List

from src.ai.npc.core.models import (
    NPCRequest,
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
from src.ai.npc.core.profile.profile_loader import ProfileLoader

logger = logging.getLogger(__name__)


class LocalProcessor(Processor):
    """
    Processes requests using a local Ollama instance.
    """
    
    def __init__(
        self,
        ollama_client: OllamaClient,
        conversation_manager: Optional[ConversationManager] = None,
        knowledge_store: Optional[KnowledgeStore] = None,
        profiles_dir: str = "src/data/profiles"
    ):
        """
        Initialize the local processor.
        
        Args:
            ollama_client: Client for interacting with Ollama
            conversation_manager: Optional manager for conversation history
            knowledge_store: Optional knowledge store instance to pass to base class
            profiles_dir: Directory containing NPC profile definitions
        """
        # Initialize base class
        super().__init__(knowledge_store=knowledge_store)
        
        self.ollama_client = ollama_client
        self.conversation_manager = conversation_manager
        self.response_parser = ResponseParser()
        self.prompt_manager = PromptManager()
        self.profile_registry = ProfileLoader(profiles_directory=profiles_dir)
        
        # Initialize adapters
        self.history_adapter = DefaultConversationHistoryAdapter()
        self.knowledge_adapter = DefaultKnowledgeContextAdapter()
        
    async def process(self, request: NPCRequest) -> Dict[str, Any]:
        """
        Process a request using the local model.
        
        Args:
            request: The request to process
            
        Returns:
            Dict containing response text and metadata
        """
        self.logger.info(f"Processing request {request.request_id} with player input: '{request.player_input}'")
        try:
            # Get conversation history if available
            history = []
            conversation_id = request.additional_params.get('conversation_id')
            self.logger.debug(f"Conversation ID from request: {conversation_id}")
            
            if conversation_id and self.conversation_manager:
                # Get history in standardized format
                try:
                    player_id = request.game_context.player_id
                    self.logger.debug(f"Retrieving conversation history for player_id: {player_id}")
                    history = await self.conversation_manager.get_player_history(
                        player_id,
                        standardized_format=True,
                        npc_id=request.game_context.npc_id
                    )
                    self.logger.debug(f"Retrieved {len(history)} conversation history entries")
                except Exception as e:
                    self.logger.error(f"Error retrieving conversation history: {e}", exc_info=True)
                    history = []
            else:
                self.logger.debug(f"No conversation history retrieved. conversation_id: {conversation_id}")

            # Get NPC profile if NPC ID is available
            profile = None
            if hasattr(request.game_context, 'npc_id') and request.game_context.npc_id:
                npc_id = request.game_context.npc_id
                self.logger.debug(f"Loading profile for NPC ID: {npc_id}")
                try:
                    # Convert enum to string value if it's an enum
                    if hasattr(npc_id, 'value'):
                        npc_id = npc_id.value
                        
                    profile = self.profile_registry.get_profile(npc_id, as_object=True)
                    if profile:
                        self.logger.debug(f"Loaded profile for {profile.name}, role: {profile.role}")
                    else:
                        self.logger.warning(f"No profile found for NPC ID: {npc_id}")
                except Exception as e:
                    self.logger.error(f"Error loading NPC profile: {e}", exc_info=True)

            # Get relevant knowledge from the knowledge store in standardized format
            try:
                self.logger.debug(f"Retrieving knowledge context for: '{request.player_input}'")
                try:
                    # Handle the count method which could be async or not
                    if hasattr(self.knowledge_store.collection.count, '__await__'):
                        doc_count = await self.knowledge_store.collection.count()
                    else:
                        doc_count = self.knowledge_store.collection.count()
                    self.logger.debug(f"Knowledge store collection has {doc_count} documents")
                except Exception as e:
                    self.logger.debug(f"Could not get document count: {str(e)}")
                
                knowledge_context = await self.knowledge_store.contextual_search(
                    request,
                    standardized_format=True
                )
                self.logger.debug(f"Retrieved {len(knowledge_context)} knowledge context items")
                
                # Log the retrieved knowledge items
                if knowledge_context:
                    for i, item in enumerate(knowledge_context):
                        if hasattr(item, 'text') and hasattr(item, 'metadata'):
                            self.logger.debug(f"Knowledge item {i+1}: {item.text[:100]}... (relevance: {item.metadata.get('relevance_score', 'N/A')})")
                        else:
                            self.logger.debug(f"Knowledge item {i+1}: {str(item)[:100]}...")
                else:
                    self.logger.debug("No knowledge items found")
            except Exception as e:
                self.logger.error(f"Error retrieving knowledge context: {str(e)}", exc_info=True)
                knowledge_context = []

            # Create prompt with standardized knowledge context, history, and profile
            self.logger.debug(f"Creating prompt with {len(history)} history entries and {len(knowledge_context)} knowledge items")
            prompt = self.prompt_manager.create_prompt(
                request,
                history=history,
                profile=profile,
                knowledge_context=knowledge_context
            )
            self.logger.debug(f"Created prompt with {self.prompt_manager.estimate_tokens(prompt)} tokens")

            # Set request_id on the client for prompt capture
            self.ollama_client.request_id = request.request_id

            # Generate response
            self.logger.debug(f"Sending prompt to Ollama with {len(prompt)} characters")
            try:
                response_text = await self.ollama_client.generate(prompt)
                self.logger.debug(f"Received response from Ollama with {len(response_text)} characters")
            except Exception as e:
                self.logger.error(f"Error generating response: {e}", exc_info=True)
                raise

            # Clear request_id after generation
            self.ollama_client.request_id = None

            # Parse response
            result = self.response_parser.parse_response(response_text, request)

            # Update conversation history if needed
            if conversation_id and self.conversation_manager:
                try:
                    self.logger.debug(f"Adding interaction to conversation history: {conversation_id}")
                    self.logger.debug(f"Player ID: {request.game_context.player_id}, NPC ID: {request.game_context.npc_id}")
                    await self.conversation_manager.add_to_history(
                        conversation_id=conversation_id,
                        user_query=request.player_input,
                        response=result['response_text'],
                        npc_id=request.game_context.npc_id,
                        player_id=request.game_context.player_id
                    )
                    self.logger.debug("Successfully added interaction to conversation history")
                except Exception as e:
                    self.logger.error(f"Error updating conversation history: {e}", exc_info=True)

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

    def _generate_fallback_response(self, request: NPCRequest, error: Exception) -> Dict[str, Any]:
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

    async def close(self):
        """
        Close the processor and release any resources.
        
        This method should be called when the processor is no longer needed
        to ensure proper cleanup of resources.
        """
        logger.info("Closing local processor and releasing resources")
        
        # Close the Ollama client if it exists and has a close method
        if hasattr(self, 'ollama_client') and self.ollama_client is not None:
            try:
                await self.ollama_client.close()
                logger.debug("Successfully closed Ollama client")
            except Exception as e:
                logger.error(f"Error closing Ollama client: {e}", exc_info=True)
        
        # Close the knowledge store if it exists and has a close method
        if hasattr(self, 'knowledge_store') and self.knowledge_store is not None:
            try:
                if hasattr(self.knowledge_store, 'clear'):
                    await self.knowledge_store.clear()
                    logger.debug("Successfully cleared knowledge store")
                
                # If there's a more specific close method, call that too
                if hasattr(self.knowledge_store, 'close'):
                    await self.knowledge_store.close()
                    logger.debug("Successfully closed knowledge store")
            except Exception as e:
                logger.error(f"Error closing knowledge store: {e}", exc_info=True) 