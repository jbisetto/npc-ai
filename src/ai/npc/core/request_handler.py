"""
Request Handler

This module implements the request handler for the companion AI system.
It coordinates the flow of requests through the system.
"""

import logging
import traceback
import inspect
import time
from typing import Optional, Any, Dict, Tuple

from src.ai.npc.core.models import (
    NPCRequest,
    CompanionResponse,
    ConversationContext,
    ProcessingTier
)
from src.ai.npc.core.processor_framework import ProcessorFactory
from src.ai.npc.core.constants import METADATA_KEY_INTENT, INTENT_DEFAULT


class RequestHandler:
    """
    Handles processing of companion requests.
    Uses a single LLM processor based on configuration.
    """
    
    def __init__(
        self,
        processor_factory: ProcessorFactory,
        response_formatter,
        npc_name: str = "NPC"
    ):
        """
        Initialize the request handler.
        
        Args:
            processor_factory: The processor factory
            response_formatter: The response formatter
            npc_name: Name of the NPC handling requests
        """
        self.processor_factory = processor_factory
        self.response_formatter = response_formatter
        self.npc_name = npc_name
        self.logger = logging.getLogger(__name__)
    
    async def handle_request(self, request: NPCRequest) -> str:
        """
        Handle a companion request.
        
        Args:
            request: The request to handle
            
        Returns:
            The formatted response
            
        Raises:
            ValueError: If no LLM processors are enabled
        """
        self.logger.info(f"Handling request {request.request_id}")
        
        # Ensure request has an intent and NPC name
        if METADATA_KEY_INTENT not in request.additional_params:
            request.additional_params[METADATA_KEY_INTENT] = INTENT_DEFAULT
        if "name" not in request.additional_params:
            request.additional_params["name"] = self.npc_name
        
        # Set the processing tier directly on the request
        request.processing_tier = ProcessingTier.LOCAL
        
        # Get the processor and process the request
        try:
            processor = self.processor_factory.get_processor(ProcessingTier.LOCAL)
            response = await processor.process(request)
            
            # Handle both dictionary and string responses
            if isinstance(response, dict):
                response_text = response.get('response_text', '')
                # Update intent if provided in response
                if 'intent' in response:
                    request.additional_params[METADATA_KEY_INTENT] = response['intent']
            else:
                response_text = response
                
            return self.response_formatter.format_response(
                processor_response=response_text,
                classified_request=request
            )
        except Exception as e:
            self.logger.error(f"Error processing request {request.request_id}: {str(e)}")
            raise

    def _generate_fallback_response(self, request: NPCRequest) -> str:
        """Generate a fallback response when processing fails"""
        return "I'm sorry, I encountered an error while processing your request. Please try again."

    def _is_tier_enabled(self, tier: ProcessingTier, processor) -> bool:
        """Check if a tier is enabled in the configuration"""
        # Try to access the config attribute if it exists
        if hasattr(processor, 'config'):
            return processor.config.get('enabled', False)
        
        # Fallback to checking via the processor factory
        try:
            return self.processor_factory.is_tier_enabled(tier)
        except AttributeError:
            # If no method exists, we can't determine if it's enabled
            # Default to trying it anyway
            return True 