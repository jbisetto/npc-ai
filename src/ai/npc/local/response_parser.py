"""
Response Parser

This module provides validation for responses from local language models.
"""

import re
import logging
from typing import Optional

from src.ai.npc.core.models import (
    ClassifiedRequest,
    ProcessingTier
)

logger = logging.getLogger(__name__)


class ResponseParser:
    """
    Validates responses from local language models.
    """
    
    def __init__(self):
        """Initialize the response parser module."""
        logger.debug("Initialized ResponseParser")
    
    def parse_response(self, raw_response: str, request: Optional[ClassifiedRequest] = None) -> str:
        """
        Validate and clean the response.
        
        Args:
            raw_response: The raw response from the language model
            request: Optional classified request that generated the response
            
        Returns:
            The validated response
        """
        try:
            # Validate the response
            validated_response = self._validate_raw_response(raw_response)
            if validated_response != raw_response:
                logger.warning(f"Response was malformed and has been replaced with a fallback")
            
            return validated_response.strip()
                
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            return "Error parsing response."

    def _validate_raw_response(self, response: str) -> str:
        """
        Validate the raw response to catch malformed or nonsensical responses.
        
        Args:
            response: The raw response from the language model
            
        Returns:
            Either the original response if valid, or a fallback response
        """
        # Check for empty response
        if not response or len(response.strip()) < 10:
            return "I'm sorry, I couldn't generate a proper response. Please try again."
            
        # Check for repetitive patterns that indicate malformed responses
        if re.search(r'Hachi:\s*$', response) or re.search(r'Hachi:\s*√', response):
            return "I'm sorry, I encountered an error while processing your request. Please try again."
            
        # Check for responses that are just repeating "Hachi:" multiple times
        hachi_count = response.count("Hachi:")
        if hachi_count > 2 and len(response.replace("Hachi:", "").strip()) < 20:
            return "I'm sorry, I couldn't generate a proper response. Please try again."
            
        return response 