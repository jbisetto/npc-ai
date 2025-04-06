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

from src.ai.npc.core.models import (
    ClassifiedRequest,
    CompanionRequest,
    ProcessingTier
)
from src.ai.npc.core.processor_framework import Processor
from src.ai.npc.hosted.bedrock_client import BedrockClient, BedrockError
from src.ai.npc.hosted.usage_tracker import UsageTracker, default_tracker
from src.ai.npc.core.context_manager import ContextManager, default_context_manager
from src.ai.npc.core.conversation_manager import ConversationManager, ConversationState
from src.ai.npc.core.prompt_manager import PromptManager
from src.ai.npc.hosted.conversation_manager import ConversationManager
from src.ai.npc.utils.monitoring import ProcessorMonitor
from src.ai.npc.config import get_config, CLOUD_API_CONFIG


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
        player_history_manager=None
    ):
        """
        Initialize the hosted processor.
        
        Args:
            usage_tracker: The usage tracker for monitoring API usage
            context_manager: Context manager for tracking conversation context
            player_history_manager: Player history manager for tracking player interactions
        """
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.client = self._create_bedrock_client(usage_tracker)
        self.conversation_manager = ConversationManager()
        self.prompt_manager = PromptManager(tier_specific_config={"model_type": "bedrock"})
        self.context_manager = context_manager or default_context_manager
        self.monitor = ProcessorMonitor()
        self.player_history_manager = player_history_manager
        
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
        
        return BedrockClient(
            usage_tracker=usage_tracker or default_tracker,
            model_id=bedrock_config.get('model_id'),
            max_tokens=bedrock_config.get('max_tokens'),
            temperature=bedrock_config.get('temperature'),
            top_p=bedrock_config.get('top_p'),
            top_k=bedrock_config.get('top_k'),
            stop_sequences=bedrock_config.get('stop_sequences', [])
        )
    
    async def process(self, request: ClassifiedRequest) -> Dict[str, Any]:
        """
        Process a classified request and generate a response using Amazon Bedrock.
        
        Args:
            request: A classified request
            
        Returns:
            A dictionary containing the response text and processing tier
        """
        start_time = time.time()
        
        try:
            # Create a companion request for the client
            companion_request = CompanionRequest(
                request_id=request.request_id,
                player_input=request.player_input,
                request_type=request.request_type,
                timestamp=request.timestamp,
                game_context=request.game_context,
                additional_params=request.additional_params
            )
            
            # Create a base prompt for the request
            base_prompt = self.prompt_manager.create_prompt(
                request
            )
            
            # Initialize conversation_history as an empty list
            conversation_history = []
            
            # Get conversation history if a conversation ID is provided
            conversation_id = request.additional_params.get("conversation_id")
            player_id = request.additional_params.get("player_id")
            
            # Use player history if available
            player_history = []
            if player_id and self.player_history_manager:
                player_history = self.player_history_manager.get_player_history(player_id)
                self.logger.debug(f"Retrieved player history for {player_id}, found {len(player_history)} entries")
                
                # If we have player history, convert it to conversation history format
                if player_history and not conversation_history:
                    for entry in player_history:
                        if 'user_query' in entry and 'assistant_response' in entry:
                            conversation_history.append({
                                "role": "user",
                                "content": entry['user_query']
                            })
                            conversation_history.append({
                                "role": "assistant",
                                "content": entry['assistant_response']
                            })
            
            # If we have a conversation ID but no conversation history yet, check the context manager
            if conversation_id and not conversation_history:
                try:
                    # Try to use get_or_create_context if available
                    context = self.context_manager.get_or_create_context(conversation_id)
                except AttributeError:
                    # Fallback to get_context if get_or_create_context is not available
                    context = self.context_manager.get_context(conversation_id)
                
                if context:
                    # Create conversation history from the context
                    if isinstance(context, dict) and "entries" in context:
                        conversation_history = context["entries"]
            
            # For testing, we'll just use a simple state and the base prompt
            state = ConversationState.NEW_TOPIC
            
            # Use contextual prompt with conversation history if available
            if conversation_history:
                self.logger.debug(f"Using contextual prompt with {len(conversation_history)} history entries")
                prompt = self.prompt_manager.create_contextual_prompt(request, conversation_history)
            else:
                # If no conversation history, use the base prompt
                prompt = base_prompt
            
            # Generate a response using the Bedrock client
            try:
                # Get configuration from companion.yaml for model parameters
                hosted_config = get_config('hosted', {})
                bedrock_config = hosted_config.get('bedrock', {})
                
                # Check if the generate method is a coroutine or not
                if asyncio.iscoroutinefunction(self.client.generate):
                    response = await self.client.generate(
                        request=companion_request,
                        model_id=bedrock_config.get("model_id"),
                        temperature=bedrock_config.get("temperature"),
                        max_tokens=bedrock_config.get("max_tokens"),
                        prompt=prompt
                    )
                else:
                    # For mocked clients that don't implement async
                    response = self.client.generate(
                        request=companion_request,
                        model_id=bedrock_config.get("model_id"),
                        temperature=bedrock_config.get("temperature"),
                        max_tokens=bedrock_config.get("max_tokens"),
                        prompt=prompt
                    )
                
                # Update conversation history if a conversation ID is provided
                if conversation_id:
                    # Check if update_context is a coroutine function
                    if asyncio.iscoroutinefunction(self.context_manager.update_context):
                        await self.context_manager.update_context(
                            conversation_id, 
                            request, 
                            response
                        )
                    else:
                        # Use the sync method
                        self.context_manager.update_context(
                            conversation_id, 
                            request, 
                            response
                        )
                
                # Parse the response
                parsed_response = self._parse_response(response)
                
                # Update player history if we have player_id and player_history_manager
                if player_id and self.player_history_manager:
                    self.player_history_manager.add_interaction(
                        player_id=player_id,
                        user_query=request.player_input,
                        assistant_response=parsed_response,
                        session_id=request.additional_params.get("session_id"),
                        metadata={
                            "processing_tier": ProcessingTier.TIER_3.value
                        }
                    )
                
                return {
                    'response_text': parsed_response,
                    'processing_tier': request.processing_tier
                }
            except Exception as e:
                self.logger.error(f"Error generating response: {str(e)}")
                return self._generate_fallback_response(request, e)
                
        except Exception as e:
            self.logger.error(f"Unexpected error in HostedProcessor: {str(e)}")
            return {
                'response_text': f"I'm sorry, I'm having trouble processing your request. Error: {str(e)}",
                'processing_tier': request.processing_tier
            }
        finally:
            elapsed_time = time.time() - start_time
            self.logger.info(f"Processed request {request.request_id} in {elapsed_time:.2f}s")
    
    def _parse_response(self, response: str) -> str:
        """
        Parse and clean the response from the Bedrock API.
        
        Args:
            response: The raw response from the API
            
        Returns:
            A cleaned response string
        """
        # Remove any system-like prefixes that might be in the response
        cleaned_response = response.strip()
        
        # Remove any <assistant> tags that might be in the response
        cleaned_response = cleaned_response.replace("<assistant>", "").replace("</assistant>", "")
        
        # Remove any leading/trailing whitespace
        cleaned_response = cleaned_response.strip()
        
        return cleaned_response
    
    def _generate_fallback_response(self, request: ClassifiedRequest, error: Any) -> Dict[str, Any]:
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
                'response_text': "I'm sorry, but I've reached my limit for complex questions right now. Could you ask something simpler, or try again later?",
                'processing_tier': request.processing_tier
            }
        
        # For other errors, provide a generic message
        self.logger.info(f"Hosted fallback for request {request.request_id} due to error: {str(error)}")
        return {
            'response_text': "I'm sorry, I'm having trouble understanding that right now. Could you rephrase your question or ask something else?",
            'processing_tier': request.processing_tier
        } 