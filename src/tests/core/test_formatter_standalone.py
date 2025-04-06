"""
Tests for the standalone formatter module.

This module contains tests for the simple response formatter that doesn't require
external dependencies.
"""

import pytest
from src.ai.npc.core.formatter_standalone import format_response
from src.ai.npc.core.models import ClassifiedRequest, ProcessingTier, GameContext

# Test Data Fixtures
@pytest.fixture
def sample_request() -> ClassifiedRequest:
    """Create a sample classified request for testing."""
    return ClassifiedRequest(
        request_id="test_req_001",
        player_input="Hello",
        processing_tier=ProcessingTier.LOCAL,
        metadata={},
        game_context=GameContext(
            player_id="test_player",
            player_location="tokyo_station",
            language_proficiency={"reading": 0.5}
        )
    )

def test_format_response_with_normal_text(sample_request):
    """Test formatting a normal text response."""
    response = "Hello, how can I help you?"
    formatted = format_response(response, sample_request)
    assert formatted == "Hello, how can I help you?"

def test_format_response_with_whitespace(sample_request):
    """Test formatting text with extra whitespace."""
    response = "  Hello,  \n  how can I help you?  \t"
    formatted = format_response(response, sample_request)
    assert formatted == "Hello,  \n  how can I help you?"

def test_format_response_with_none(sample_request):
    """Test formatting when response is None."""
    formatted = format_response(None, sample_request)
    assert formatted == ""

def test_format_response_with_empty_string(sample_request):
    """Test formatting an empty string."""
    formatted = format_response("", sample_request)
    assert formatted == ""

def test_format_response_with_only_whitespace(sample_request):
    """Test formatting a string containing only whitespace."""
    formatted = format_response("   \n\t   ", sample_request)
    assert formatted == ""

def test_format_response_preserves_internal_whitespace(sample_request):
    """Test that internal whitespace is preserved."""
    response = "First line\n  Second line\n    Third line"
    formatted = format_response(response, sample_request)
    assert formatted == "First line\n  Second line\n    Third line"

def test_format_response_with_japanese_text(sample_request):
    """Test formatting text containing Japanese characters."""
    response = "  こんにちは、元気ですか？  "
    formatted = format_response(response, sample_request)
    assert formatted == "こんにちは、元気ですか？" 