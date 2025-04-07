"""
Test module for the unified response parser.

This module tests the ResponseParser class that handles response validation
and cleaning for both local and hosted LLM responses.
"""

import pytest
from src.ai.npc.core.response_parser import ResponseParser
from src.ai.npc.core.models import ClassifiedRequest, ProcessingTier
from src.tests.utils.factories import create_test_request
from src.tests.utils.mock_responses import (
    create_mock_llm_response,
    create_mock_japanese_response
)
from src.tests.utils.assertions import assert_valid_response


@pytest.fixture
def parser():
    """Create a ResponseParser instance for testing."""
    return ResponseParser()


@pytest.fixture
def sample_request():
    """Create a sample request for testing."""
    return create_test_request(
        request_id="test-123",
        player_input="hello",
        request_type="greeting"
    )


def test_clean_normal_response(parser):
    """Test cleaning a normal response."""
    mock_response = create_mock_llm_response("Hello, how can I help you?")
    result = parser.parse_response(mock_response["response_text"])
    assert_valid_response(result)
    assert result['response_text'] == "Hello, how can I help you?"
    assert not result['is_fallback']


def test_clean_response_with_system_tokens(parser):
    """Test cleaning a response with system tokens."""
    mock_response = create_mock_llm_response("<assistant>Hello</assistant> AI: How can I help you?")
    result = parser.parse_response(mock_response["response_text"])
    assert_valid_response(result)
    assert result['response_text'] == "Hello How can I help you?"
    assert not result['is_fallback']


def test_clean_whitespace(parser):
    """Test cleaning whitespace."""
    mock_response = create_mock_llm_response("  Hello  \n  World  \t")
    result = parser.parse_response(mock_response["response_text"])
    assert_valid_response(result)
    assert result['response_text'] == "Hello\nWorld"
    assert not result['is_fallback']


def test_empty_response(parser):
    """Test handling empty response."""
    result = parser.parse_response("")
    assert_valid_response(result)
    assert result['response_text'] == "I'm sorry, I couldn't generate a proper response. Could you try rephrasing your question?"
    assert result['is_fallback']


def test_none_response(parser):
    """Test handling None response."""
    result = parser.parse_response(None)
    assert_valid_response(result)
    assert result['response_text'] == "I'm sorry, I couldn't generate a proper response. Could you try rephrasing your question?"
    assert result['is_fallback']


def test_too_short_response(parser):
    """Test handling too short response."""
    mock_response = create_mock_llm_response("Hi")
    result = parser.parse_response(mock_response["response_text"])
    assert_valid_response(result)
    assert result['response_text'] == "I'm sorry, I couldn't generate a proper response. Could you try rephrasing your question?"
    assert result['is_fallback']


def test_response_with_request(parser, sample_request):
    """Test parsing response with request context."""
    mock_response = create_mock_llm_response("Hello there!")
    result = parser.parse_response(mock_response["response_text"], sample_request)
    assert_valid_response(result)
    assert result['response_text'] == "Hello there!"
    assert not result['is_fallback']
    assert result['processing_tier'] == ProcessingTier.LOCAL


def test_error_handling(parser, monkeypatch):
    """Test error handling during parsing."""
    def mock_clean_response(self, response):
        raise ValueError("Test error")
    
    # Patch the _clean_response method to raise an error
    monkeypatch.setattr(ResponseParser, '_clean_response', mock_clean_response)
    
    result = parser.parse_response("test")
    assert_valid_response(result)
    assert result['response_text'] == "I'm sorry, I encountered an error processing your request. Please try again."
    assert result['is_fallback']


def test_japanese_text(parser):
    """Test handling Japanese text."""
    mock_response = create_mock_japanese_response(
        japanese_text="こんにちは、元気ですか？",
        english_text="Hello, how are you?"
    )
    result = parser.parse_response(mock_response["japanese"])
    assert_valid_response(result)
    assert result['response_text'] == "こんにちは、元気ですか？"
    assert not result['is_fallback']


def test_multiline_response(parser):
    """Test handling multiline response."""
    mock_response = create_mock_llm_response("Line 1\n  Line 2\nLine 3")
    result = parser.parse_response(mock_response["response_text"])
    assert_valid_response(result)
    assert result['response_text'] == "Line 1\nLine 2\nLine 3"
    assert not result['is_fallback']


def test_all_system_tokens_removed(parser):
    """Test that all system tokens are removed."""
    mock_response = create_mock_llm_response("<assistant>AI: Hello Assistant: there!</assistant>")
    result = parser.parse_response(mock_response["response_text"])
    assert_valid_response(result)
    assert result['response_text'] == "Hello there!"
    assert not result['is_fallback'] 