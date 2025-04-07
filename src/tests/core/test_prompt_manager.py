"""
Tests for the prompt manager module.

Test Strategy:
-------------
1. Unit Tests: Test prompt creation, optimization, and formatting
2. Error Tests: Test error handling and recovery
3. State Tests: Test state consistency and preservation
4. Performance Tests: Test under load and with large data
5. Coverage Goals: 90%+ line coverage, all error paths tested
"""

import pytest
from datetime import datetime
import psutil
import time

from src.ai.npc.core.models import (
    ProcessingTier,
    GameContext,
    ClassifiedRequest
)
from src.ai.npc.core.npc_profile import NPCProfile
from src.ai.npc.core.prompt_manager import PromptManager, BASE_SYSTEM_PROMPT
from src.tests.utils.factories import (
    create_test_request,
    create_test_game_context,
    create_test_response
)

# Register performance mark
performance = pytest.mark.performance

@pytest.fixture
def prompt_manager():
    """Create a PromptManager instance for testing."""
    return PromptManager(max_prompt_tokens=800)

@pytest.fixture
def sample_request():
    """Create a sample request for testing."""
    game_context = create_test_game_context(
        player_id="test_player",
        language_proficiency={"JLPT": 5.0, "speaking": 0.3, "listening": 0.4},
        conversation_history=[]
    )
    return create_test_request(
        request_id="test_id",
        player_input="Where is the ticket gate?",
        game_context=game_context
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

@pytest.fixture(scope="session")
def performance_threshold():
    """Fixture providing performance thresholds."""
    return {
        "max_prompt_gen_time": 0.5,  # 500ms
        "max_memory_increase": 50 * 1024 * 1024,  # 50MB
        "max_token_est_time": 0.1  # 100ms
    }

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
    request = create_test_request(
        request_id="test_id",
        player_input=long_input,
        game_context=create_test_game_context(conversation_history=[])
    )
    
    # Create prompt with small token limit
    small_manager = PromptManager(max_prompt_tokens=100)
    prompt = small_manager.create_prompt(request)
    
    # Check that the prompt is optimized to the minimal form
    expected_start = "You are Hachiko, a helpful bilingual dog companion."
    expected_rules = "RULES:\n1. Keep responses short\n2. Use JLPT N5 only\n3. Include Japanese and English"
    
    assert prompt.startswith(expected_start)
    assert expected_rules in prompt
    assert prompt.endswith(f"Human: {request.player_input}\nAssistant:")

def test_invalid_prompt_manager_init():
    """Test invalid PromptManager initialization."""
    with pytest.raises(ValueError):
        PromptManager(max_prompt_tokens=-1)  # Negative tokens should raise ValueError
    
    with pytest.raises(ValueError):
        PromptManager(max_prompt_tokens=0)  # Zero tokens should raise ValueError

def test_invalid_request_handling(prompt_manager):
    """Test handling of invalid requests."""
    # Test with None request
    with pytest.raises(ValueError):
        prompt_manager.create_prompt(None)
    
    # Test with invalid game context
    request = ClassifiedRequest(
        request_id="test_id",
        player_input="Test input",
        game_context=None,
        processing_tier=ProcessingTier.LOCAL,
        request_type="test",
        confidence=1.0,
        timestamp=datetime.now(),
        extracted_entities={},
        additional_params={}
    )
    with pytest.raises(ValueError):
        prompt_manager.create_prompt(request)
    
    # Test with empty player input
    empty_request = create_test_request(
        request_id="test_id",
        player_input="",
        game_context=create_test_game_context(conversation_history=[])
    )
    with pytest.raises(ValueError):
        prompt_manager.create_prompt(empty_request)

def test_token_estimation_error_recovery(prompt_manager):
    """Test recovery from token estimation errors."""
    # Test with invalid input types
    with pytest.raises(TypeError):
        prompt_manager.estimate_tokens(None)
    with pytest.raises(TypeError):
        prompt_manager.estimate_tokens(123)
    with pytest.raises(TypeError):
        prompt_manager.estimate_tokens([])
    
    # Test with valid string inputs
    assert prompt_manager.estimate_tokens("123.45") > 0
    assert prompt_manager.estimate_tokens("True") > 0
    assert prompt_manager.estimate_tokens("test") > 0

def test_prompt_state_consistency(prompt_manager, sample_request):
    """Test that prompt manager maintains consistent state."""
    # Create multiple prompts and verify they're consistent
    prompt1 = prompt_manager.create_prompt(sample_request)
    prompt2 = prompt_manager.create_prompt(sample_request)
    prompt3 = prompt_manager.create_prompt(sample_request)
    
    assert prompt1 == prompt2 == prompt3
    assert prompt_manager.max_prompt_tokens == 800

def test_optimization_state_preservation(prompt_manager, sample_request):
    """Test that optimization preserves essential information."""
    # Create a prompt with history
    history = [{"user": "Hello", "assistant": "Hi"}]
    prompt = prompt_manager.create_prompt(sample_request, history=history)
    
    # Check that essential information is preserved
    assert BASE_SYSTEM_PROMPT in prompt
    assert sample_request.player_input in prompt
    assert "Hello" in prompt
    assert "Hi" in prompt
    assert "Language Proficiency:" in prompt

@performance
def test_prompt_generation_performance(prompt_manager, sample_request, performance_threshold):
    """Test prompt generation performance."""
    start_time = time.time()
    
    # Generate multiple prompts
    for _ in range(100):
        prompt_manager.create_prompt(sample_request)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Check performance thresholds
    assert total_time / 100 < performance_threshold["max_prompt_gen_time"]
    # Token estimation should be fast but realistic
    token_start = time.time()
    tokens = prompt_manager.estimate_tokens("test")
    token_time = time.time() - token_start
    assert token_time < performance_threshold["max_token_est_time"]
    assert tokens > 0

@performance
def test_memory_usage_with_large_history(prompt_manager, sample_request, performance_threshold):
    """Test memory usage with large conversation history."""
    # Record initial memory usage
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    # Create large history
    large_history = []
    for i in range(1000):
        large_history.append({
            "user": f"User message {i}",
            "assistant": f"Assistant response {i}"
        })
    
    # Generate prompt with large history
    prompt_manager.create_prompt(sample_request, history=large_history)
    
    # Check memory usage
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    assert memory_increase < performance_threshold["max_memory_increase"] 