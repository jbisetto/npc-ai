"""
Test module for the standalone formatter.

This module tests the simplified response formatter that handles basic text formatting
without any personality or learning cue enhancements.
"""

import pytest
from src.ai.npc.core.formatter_standalone import format_response
from src.tests.utils.factories import create_test_request
from src.tests.utils.mock_responses import (
    create_mock_llm_response,
    create_mock_japanese_response
)
from src.tests.utils.assertions import assert_valid_japanese


@pytest.fixture
def sample_request():
    """Create a sample request for testing."""
    return create_test_request(
        request_id="test-123",
        player_input="hello",
        request_type="greeting"
    )


def test_format_normal_text(sample_request):
    """Test formatting normal text."""
    mock_response = create_mock_llm_response("Hello, how can I help you?")
    formatted = format_response(mock_response["response_text"], sample_request)
    assert formatted == "Hello, how can I help you?"


def test_format_whitespace(sample_request):
    """Test formatting text with extra whitespace."""
    mock_response = create_mock_llm_response("  Hello,   how can I   help you?  ")
    formatted = format_response(mock_response["response_text"], sample_request)
    assert formatted == "Hello,   how can I   help you?"


def test_format_internal_whitespace(sample_request):
    """Test that internal whitespace is preserved."""
    mock_response = create_mock_llm_response("First line\n  Indented line\nLast line")
    formatted = format_response(mock_response["response_text"], sample_request)
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
    mock_response = create_mock_japanese_response(
        japanese_text="こんにちは、元気ですか？",
        english_text="Hello, how are you?"
    )
    formatted = format_response(mock_response["japanese"], sample_request)
    assert formatted == "こんにちは、元気ですか？"
    assert_valid_japanese(formatted, allow_romaji=False) 