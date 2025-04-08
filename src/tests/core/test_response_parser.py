"""
Test module for the unified response parser.

This module tests the ResponseParser class that handles response validation
and cleaning for both local and hosted LLM responses.
"""

import pytest
from src.ai.npc.core.response_parser import (
    ResponseParser,
    DeepSeekFormatter,
    DefaultFormatter
)
from src.ai.npc.core.models import ClassifiedRequest, ProcessingTier
from src.tests.utils.factories import create_test_request
from src.tests.utils.mock_responses import (
    create_mock_llm_response,
    create_mock_japanese_response
)
from src.tests.utils.assertions import assert_valid_response
import textwrap
import json


@pytest.fixture
def parser():
    """Create a ResponseParser instance for testing."""
    return ResponseParser(formatter=DeepSeekFormatter())


@pytest.fixture
def default_parser():
    """Create a ResponseParser instance with default formatter."""
    return ResponseParser(formatter=DefaultFormatter())


@pytest.fixture
def sample_request():
    """Create a sample request for testing."""
    return create_test_request(
        request_id="test-123",
        player_input="hello",
        request_type="greeting"
    )


def test_explicit_thinking_section(parser):
    """Test extracting both <think> and <thinking> sections while removing them from the response."""
    response = """<think>Planning my response:
1. Greet in English
2. Add Japanese translation</think>
<thinking>Additional thoughts about formatting</thinking>
English: Hello there!
Japanese: こんにちは！"""
    result = parser.parse_response(response)
    assert_valid_response(result)
    # Verify thinking sections are removed from response_text
    assert result['response_text'] == "English: Hello there!\nJapanese: こんにちは！"
    # Verify both thinking sections are extracted and combined
    assert result['response_thinking'] == "Planning my response:\n1. Greet in English\n2. Add Japanese translation\nAdditional thoughts about formatting"
    assert not result['is_fallback']


def test_single_think_tag(parser):
    """Test extracting just <think> tag while removing it from the response."""
    response = """<think>Planning my response:
1. Greet in English
2. Add Japanese translation</think>
English: Hello there!
Japanese: こんにちは！"""
    result = parser.parse_response(response)
    assert_valid_response(result)
    # Verify thinking section is removed from response_text
    assert result['response_text'] == "English: Hello there!\nJapanese: こんにちは！"
    # Verify thinking section is extracted
    assert result['response_thinking'] == "Planning my response:\n1. Greet in English\n2. Add Japanese translation"
    assert not result['is_fallback']


def test_single_thinking_tag(parser):
    """Test extracting just <thinking> tag while removing it from the response."""
    response = """<thinking>Additional thoughts about formatting</thinking>
English: Hello there!
Japanese: こんにちは！"""
    result = parser.parse_response(response)
    assert_valid_response(result)
    # Verify thinking section is removed from response_text
    assert result['response_text'] == "English: Hello there!\nJapanese: こんにちは！"
    # Verify thinking section is extracted
    assert result['response_thinking'] == "Additional thoughts about formatting"
    assert not result['is_fallback']


def test_no_thinking_section(parser):
    """Test handling response without any thinking section."""
    response = """English: Hello there!
    Japanese: こんにちは！"""
    result = parser.parse_response(response)
    assert_valid_response(result)
    assert result['response_text'] == "English: Hello there!\nJapanese: こんにちは！"
    assert result['response_thinking'] is None
    assert not result['is_fallback']


def test_default_formatter(default_parser):
    """Test that default formatter doesn't extract thinking sections."""
    response = """<thinking>Planning my response:
1. Greet in English
2. Add Japanese translation</thinking>
English: Hello there!
Japanese: こんにちは！"""
    result = default_parser.parse_response(response)
    assert_valid_response(result)
    assert result['response_text'] == response.strip()
    assert result['response_thinking'] is None
    assert not result['is_fallback']


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


def test_real_world_thinking_sections(parser):
    """Test handling a real-world response with both <think> and <thinking> sections."""
    response = textwrap.dedent("""<think>
Okay, so the user asked "Who are you?" and I responded that I'm Hachiko, a friendly dog companion. Now, I need to break down how I came up with this response using only N5 guidelines.
First, I used basic Japanese particles like は and が but kept it simple. Then, for the English part, "I am a helpful bilingual..." is straightforward and clear. Translating that into hiragana gives me something easy to understand without complex kanji.
I made sure each part was concise, fitting within three sentences as per the constraints. Also, I included both languages in the response format required. Finally, pronouncing the words was kept simple so it's easy for the user to grasp quickly.
</think>
<thinking>
The user asked "Who are you?" and I need to respond using only N5 vocabulary and grammar. I'll use a friendly and encouraging tone with simple particles like は and が. The response should be concise, fitting within three sentences in both Japanese and English.</thinking>
**English Answer:**
I am a helpful bilingual dog companion.
**Japanese Phrase (Hiragana):**
はい、私は JAPANESE PHONETIC: "I am a helpful bilingual dog companion."
**Pronunciation Guide:**
"I AM A HELPFUL BILINGUAL DOG COMPELLER\"""")
    
    result = parser.parse_response(response)
    assert_valid_response(result)
    
    # Print the full parsed response
    print("\nFull parsed response:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Verify the response text has thinking sections removed
    expected_response_text = """**English Answer:**
I am a helpful bilingual dog companion.
**Japanese Phrase (Hiragana):**
はい、私は JAPANESE PHONETIC: "I am a helpful bilingual dog companion."
**Pronunciation Guide:**
"I AM A HELPFUL BILINGUAL DOG COMPELLER\""""
    assert result['response_text'] == expected_response_text
    
    # Verify both thinking sections are extracted and combined
    expected_thinking = """Okay, so the user asked "Who are you?" and I responded that I'm Hachiko, a friendly dog companion. Now, I need to break down how I came up with this response using only N5 guidelines.
First, I used basic Japanese particles like は and が but kept it simple. Then, for the English part, "I am a helpful bilingual..." is straightforward and clear. Translating that into hiragana gives me something easy to understand without complex kanji.
I made sure each part was concise, fitting within three sentences as per the constraints. Also, I included both languages in the response format required. Finally, pronouncing the words was kept simple so it's easy for the user to grasp quickly.
The user asked "Who are you?" and I need to respond using only N5 vocabulary and grammar. I'll use a friendly and encouraging tone with simple particles like は and が. The response should be concise, fitting within three sentences in both Japanese and English."""
    
    assert result['response_thinking'] == expected_thinking
    assert not result['is_fallback'] 