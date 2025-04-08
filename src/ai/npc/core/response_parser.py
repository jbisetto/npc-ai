"""
Response Parser

This module provides unified response parsing and validation for all LLM responses,
whether from local or hosted models.
"""

import re
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Protocol

from src.ai.npc.core.models import ClassifiedRequest, ProcessingTier

logger = logging.getLogger(__name__)


class ResponseFormatter(Protocol):
    """Protocol defining how to format responses from different LLMs."""
    
    def format_response(self, raw_response: str) -> tuple[str, Optional[str]]:
        """
        Format a raw response from an LLM.
        
        Args:
            raw_response: The raw response from the language model
            
        Returns:
            Tuple of (response_text, thinking_section)
            thinking_section will be None if no thinking section is present
        """
        ...


class DeepSeekFormatter:
    """Formats responses from DeepSeek models which use <think> and <thinking> tags."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def format_response(self, raw_response: str) -> tuple[str, Optional[str]]:
        # Look for both <think> and <thinking> tags
        think_patterns = [
            r'<think>(.*?)</think>',
            r'<thinking>(.*?)</thinking>'
        ]
        
        self.logger.debug(f"Processing raw response: {raw_response}")
        
        # Extract all thinking sections
        thinking_sections = []
        main_response = raw_response.strip()
        
        for pattern in think_patterns:
            matches = re.finditer(pattern, main_response, re.DOTALL)
            for match in matches:
                thinking_lines = []
                for line in match.group(1).strip().splitlines():
                    thinking_lines.append(line.strip())
                thinking_sections.append('\n'.join(thinking_lines))
                # Remove the thinking section from the main response
                main_response = main_response.replace(match.group(0), '').strip()
        
        if thinking_sections:
            # Combine all thinking sections
            thinking = '\n'.join(thinking_sections)
            
            self.logger.debug(f"Extracted thinking: {thinking}")
            self.logger.debug(f"Main response (without thinking): {main_response}")
            
            return main_response, thinking
        
        self.logger.debug("No thinking tags found in response")
        return main_response, None


class DefaultFormatter:
    """Default formatter for LLMs that don't have special formatting needs."""
    
    def format_response(self, raw_response: str) -> tuple[str, Optional[str]]:
        return raw_response.strip(), None


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
    
    def __init__(self, formatter: Optional[ResponseFormatter] = None):
        """
        Initialize the response parser.
        
        Args:
            formatter: Optional response formatter to use. Defaults to DeepSeekFormatter.
        """
        self.logger = logging.getLogger(__name__)
        self.formatter = formatter or DeepSeekFormatter()
    
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
                - response_thinking: The thinking section if present
                - processing_tier: The processing tier (if request provided)
                - is_fallback: Whether this is a fallback response
        """
        try:
            # Convert to string first
            response_str = str(raw_response) if raw_response is not None else ""
            
            # Format the response using the configured formatter
            main_response, thinking_section = self.formatter.format_response(response_str)
            
            # Clean the main response
            cleaned_response = self._clean_response(main_response)
            
            # Then validate it
            validated_response = self._validate_response(cleaned_response)
            
            # Prepare the result
            result = {
                'response_text': validated_response,
                'response_thinking': thinking_section,
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
        """Clean a response by removing system tokens and normalizing whitespace."""
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
        """Validate a response and return either the original or a fallback."""
        if not response or len(response.strip()) < self.MIN_RESPONSE_LENGTH:
            return "I'm sorry, I couldn't generate a proper response. Could you try rephrasing your question?"
        
        return response
    
    def _create_error_response(self, request: Optional[ClassifiedRequest] = None) -> Dict[str, Any]:
        """Create an error response when parsing fails."""
        result = {
            'response_text': "I'm sorry, I encountered an error processing your request. Please try again.",
            'is_fallback': True
        }
        
        if request:
            result['processing_tier'] = request.processing_tier
            
        return result 