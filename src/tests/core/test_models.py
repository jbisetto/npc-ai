"""
Tests for the core data models.

This module contains tests for all the data models defined in src.ai.npc.core.models.
Following our testing guidelines, each test is isolated and uses no shared resources.
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from src.ai.npc.core.models import (
    ProcessingTier,
    GameContext,
    CompanionRequest,
    ClassifiedRequest,
    CompanionResponse,
    ConversationContext
)

# Test Data Fixtures
@pytest.fixture
def sample_game_context() -> Dict[str, Any]:
    """Create a sample game context dictionary."""
    return {
        "player_id": "test_player",
        "player_location": "tokyo_station",
        "language_proficiency": {"reading": 0.5, "speaking": 0.3},
        "current_quest": "find_platform",
        "npc_id": "station_attendant",
        "conversation_history": []
    }

@pytest.fixture
def sample_request_data() -> Dict[str, Any]:
    """Create a sample request dictionary."""
    return {
        "request_id": "test_req_001",
        "player_input": "Where is platform 3?",
    }

# ProcessingTier Tests
def test_processing_tier_values():
    """Test ProcessingTier enum values."""
    assert ProcessingTier.LOCAL.value == "local"
    assert ProcessingTier.HOSTED.value == "hosted"
    assert len(ProcessingTier) == 2

# GameContext Tests
def test_game_context_creation(sample_game_context):
    """Test creating a GameContext with valid data."""
    context = GameContext(**sample_game_context)
    assert context.player_id == "test_player"
    assert context.player_location == "tokyo_station"
    assert context.language_proficiency["reading"] == 0.5
    assert context.current_quest == "find_platform"
    assert context.npc_id == "station_attendant"
    assert context.conversation_history == []

def test_game_context_optional_fields():
    """Test GameContext with only required fields."""
    minimal_context = GameContext(
        player_id="test_player",
        player_location="tokyo_station",
        language_proficiency={"reading": 0.5}
    )
    assert minimal_context.current_quest is None
    assert minimal_context.npc_id is None
    assert minimal_context.conversation_history is None

def test_game_context_to_dict(sample_game_context):
    """Test GameContext to_dict method."""
    context = GameContext(**sample_game_context)
    context_dict = context.to_dict()
    assert context_dict == sample_game_context

# CompanionRequest Tests
def test_companion_request_creation(sample_request_data, sample_game_context):
    """Test creating a CompanionRequest with valid data."""
    game_context = GameContext(**sample_game_context)
    request_data = sample_request_data.copy()
    request_data["game_context"] = game_context
    
    request = CompanionRequest(**request_data)
    assert request.request_id == "test_req_001"
    assert request.player_input == "Where is platform 3?"
    assert isinstance(request.game_context, GameContext)

def test_companion_request_without_context(sample_request_data):
    """Test creating a CompanionRequest without game context."""
    request = CompanionRequest(**sample_request_data)
    assert request.game_context is None

def test_companion_request_to_dict(sample_request_data, sample_game_context):
    """Test CompanionRequest to_dict method."""
    game_context = GameContext(**sample_game_context)
    request_data = sample_request_data.copy()
    request_data["game_context"] = game_context
    
    request = CompanionRequest(**request_data)
    request_dict = request.to_dict()
    
    assert request_dict["request_id"] == "test_req_001"
    assert request_dict["player_input"] == "Where is platform 3?"
    assert request_dict["game_context"] == game_context.to_dict()

# ClassifiedRequest Tests
def test_classified_request_creation(sample_request_data, sample_game_context):
    """Test creating a ClassifiedRequest with valid data."""
    game_context = GameContext(**sample_game_context)
    request_data = sample_request_data.copy()
    request_data["game_context"] = game_context
    request_data["processing_tier"] = ProcessingTier.LOCAL
    request_data["metadata"] = {"confidence": 0.9}
    
    request = ClassifiedRequest(**request_data)
    assert request.processing_tier == ProcessingTier.LOCAL
    assert request.metadata["confidence"] == 0.9

def test_classified_request_to_dict(sample_request_data, sample_game_context):
    """Test ClassifiedRequest to_dict method."""
    game_context = GameContext(**sample_game_context)
    request_data = sample_request_data.copy()
    request_data["game_context"] = game_context
    request_data["processing_tier"] = ProcessingTier.LOCAL
    request_data["metadata"] = {"confidence": 0.9}
    
    request = ClassifiedRequest(**request_data)
    request_dict = request.to_dict()
    
    assert request_dict["processing_tier"] == "local"
    assert request_dict["metadata"]["confidence"] == 0.9

# CompanionResponse Tests
def test_companion_response_creation():
    """Test creating a CompanionResponse with valid data."""
    response = CompanionResponse(
        request_id="test_req_001",
        response_text="Platform 3 is to your right.",
        processing_tier=ProcessingTier.LOCAL
    )
    assert response.request_id == "test_req_001"
    assert response.response_text == "Platform 3 is to your right."
    assert response.processing_tier == ProcessingTier.LOCAL
    assert response.emotion == "neutral"  # default value
    assert response.confidence == 1.0  # default value
    assert isinstance(response.timestamp, datetime)

def test_companion_response_with_optional_fields():
    """Test creating a CompanionResponse with optional fields."""
    response = CompanionResponse(
        request_id="test_req_001",
        response_text="Platform 3 is to your right.",
        processing_tier=ProcessingTier.LOCAL,
        suggested_actions=["Look for signs", "Ask station staff"],
        learning_cues={"vocabulary": ["platform", "みぎ"]},
        emotion="happy",
        confidence=0.95,
        debug_info={"processing_time": 0.5}
    )
    assert len(response.suggested_actions) == 2
    assert response.learning_cues["vocabulary"] == ["platform", "みぎ"]
    assert response.emotion == "happy"
    assert response.confidence == 0.95
    assert response.debug_info["processing_time"] == 0.5

# ConversationContext Tests
def test_conversation_context_creation():
    """Test creating a ConversationContext with valid data."""
    context = ConversationContext(conversation_id="test_conv_001")
    assert context.conversation_id == "test_conv_001"
    assert len(context.request_history) == 0
    assert len(context.response_history) == 0
    assert isinstance(context.session_start, datetime)
    assert isinstance(context.last_updated, datetime)

def test_conversation_context_add_interaction(sample_request_data, sample_game_context):
    """Test adding an interaction to ConversationContext."""
    context = ConversationContext(conversation_id="test_conv_001")
    
    # Create request and response
    game_context = GameContext(**sample_game_context)
    request_data = sample_request_data.copy()
    request_data["game_context"] = game_context
    request = CompanionRequest(**request_data)
    
    response = CompanionResponse(
        request_id=request.request_id,
        response_text="Platform 3 is to your right.",
        processing_tier=ProcessingTier.LOCAL
    )
    
    # Add interaction
    original_update_time = context.last_updated
    context.add_interaction(request, response)
    
    assert len(context.request_history) == 1
    assert len(context.response_history) == 1
    assert context.request_history[0] == request
    assert context.response_history[0] == response
    assert context.last_updated > original_update_time

def test_conversation_context_multiple_interactions(sample_request_data, sample_game_context):
    """Test adding multiple interactions to ConversationContext."""
    context = ConversationContext(conversation_id="test_conv_001")
    
    # Create requests and responses
    game_context = GameContext(**sample_game_context)
    for i in range(3):
        request_data = sample_request_data.copy()
        request_data["request_id"] = f"test_req_{i}"
        request_data["game_context"] = game_context
        request = CompanionRequest(**request_data)
        
        response = CompanionResponse(
            request_id=request.request_id,
            response_text=f"Response {i}",
            processing_tier=ProcessingTier.LOCAL
        )
        
        context.add_interaction(request, response)
    
    assert len(context.request_history) == 3
    assert len(context.response_history) == 3
    assert [r.request_id for r in context.request_history] == [
        "test_req_0", "test_req_1", "test_req_2"
    ] 