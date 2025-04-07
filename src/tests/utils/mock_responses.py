"""
Mock response generators for testing.

This module provides utilities for generating mock LLM responses
in various formats for testing response parsing and formatting.
"""

from typing import Dict, Any, Optional


def create_mock_llm_response(
    text: str = "The ticket gate is straight ahead.",
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a mock LLM response dictionary.
    
    Args:
        text: The response text
        error: Optional error message
        metadata: Optional metadata to include
        
    Returns:
        A dictionary mimicking an LLM response
    """
    response = {
        "response_text": text,
        "is_error": error is not None,
        "error_message": error,
        "metadata": metadata or {}
    }
    
    return response


def create_mock_japanese_response(
    japanese_text: str = "切符売り場はまっすぐ前です。",
    english_text: str = "The ticket gate is straight ahead.",
    include_furigana: bool = False
) -> Dict[str, Any]:
    """
    Create a mock bilingual response.
    
    Args:
        japanese_text: The Japanese response text
        english_text: The English translation
        include_furigana: Whether to include furigana
        
    Returns:
        A dictionary with Japanese and English text
    """
    response = {
        "japanese": japanese_text,
        "english": english_text,
        "has_furigana": include_furigana
    }
    
    if include_furigana:
        response["furigana"] = "きっぷうりば は まっすぐ まえ です。"
        
    return response


def create_mock_error_response(
    error_type: str = "processing_error",
    error_message: str = "An error occurred processing your request.",
    error_details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a mock error response.
    
    Args:
        error_type: Type of error
        error_message: Error message
        error_details: Optional error details
        
    Returns:
        A dictionary representing an error response
    """
    response = {
        "is_error": True,
        "error_type": error_type,
        "error_message": error_message,
        "error_details": error_details or {},
        "response_text": None
    }
    
    return response 