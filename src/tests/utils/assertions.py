"""
Custom assertions for testing.

This module provides custom assertion functions for validating
responses, contexts, and other test data.
"""

import json
import re
from typing import Dict, Any, Union
from pathlib import Path

from src.ai.npc.core.models import ConversationContext


def assert_valid_response(
    response: Dict[str, Any],
    expected_fields: list = None,
    allow_extra: bool = True
) -> None:
    """
    Assert that a response dictionary is valid.
    
    Args:
        response: The response dictionary to validate
        expected_fields: List of required field names
        allow_extra: Whether to allow extra fields
    
    Raises:
        AssertionError: If validation fails
    """
    if expected_fields is None:
        expected_fields = ["response_text", "is_error"]
        
    # Check required fields
    for field in expected_fields:
        assert field in response, f"Missing required field: {field}"
    
    # Check for unexpected fields
    if not allow_extra:
        extra_fields = set(response.keys()) - set(expected_fields)
        assert not extra_fields, f"Unexpected fields: {extra_fields}"
    
    # Basic type checks
    if "is_error" in response:
        assert isinstance(response["is_error"], bool)
    if "response_text" in response and response["response_text"] is not None:
        assert isinstance(response["response_text"], str)


def assert_valid_context(context: ConversationContext) -> None:
    """
    Assert that a conversation context is valid.
    
    Args:
        context: The context to validate
    
    Raises:
        AssertionError: If validation fails
    """
    assert context.player_id, "Missing player_id"
    assert isinstance(context.player_language_level, dict), "Invalid player_language_level"
    assert isinstance(context.entries, list), "Invalid entries list"
    
    # Validate entries if any exist
    for entry in context.entries:
        assert hasattr(entry, "player_input"), "Missing player_input in entry"
        assert hasattr(entry, "response"), "Missing response in entry"
        assert hasattr(entry, "game_context"), "Missing game_context in entry"
        assert hasattr(entry, "timestamp"), "Missing timestamp in entry"


def assert_valid_json(
    file_path: Union[str, Path],
    required_fields: list = None
) -> None:
    """
    Assert that a JSON file is valid and contains required fields.
    
    Args:
        file_path: Path to the JSON file
        required_fields: List of required field names
        
    Raises:
        AssertionError: If validation fails
    """
    file_path = Path(file_path)
    assert file_path.exists(), f"File does not exist: {file_path}"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise AssertionError(f"Invalid JSON in {file_path}: {e}")
    
    if required_fields:
        for field in required_fields:
            assert field in data, f"Missing required field in {file_path}: {field}"


def assert_valid_japanese(
    text: str,
    allow_romaji: bool = False,
    allow_english: bool = True
) -> None:
    """
    Assert that text contains valid Japanese content.
    
    Args:
        text: The text to validate
        allow_romaji: Whether to allow romaji
        allow_english: Whether to allow English
        
    Raises:
        AssertionError: If validation fails
    """
    # Check for Japanese characters (hiragana, katakana, kanji)
    has_japanese = bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text))
    assert has_japanese, "Text contains no Japanese characters"
    
    if not allow_romaji:
        has_romaji = bool(re.search(r'[a-zA-Z]', text))
        assert not has_romaji, "Text contains romaji"
    
    if not allow_english:
        # More thorough check for English words (allows for punctuation)
        has_english = bool(re.search(r'\b[a-zA-Z]+\b', text))
        assert not has_english, "Text contains English words" 