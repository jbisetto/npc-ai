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
from src.ai.npc.core.prompt_manager import PromptManager
from src.ai.npc.utils.monitoring import ProcessorMonitor
from src.ai.npc.config import get_config, CLOUD_API_CONFIG
from src.ai.npc.core.response_parser import ResponseParser
from src.ai.npc.core.conversation_manager import ConversationManager


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
        conversation_manager: Optional[ConversationManager] = None
    ):
        """
        Initialize the hosted processor.
        
        Args:
            usage_tracker: The usage tracker for monitoring API usage
            context_manager: Context manager for tracking conversation context
            conversation_manager: Conversation manager for tracking interactions
        """
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.client = self._create_bedrock_client(usage_tracker)
        self.prompt_manager = PromptManager(tier_specific_config={"model_type": "bedrock"})
        self.context_manager = context_manager or default_context_manager
        self.monitor = ProcessorMonitor()
        self.conversation_manager = conversation_manager
        self.response_parser = ResponseParser()
        
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
            # Get conversation history if available
            history = []
            conversation_id = request.additional_params.get('conversation_id')
            if conversation_id and self.conversation_manager:
                history = await self.conversation_manager.get_player_history(request.game_context.player_id)

            # Create prompt
            prompt = self.prompt_manager.create_prompt(request, history)

            # Generate response
            response_text = await self.client.generate(prompt)

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

        except Exception as e:
            self.logger.error(f"Error processing request: {e}", exc_info=True)
            return self._generate_fallback_response(request, e)
            
        finally:
            elapsed_time = time.time() - start_time
            self.logger.info(f"Processed request {request.request_id} in {elapsed_time:.2f}s")
    
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
                'response_text': (
                    "I'm sorry, but I've reached my limit for complex questions right now. "
                    "Could you ask something simpler, or try again later?"
                ),
                'processing_tier': request.processing_tier,
                'is_fallback': True
            }
        
        # For other errors, provide a generic message
        self.logger.info(f"Hosted fallback for request {request.request_id} due to error: {str(error)}")
        return {
            'response_text': (
                "I'm sorry, I'm having trouble understanding that right now. "
                "Could you rephrase your question or ask something else?"
            ),
            'processing_tier': request.processing_tier,
            'is_fallback': True
        } 