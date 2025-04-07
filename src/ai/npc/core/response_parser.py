"""
Response Parser

This module provides unified response parsing and validation for all LLM responses,
whether from local or hosted models.
"""

import re
import logging
from typing import Optional, Dict, Any

from src.ai.npc.core.models import ClassifiedRequest, ProcessingTier

logger = logging.getLogger(__name__)


class ResponseParser:
    """
    Validates and cleans responses from language models.
    
    This parser handles:
    1. Basic validation (empty/short responses)
    2. Cleaning (removing system tokens, tags)
    3. Error handling and fallback responses
    """
    
    # Minimum response length (in characters) to be considered valid
    MIN_RESPONSE_LENGTH = 10
    
    # System tokens/tags to remove
    SYSTEM_TOKENS = [
        "<assistant>",
        "</assistant>",
        "Assistant:",
        "AI:",
    ]
    
    def __init__(self):
        """Initialize the response parser."""
        self.logger = logging.getLogger(__name__)
    
    def parse_response(
        self,
        raw_response: str,
        request: Optional[ClassifiedRequest] = None
    ) -> Dict[str, Any]:
        """
        Parse and validate a response from any LLM.
        
        Args:
            raw_response: The raw response from the language model
            request: Optional request that generated the response
            
        Returns:
            Dict containing:
                - response_text: The cleaned and validated response
                - processing_tier: The processing tier (if request provided)
                - is_fallback: Whether this is a fallback response
        """
        try:
            # Convert to string first
            response_str = str(raw_response) if raw_response is not None else ""
            
            # Clean the response
            cleaned_response = self._clean_response(response_str)
            
            # Then validate it
            validated_response = self._validate_response(cleaned_response)
            
            # Prepare the result
            result = {
                'response_text': validated_response,
                'is_fallback': validated_response != cleaned_response
            }
            
            # Add processing tier if request is provided
            if request:
                result['processing_tier'] = request.processing_tier
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error parsing response: {str(e)}")
            return self._create_error_response(request)
    
    def _clean_response(self, response: str) -> str:
        """
        Clean a response by removing system tokens and normalizing whitespace.
        
        Args:
            response: The response to clean
            
        Returns:
            The cleaned response
        """
        if not response:
            return ""
            
        cleaned = response.strip()
        
        # Remove system tokens
        for token in self.SYSTEM_TOKENS:
            cleaned = cleaned.replace(token, "")
        
        # Normalize whitespace but preserve intentional newlines
        lines = []
        for line in cleaned.splitlines():
            # Normalize whitespace within each line
            normalized = ' '.join(word for word in line.split() if word)
            if normalized:
                lines.append(normalized)
        
        # Join lines with newlines
        cleaned = '\n'.join(lines)
        
        return cleaned
    
    def _validate_response(self, response: str) -> str:
        """
        Validate a response and return either the original or a fallback.
        
        Args:
            response: The response to validate
            
        Returns:
            Either the original response if valid, or a fallback response
        """
        # Check for empty or too short responses
        if not response or len(response.strip()) < self.MIN_RESPONSE_LENGTH:
            return "I'm sorry, I couldn't generate a proper response. Could you try rephrasing your question?"
        
        return response
    
    def _create_error_response(self, request: Optional[ClassifiedRequest] = None) -> Dict[str, Any]:
        """
        Create an error response when parsing fails.
        
        Args:
            request: Optional request that generated the response
            
        Returns:
            Dict containing error response and metadata
        """
        result = {
            'response_text': "I'm sorry, I encountered an error processing your request. Please try again.",
            'is_fallback': True
        }
        
        if request:
            result['processing_tier'] = request.processing_tier
            
        return result 