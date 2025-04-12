"""
Hosted Processor

This processor handles requests by generating responses with a
powerful cloud-based language model. It is the most flexible but also
the most expensive processor in the processing framework.
"""

import logging
import asyncio
import time
from typing import Dict, Any, Optional, List
from unittest.mock import patch
import os

from src.ai.npc.core.models import (
    ClassifiedRequest,
    CompanionRequest,
    ProcessingTier
)
from src.ai.npc.core.processor_framework import Processor
from src.ai.npc.hosted.bedrock_client import BedrockClient, BedrockError
from src.ai.npc.hosted.usage_tracker import UsageTracker, default_tracker
from src.ai.npc.core.context_manager import ContextManager, default_context_manager
from src.ai.npc.core.prompt_manager import PromptManager
from src.ai.npc.utils.monitoring import ProcessorMonitor
from src.ai.npc.config import get_config, CLOUD_API_CONFIG
from src.ai.npc.core.response_parser import ResponseParser
from src.ai.npc.core.conversation_manager import ConversationManager
from src.ai.npc.core.vector.knowledge_store import KnowledgeStore
from src.ai.npc.core.history_adapter import DefaultConversationHistoryAdapter
from src.ai.npc.core.knowledge_adapter import DefaultKnowledgeContextAdapter
from src.ai.npc.core.profile.profile_loader import ProfileLoader
from src.ai.npc.core.models import NPCRequest

logger = logging.getLogger(__name__)


