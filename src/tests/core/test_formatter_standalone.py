"""
Tests for the standalone formatter module.

This module contains tests for the simple response formatter that doesn't require
external dependencies. The formatter is responsible for basic text cleaning and
standardization of responses.

Test Strategy:
-------------
1. Unit Tests:
   - Basic functionality testing of format_response()
   - Edge case handling
   - Text cleaning verification
   - Unicode/Japanese text support

2. Coverage Goals:
   - Line coverage: 80%+
   - Branch coverage: 70%+
   - Function coverage: 90%+

3. Dependencies:
   - pytest for test framework
   - core.models for request types
   - No external service mocking needed (standalone component)
"""

import pytest
from src.ai.npc.core.formatter_standalone import format_response
from src.ai.npc.core.models import ClassifiedRequest, GameContext, ProcessingTier

# Test Fixtures
@pytest.fixture
def sample_request():
    """
    Create a sample request for testing.
    
    This fixture provides a standardized ClassifiedRequest object with:
    - Basic request metadata
    - Game context with player info
    - Local processing tier
    - Empty metadata (not used by formatter)
    
    Returns:
        ClassifiedRequest: A request object for testing
    """
    return ClassifiedRequest(
        request_id="test-123",
        player_input="Hello",
        request_type="greeting",
        timestamp="2024-04-06T12:00:00Z",
        game_context=GameContext(
            player_id="test_player",
            player_location="test_location",
            language_proficiency={"reading": 0.8, "speaking": 0.7},
            game_state={},
            player_state={},
            npc_state={}
        ),
        processing_tier=ProcessingTier.LOCAL,
        metadata={},
        additional_params={}
    )

# Basic Functionality Tests
def test_format_normal_text(sample_request):
    """
    Test basic text formatting functionality.
    
    Verifies that normal text passes through the formatter unchanged
    except for any outer whitespace removal.
    """
    response = "Hello, how are you?"
    formatted = format_response(response, sample_request)
    assert formatted == "Hello, how are you?"

# Whitespace Handling Tests
def test_format_whitespace(sample_request):
    """
    Test handling of various whitespace patterns.
    
    Verifies that:
    - Leading/trailing whitespace is removed
    - Internal whitespace is preserved
    - Multiple types of whitespace (spaces, newlines, tabs) are handled
    """
    response = "  Hello  \n  World  \t"
    formatted = format_response(response, sample_request)
    assert formatted == "Hello  \n  World"

def test_format_internal_whitespace(sample_request):
    """
    Test preservation of intentional internal whitespace.
    
    Verifies that meaningful whitespace between words is not altered
    while still cleaning external whitespace.
    """
    response = "Hello   World"  # Multiple spaces between words
    formatted = format_response(response, sample_request)
    assert formatted == "Hello   World"

# Edge Case Tests
def test_format_none(sample_request):
    """
    Test handling of None input.
    
    Verifies that None is safely converted to an empty string
    without raising exceptions.
    """
    formatted = format_response(None, sample_request)
    assert formatted == ""

def test_format_empty_string(sample_request):
    """
    Test handling of empty string input.
    
    Verifies that empty strings remain empty after formatting.
    """
    formatted = format_response("", sample_request)
    assert formatted == ""

def test_format_only_whitespace(sample_request):
    """
    Test handling of whitespace-only input.
    
    Verifies that strings containing only whitespace characters
    are converted to empty strings.
    """
    formatted = format_response("   \n\t   ", sample_request)
    assert formatted == ""

# Unicode/International Text Tests
def test_format_japanese_text(sample_request):
    """
    Test handling of Japanese Unicode text.
    
    Verifies that:
    - Unicode characters are preserved
    - Whitespace rules apply correctly to Unicode strings
    - No encoding/decoding issues occur
    """
    response = "  こんにちは、世界！  "
    formatted = format_response(response, sample_request)
    assert formatted == "こんにちは、世界！" 