"""
Tests for the prompt manager module.
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from src.ai.npc.core.models import (
    ClassifiedRequest,
    ProcessingTier,
    GameContext
)
from src.ai.npc.core.prompt_manager import PromptManager, BASE_SYSTEM_PROMPT
from src.ai.npc.core.npc_profile import NPCProfile

@pytest.fixture
def prompt_manager():
    """Create a PromptManager instance for testing."""
    return PromptManager(max_prompt_tokens=800)

@pytest.fixture
def sample_request():
    """Create a sample request for testing."""
    return ClassifiedRequest(
        request_id="test_id",
        player_input="Where is the ticket gate?",
        game_context=GameContext(
            player_id="player1",
            language_proficiency={"JLPT": 5, "speaking": 0.3, "listening": 0.4}
        ),
        processing_tier=ProcessingTier.LOCAL,
        timestamp=datetime.now()
    )

@pytest.fixture
def sample_history():
    """Create sample conversation history for testing."""
    return [
        {
            "user": "Hello!",
            "assistant": "こんにちは! Hi there!"
        },
        {
            "user": "How are you?",
            "assistant": "元気です! I'm fine!"
        }
    ]

def test_create_basic_prompt(prompt_manager, sample_request):
    """Test creating a basic prompt with just a request."""
    prompt = prompt_manager.create_prompt(sample_request)
    
    # Check that the prompt contains essential parts
    assert BASE_SYSTEM_PROMPT in prompt
    assert sample_request.player_input in prompt
    assert "Human:" in prompt
    assert "Assistant:" in prompt

def test_create_prompt_with_history(prompt_manager, sample_request, sample_history):
    """Test creating a prompt with conversation history."""
    prompt = prompt_manager.create_prompt(sample_request, history=sample_history)
    
    # Check that history is included
    assert "Previous conversation:" in prompt
    assert "Hello!" in prompt
    assert "こんにちは" in prompt
    assert "How are you?" in prompt
    assert "元気です" in prompt

def test_create_prompt_with_game_context(prompt_manager, sample_request):
    """Test creating a prompt with game context."""
    prompt = prompt_manager.create_prompt(sample_request)
    
    # Check that game context is included
    assert "Language Proficiency:" in prompt
    assert "JLPT" in prompt
    assert "speaking" in prompt
    assert "listening" in prompt

def test_token_estimation(prompt_manager):
    """Test token estimation functionality."""
    # Test empty string
    assert prompt_manager.estimate_tokens("") == 1
    
    # Test short text
    short_text = "Hello, world!"
    assert prompt_manager.estimate_tokens(short_text) > 0
    
    # Test longer text
    long_text = "This is a much longer text that should result in more tokens."
    assert prompt_manager.estimate_tokens(long_text) > prompt_manager.estimate_tokens(short_text)

def test_prompt_optimization(prompt_manager, sample_request):
    """Test prompt optimization when exceeding token limit."""
    # Create a prompt manager with very low token limit
    small_manager = PromptManager(max_prompt_tokens=50)
    
    # Create a prompt that will exceed the limit
    prompt = small_manager.create_prompt(sample_request)
    
    # Check that the prompt is optimized to the minimal form
    expected_start = "You are Hachiko, a helpful bilingual dog companion."
    expected_rules = "RULES:\n1. Keep responses short\n2. Use JLPT N5 only\n3. Include Japanese and English"
    
    assert prompt.startswith(expected_start)
    assert expected_rules in prompt
    assert prompt.endswith(f"Human: {sample_request.player_input}\nAssistant:")

def test_text_truncation(prompt_manager):
    """Test text truncation functionality."""
    long_text = "This is a very long text that needs to be truncated to fit within token limits."
    truncated = prompt_manager._truncate_to_tokens(long_text, 5)
    
    # Check that truncation produces shorter text
    assert len(truncated) < len(long_text)
    assert prompt_manager.estimate_tokens(truncated) <= 5

def test_game_context_formatting(prompt_manager, sample_request):
    """Test game context formatting."""
    context_text = prompt_manager._format_game_context(sample_request.game_context)
    
    # Check that context includes essential information
    assert "Language Proficiency:" in context_text
    assert "JLPT: 5.0" in context_text
    assert "speaking: 0.3" in context_text
    assert "listening: 0.4" in context_text
    assert "Player ID:" in context_text

def test_prompt_with_npc_profile(prompt_manager, sample_request):
    """Test creating a prompt with an NPC profile."""
    # Create a mock NPC profile
    class MockProfile(NPCProfile):
        def get_prompt_context(self) -> str:
            return "I am a helpful station attendant."
        
        def get_response_format(self, request: ClassifiedRequest) -> str:
            return "You are a helpful NPC. Respond naturally to: {input}"

    profile = MockProfile(profile_id="station_attendant")
    prompt = prompt_manager.create_prompt(sample_request, profile=profile)
    
    # Check that profile context is included
    assert "I am a helpful station attendant" in prompt 

def test_empty_history_entries(prompt_manager, sample_request):
    """Test handling of empty or invalid history entries."""
    history = [
        {'user': '', 'assistant': ''},  # Empty entries
        {'unknown_key': 'test'},  # Invalid entry
        {'user': 'Hello', 'assistant': ''},  # Empty assistant
        {'user': '', 'assistant': 'Hi'},  # Empty user
        {'user': 'Test', 'assistant': 'Response'}  # Valid entry
    ]
    prompt = prompt_manager.create_prompt(sample_request, history=history)
    
    # Check that only valid entries are included
    assert "Human: Test" in prompt
    assert "Assistant: Response" in prompt
    assert "Human: Hello" not in prompt  # Entry with empty assistant should be skipped
    assert "Assistant: Hi" not in prompt  # Entry with empty user should be skipped
    assert "unknown_key" not in prompt

def test_long_player_input(prompt_manager):
    """Test handling of very long player inputs."""
    long_input = "What is the meaning of " + "very " * 200 + "long question?"
    request = ClassifiedRequest(
        request_id='test_id',
        player_input=long_input,
        game_context=GameContext(
            player_id='player1',
            language_proficiency={'JLPT': 5.0, 'speaking': 0.3, 'listening': 0.4}
        ),
        processing_tier=ProcessingTier.LOCAL
    )
    
    # Create prompt with small token limit
    small_manager = PromptManager(max_prompt_tokens=100)
    prompt = small_manager.create_prompt(request)
    
    # Check that the prompt is optimized to the minimal form
    expected_start = "You are Hachiko, a helpful bilingual dog companion."
    expected_rules = "RULES:\n1. Keep responses short\n2. Use JLPT N5 only\n3. Include Japanese and English"
    
    assert prompt.startswith(expected_start)
    assert expected_rules in prompt
    assert prompt.endswith(f"Human: {long_input}\nAssistant:")

def test_invalid_prompt_manager_init():
    """Test initialization with invalid token limits."""
    # Zero tokens should use default
    manager = PromptManager(max_prompt_tokens=0)
    assert manager.max_prompt_tokens == 800
    
    # Negative tokens should use default
    manager = PromptManager(max_prompt_tokens=-100)
    assert manager.max_prompt_tokens == 800 