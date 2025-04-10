"""
Tests for prompt configuration management.

This module tests that the PromptManager correctly respects configuration
settings for conversation history and knowledge context inclusion.
"""

import pytest
from unittest.mock import patch, MagicMock
import logging
from datetime import datetime

from src.ai.npc.core.models import ClassifiedRequest, GameContext, ProcessingTier
from src.ai.npc.core.prompt_manager import PromptManager
from src.ai.npc.core.adapters import ConversationHistoryEntry, KnowledgeDocument

# Set up logging
logging.basicConfig(level=logging.DEBUG)

@pytest.fixture
def sample_request():
    """Create a sample request for testing."""
    game_context = GameContext(
        player_id="test_player",
        npc_id="test_npc",
        language_proficiency={"japanese": 0.3},
        player_location="Tokyo Station",
        session_id="test_session"
    )
    return ClassifiedRequest(
        request_id="test_request",
        player_input="Hello there!",
        game_context=game_context,
        processing_tier=ProcessingTier.LOCAL,
        request_type="greeting",
        confidence=1.0,
        timestamp=datetime.now(),
        extracted_entities={},
        additional_params={"intent": "greeting"}
    )

@pytest.fixture
def sample_history():
    """Create sample conversation history for testing."""
    return [
        ConversationHistoryEntry(
            user="How do I say 'hello' in Japanese?",
            assistant="Hello is 'こんにちは' (konnichiwa) in Japanese.",
            timestamp=datetime.now().isoformat(),
            metadata={"intent": "translation"}
        ),
        ConversationHistoryEntry(
            user="Thank you!",
            assistant="You're welcome! 'ありがとう' (arigatou) means 'thank you'.",
            timestamp=datetime.now().isoformat(),
            metadata={"intent": "greeting"}
        )
    ]

@pytest.fixture
def sample_knowledge():
    """Create sample knowledge documents for testing."""
    return [
        KnowledgeDocument(
            text="こんにちは (konnichiwa) is a greeting used during the day.",
            id="greeting-001",
            metadata={"source": "Japanese Phrasebook", "relevance_score": 0.95, "type": "vocabulary"}
        ),
        KnowledgeDocument(
            text="駅 (eki) means station in Japanese.",
            id="station-001",
            metadata={"source": "Station Guide", "relevance_score": 0.85, "type": "vocabulary"}
        )
    ]

def test_prompt_respects_conversation_history_config(sample_request, sample_history):
    """Test that the prompt manager respects include_conversation_history config."""
    # Create a prompt manager and directly set config flag
    prompt_manager = PromptManager()
    prompt_manager.include_conversation_history = False
    prompt_manager.include_knowledge_context = True
    
    # Create prompt with history
    prompt = prompt_manager.create_prompt(sample_request, history=sample_history)
    
    # Verify history is not included
    assert "Previous conversation:" not in prompt

def test_prompt_respects_knowledge_context_config(sample_request, sample_knowledge):
    """Test that the prompt manager respects include_knowledge_context config."""
    # Create a prompt manager and directly set config flag
    prompt_manager = PromptManager()
    prompt_manager.include_conversation_history = True
    prompt_manager.include_knowledge_context = False
    
    # Create prompt with knowledge context
    prompt = prompt_manager.create_prompt(sample_request, knowledge_context=sample_knowledge)
    
    # Verify knowledge context is not included
    assert "Relevant information:" not in prompt

def test_both_configs_disabled(sample_request, sample_history, sample_knowledge):
    """Test that both history and knowledge context can be disabled."""
    # Create a prompt manager and directly set config flags
    prompt_manager = PromptManager()
    prompt_manager.include_conversation_history = False
    prompt_manager.include_knowledge_context = False
    
    # Create prompt with both history and knowledge context
    prompt = prompt_manager.create_prompt(sample_request, history=sample_history, knowledge_context=sample_knowledge)
    
    # Verify neither is included
    assert "Previous conversation:" not in prompt
    assert "Relevant information:" not in prompt
    
    # But request is still there
    assert "CURRENT REQUEST:" in prompt
    assert "Hello there!" in prompt

def test_both_configs_enabled(sample_request, sample_history, sample_knowledge):
    """Test that both history and knowledge context can be enabled."""
    # Create a prompt manager and directly set config flags
    prompt_manager = PromptManager()
    prompt_manager.include_conversation_history = True
    prompt_manager.include_knowledge_context = True
    
    # Create prompt with both history and knowledge context
    prompt = prompt_manager.create_prompt(sample_request, history=sample_history, knowledge_context=sample_knowledge)
    
    # Verify both are included
    assert "Previous conversation:" in prompt
    assert "Relevant information:" in prompt
    
    # And request is there too
    assert "CURRENT REQUEST:" in prompt
    assert "Hello there!" in prompt 