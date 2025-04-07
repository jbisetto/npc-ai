"""
Test module for the standalone formatter.

This module tests the simplified response formatter that handles basic text formatting
without any personality or learning cue enhancements.
"""

import pytest
from src.ai.npc.core.formatter_standalone import format_response
from src.ai.npc.core.models import ClassifiedRequest, ProcessingTier


@pytest.fixture
def sample_request():
    """Create a sample request for testing."""
    return ClassifiedRequest(
        request_id="test-123",
        player_input="hello",
        request_type="greeting",
        processing_tier=ProcessingTier.LOCAL,
        confidence=1.0,
        extracted_entities={},
        additional_params={}
    )


def test_format_normal_text(sample_request):
    """Test formatting normal text."""
    response = "Hello, how can I help you?"
    formatted = format_response(response, sample_request)
    assert formatted == "Hello, how can I help you?"


def test_format_whitespace(sample_request):
    """Test formatting text with extra whitespace."""
    response = "  Hello,   how can I   help you?  "
    formatted = format_response(response, sample_request)
    assert formatted == "Hello,   how can I   help you?"


def test_format_internal_whitespace(sample_request):
    """Test that internal whitespace is preserved."""
    response = "First line\n  Indented line\nLast line"
    formatted = format_response(response, sample_request)
    assert formatted == "First line\n  Indented line\nLast line"


def test_format_none(sample_request):
    """Test formatting None input."""
    formatted = format_response(None, sample_request)
    assert formatted == ""


def test_format_empty_string(sample_request):
    """Test formatting empty string."""
    formatted = format_response("", sample_request)
    assert formatted == ""


def test_format_only_whitespace(sample_request):
    """Test formatting string with only whitespace."""
    formatted = format_response("   \n  \t  ", sample_request)
    assert formatted == ""


def test_format_japanese_text(sample_request):
    """Test formatting Japanese text."""
    response = "こんにちは、元気ですか？"
    formatted = format_response(response, sample_request)
    assert formatted == "こんにちは、元気ですか？" 