class HostedProcessor(Processor):
    """
    Hosted processor that uses Amazon Bedrock for generating responses.
    
    This processor handles complex requests by generating responses with a
    powerful cloud-based language model. It is the most flexible but also
    the most expensive processor in the processing framework.
    """
    
    def __init__(
        self,
        usage_tracker: Optional[UsageTracker] = None,
        context_manager: Optional[ContextManager] = None,
        conversation_manager: Optional[ConversationManager] = None,
        knowledge_store: Optional[KnowledgeStore] = None
    ):
        """
        Initialize the hosted processor.
        
        Args:
            usage_tracker: The usage tracker for monitoring API usage
            context_manager: Context manager for tracking conversation context
            conversation_manager: Conversation manager for tracking interactions
            knowledge_store: Optional knowledge store instance to pass to base class
        """
        # Initialize base class
        super().__init__(knowledge_store=knowledge_store)
        
        # Initialize components
        self.client = self._create_bedrock_client(usage_tracker)
        self.prompt_manager = PromptManager(tier_specific_config={"model_type": "bedrock"})
        self.context_manager = context_manager or default_context_manager
        self.monitor = ProcessorMonitor()
        self.conversation_manager = conversation_manager
        self.response_parser = ResponseParser()
        
        # Initialize adapters
        self.history_adapter = DefaultConversationHistoryAdapter()
        self.knowledge_adapter = DefaultKnowledgeContextAdapter()
        
        # Initialize profile registry with absolute path
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
        profiles_dir = os.path.join(base_dir, "src/data/profiles")
        self.logger.info(f"[PROFILE DEBUG] Current working directory: {os.getcwd()}")
        self.logger.info(f"[PROFILE DEBUG] Base directory: {base_dir}")
        self.logger.info(f"[PROFILE DEBUG] Absolute profiles directory: {profiles_dir}")
        self.logger.info(f"[PROFILE DEBUG] Directory exists: {os.path.exists(profiles_dir)}")
        if os.path.exists(profiles_dir):
            self.logger.info(f"[PROFILE DEBUG] Files in directory: {os.listdir(profiles_dir)}")
        self.profile_registry = ProfileLoader(profiles_directory=profiles_dir)
        self.logger.info(f"[PROFILE DEBUG] ProfileLoader created, profiles loaded: {len(self.profile_registry.profiles)}")
        
        # Initialize storage
        self.conversation_histories = {}
        
        self.logger.info("Initialized HostedProcessor with Bedrock client")
    
    def _create_bedrock_client(self, usage_tracker: Optional[UsageTracker] = None) -> BedrockClient:
        """
        Create and configure the Bedrock client.
        
        Args:
            usage_tracker: Optional usage tracker for monitoring API usage
            
        Returns:
            A configured Bedrock client
        """
        hosted_config = get_config('hosted', {})
        bedrock_config = hosted_config.get('bedrock', {})
        
        # Log the configuration for debugging
        self.logger.info(f"Creating Bedrock client with config: {bedrock_config}")
        
        return BedrockClient(
            usage_tracker=usage_tracker or default_tracker,
            model_id=bedrock_config.get('model_id'),
            max_tokens=bedrock_config.get('max_tokens'),
            temperature=bedrock_config.get('temperature'),
            top_p=bedrock_config.get('top_p'),
            top_k=bedrock_config.get('top_k'),
            stop_sequences=bedrock_config.get('stop_sequences', [])
        )
    
    async def process(self, request: NPCRequest) -> Dict[str, Any]:
        """
        Process a request and generate a response using Amazon Bedrock.
        
        Args:
            request: A request to the NPC AI system
            
        Returns:
            A dictionary containing the response text and processing tier
        """
        start_time = time.time()
        
        try:
            # Get conversation history if available
            history = []
            conversation_id = request.additional_params.get('conversation_id')
            if conversation_id and self.conversation_manager:
                # Get history in standardized format
                history = await self.conversation_manager.get_player_history(
                    request.game_context.player_id,
                    standardized_format=True,
                    npc_id=request.game_context.npc_id
                )
                self.logger.debug(f"Retrieved {len(history)} conversation history entries")
            else:
                self.logger.debug(f"No conversation history retrieved. conversation_id: {conversation_id}")

            # Load profile if NPC ID is available
            profile = None
            if hasattr(request.game_context, 'npc_id') and request.game_context.npc_id:
                npc_id = request.game_context.npc_id
                self.logger.info(f"[PROFILE DEBUG] Loading profile for NPC ID: {npc_id}")
                
                try:
                    # Convert enum to string value if it's an enum
                    if hasattr(npc_id, 'value'):
                        npc_id = npc_id.value
                        self.logger.info(f"[PROFILE DEBUG] Converted enum value from {npc_id} to {npc_id}")
                    
                    # Get profile by ID - same as local_processor
                    profile = self.profile_registry.get_profile(npc_id, as_object=True)
                    if profile:
                        self.logger.info(f"[PROFILE DEBUG] Successfully loaded profile for {profile.name}, role: {profile.role}")
                    else:
                        self.logger.warning(f"[PROFILE DEBUG] No profile found for NPC ID: {npc_id}")
                except Exception as e:
                    self.logger.error(f"[PROFILE DEBUG] Error loading NPC profile: {e}", exc_info=True)

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
            self.logger.info(f"[PROFILE DEBUG] Using profile in prompt generation: {profile.name if profile else 'None'}")
            
            prompt = self.prompt_manager.create_prompt(
                request,
                history=history,
                profile=profile,
                knowledge_context=knowledge_context
            )
            self.logger.debug(f"Created prompt with {self.prompt_manager.estimate_tokens(prompt)} tokens")

            # Log the prompt for debugging
            self.logger.debug(f"Generated prompt for request {request.request_id}:\n{prompt}")

            # Generate response
            self.logger.info(f"Calling Bedrock API for request {request.request_id}")
            try:
                response_text = await self.client.generate(prompt)
                self.logger.info(f"Bedrock API response received: {response_text[:100]}...")
                
                # Check if we got the placeholder response
                if response_text.startswith("Response to:") or response_text.startswith("Error generating response:"):
                    self.logger.error(f"Bedrock API returned an error or placeholder: {response_text}")
                    return self._generate_fallback_response(
                        request, 
                        Exception(f"Bedrock API error: {response_text}")
                    )
            except Exception as api_error:
                self.logger.error(f"Error calling Bedrock API: {api_error}", exc_info=True)
                return self._generate_fallback_response(request, api_error)

            # Parse response
            result = self.response_parser.parse_response(response_text, request)
            
            # Add diagnostic information
            result['debug_info'] = result.get('debug_info', {})
            result['debug_info']['prompt'] = prompt
            result['debug_info']['knowledge_count'] = len(knowledge_context)
            result['debug_info']['history_count'] = len(history)
            result['debug_info']['prompt_tokens'] = self.prompt_manager.estimate_tokens(prompt)
            
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

            # Update conversation history if needed
            if conversation_id and self.conversation_manager:
                # Convert npc_id to string if it's an enum
                npc_id = request.game_context.npc_id
                if hasattr(npc_id, 'value'):
                    npc_id = npc_id.value
                    
                await self.conversation_manager.add_to_history(
                    conversation_id=conversation_id,
                    user_query=request.player_input,
                    response=result['response_text'],
                    npc_id=npc_id,
                    player_id=request.game_context.player_id
                )

            return result

        except Exception as e:
            self.logger.error(f"Error processing request: {e}", exc_info=True)
            return self._generate_fallback_response(request, e)
            
        finally:
            elapsed_time = time.time() - start_time
            self.logger.info(f"Processed request {request.request_id} in {elapsed_time:.2f}s")
    
    def _generate_fallback_response(self, request: NPCRequest, error: Any) -> Dict[str, Any]:
        """
        Generate a fallback response when an error occurs.
        
        Args:
            request: The request that failed
            error: The error that occurred
            
        Returns:
            A dictionary containing the fallback response and processing tier
        """
        self.logger.debug(f"Generating fallback response for request {request.request_id}")
        
        # For quota errors, provide a specific message
        if isinstance(error, BedrockError) and error.error_type == BedrockError.QUOTA_ERROR:
            self.logger.info(f"Hosted quota exceeded for request {request.request_id}. Returning quota error message.")
            return {
                'response_text': (
                    "I'm sorry, but I've reached my limit for complex questions right now. "
                    "Could you ask something simpler, or try again later?"
                ),
                'processing_tier': request.processing_tier,
                'is_fallback': True,
                'debug_info': {
                    'error_type': 'QuotaExceeded',
                    'error': str(error)
                }
            }
        
        # For other errors, provide a generic message
        self.logger.info(f"Hosted fallback for request {request.request_id} due to error: {str(error)}")
        return {
            'response_text': (
                "I'm sorry, I'm having trouble understanding that right now. "
                "Could you rephrase your question or ask something else?"
            ),
            'processing_tier': request.processing_tier,
            'is_fallback': True,
            'debug_info': {
                'error_type': type(error).__name__,
                'error': str(error)
            }
        } 