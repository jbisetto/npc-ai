"""
Tests for ConversationManager

This module tests the conversation manager, which is responsible for managing
conversation history, detecting conversation state, and generating contextual prompts.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime
from typing import Dict, Any

from src.ai.npc.core.models import (
    ClassifiedRequest,
    ProcessingTier,
    GameContext
)
from src.ai.npc.core.context_manager import (
    ConversationContext,
    ContextManager,
    ContextEntry
)
from src.ai.npc.hosted.conversation_manager import ConversationManager, ConversationState

@pytest.fixture
def sample_game_context():
    """Sample game context for testing."""
    return GameContext(
        player_id="test_player",
        language_proficiency={"reading": 0.5, "speaking": 0.3},
        conversation_history=[]
    )

@pytest.fixture
def sample_classified_request(sample_game_context):
    """Sample classified request for testing."""
    return ClassifiedRequest(
        request_id="test-123",
        player_input="tell me more about train tickets",
        processing_tier=ProcessingTier.HOSTED,
        game_context=sample_game_context,
        timestamp=datetime.now(),
        additional_params={"conversation_id": "test-conv-123"}
    )

@pytest.fixture
def sample_context():
    """Sample conversation context for testing."""
    return ConversationContext(
        conversation_id="test-conv-123",
        player_id="test_player",
        player_language_level="N5",
        current_location="tokyo_station"
    )

class TestConversationManager:
    
    def test_conversation_manager_creation(self):
        """Test creating a conversation manager."""
        manager = ConversationManager()
        assert manager is not None
        assert hasattr(manager, 'follow_up_patterns')
        assert hasattr(manager, 'clarification_patterns')
    
    def test_detect_conversation_state(self, sample_classified_request, sample_context):
        """Test detecting conversation state."""
        manager = ConversationManager()
        
        # Add some context entries
        context_entry = ContextEntry(
            player_input="What is a train ticket called in Japanese?",
            response="A train ticket in Japanese is called 'kippu' (切符).",
            game_context=sample_classified_request.game_context
        )
        sample_context.add_entry(context_entry)
        
        # Test with a follow-up question
        sample_classified_request.player_input = "tell me more about train tickets"
        state = manager.detect_conversation_state(sample_classified_request, sample_context)
        assert state == ConversationState.FOLLOW_UP
        
        # Test with a clarification request
        sample_classified_request.player_input = "I don't understand what you mean"
        state = manager.detect_conversation_state(sample_classified_request, sample_context)
        assert state == ConversationState.CLARIFICATION
        
        # Test with a new topic
        sample_classified_request.player_input = "What time does the train to Tokyo leave?"
        state = manager.detect_conversation_state(sample_classified_request, sample_context)
        assert state == ConversationState.NEW_TOPIC
    
    def test_generate_contextual_prompt(self, sample_classified_request, sample_context):
        """Test generating a contextual prompt."""
        manager = ConversationManager()
        
        # Test with a follow-up question
        sample_classified_request.player_input = "tell me more about train tickets"
        state = ConversationState.FOLLOW_UP
        
        prompt = manager.generate_contextual_prompt(
            sample_classified_request,
            sample_context,
            state
        )
        
        # Check that the prompt contains instructions for handling follow-up questions
        assert "follow-up question" in prompt.lower()
        assert sample_classified_request.player_input in prompt
    
    def test_handle_follow_up_question(self, sample_classified_request, sample_context):
        """Test handling a follow-up question."""
        manager = ConversationManager()
        context_manager = MagicMock()
        context_manager.get_context.return_value = sample_context
        
        bedrock_client = MagicMock()
        bedrock_client.generate_text.return_value = "Here's more information about train tickets..."
        
        response = manager.handle_follow_up_question(
            sample_classified_request,
            context_manager,
            bedrock_client
        )
        
        assert response == "Here's more information about train tickets..."
        bedrock_client.generate_text.assert_called_once()
    
    def test_handle_clarification(self, sample_classified_request, sample_context):
        """Test handling a clarification request."""
        manager = ConversationManager()
        context_manager = MagicMock()
        context_manager.get_context.return_value = sample_context
        
        bedrock_client = MagicMock()
        bedrock_client.generate_text.return_value = "Let me clarify..."
        
        response = manager.handle_clarification(
            sample_classified_request,
            context_manager,
            bedrock_client
        )
        
        assert response == "Let me clarify..."
        bedrock_client.generate_text.assert_called_once()
    
    def test_handle_new_topic(self, sample_classified_request):
        """Test handling a new topic."""
        manager = ConversationManager()
        bedrock_client = MagicMock()
        bedrock_client.generate_text.return_value = "Here's information about your new topic..."
        
        response = manager.handle_new_topic(
            sample_classified_request,
            bedrock_client
        )
        
        assert response == "Here's information about your new topic..."
        bedrock_client.generate_text.assert_called_once()
    
    def test_process(self, sample_classified_request, sample_context):
        """Test the main process method."""
        manager = ConversationManager()
        context_manager = MagicMock()
        context_manager.get_context.return_value = sample_context
        
        bedrock_client = MagicMock()
        bedrock_client.generate_text.return_value = "Here's your response..."
        
        response = manager.process(
            sample_classified_request,
            context_manager,
            bedrock_client
        )
        
        assert response == "Here's your response..."
        bedrock_client.generate_text.assert_called_once() 