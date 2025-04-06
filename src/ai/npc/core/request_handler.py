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
    CompanionRequest,
    ClassifiedRequest,
    CompanionResponse,
    ConversationContext,
    ProcessingTier
)
from src.ai.npc.core.processor_framework import ProcessorFactory


class RequestHandler:
    """
    Handles processing of companion requests.
    Uses a single LLM processor based on configuration.
    """
    
    def __init__(
        self,
        processor_factory: ProcessorFactory,
        response_formatter
    ):
        """
        Initialize the request handler.
        
        Args:
            processor_factory: The processor factory
            response_formatter: The response formatter
        """
        self.processor_factory = processor_factory
        self.response_formatter = response_formatter
        self.logger = logging.getLogger(__name__)
    
    async def handle_request(self, request: CompanionRequest) -> str:
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
        
        # Create classified request with default processing tier
        classified_request = ClassifiedRequest(
            request_id=request.request_id,
            player_input=request.player_input,
            request_type=request.request_type,
            processing_tier=ProcessingTier.LOCAL,
            confidence=1.0,
            extracted_entities={},
            additional_params=request.additional_params
        )
        
        # Get the processor and process the request
        try:
            processor = self.processor_factory.get_processor(ProcessingTier.LOCAL)
            response = await processor.process(classified_request)
            
            # Handle both dictionary and string responses
            if isinstance(response, dict):
                response_text = response.get('response_text', '')
            else:
                response_text = response
                
            return self.response_formatter.format_response(
                processor_response=response_text,
                classified_request=classified_request
            )
        except Exception as e:
            self.logger.error(f"Error processing request {request.request_id}: {str(e)}")
            raise

    def _generate_fallback_response(self, request: ClassifiedRequest) -> str:
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