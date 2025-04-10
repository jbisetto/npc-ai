"""
Tests for the core data models.

This module contains tests for all the data models defined in src.ai.npc.core.models.
Following our testing guidelines, each test is isolated and uses no shared resources.
"""

import pytest
from datetime import datetime

from src.ai.npc.core.models import (
    ProcessingTier,
    GameContext,
    CompanionRequest,
    ClassifiedRequest,
    CompanionResponse,
    ConversationContext,
    NPCProfileType
)
from src.tests.utils.factories import (
    create_test_request,
    create_test_game_context,
    create_test_response
)


# ProcessingTier Tests
def test_processing_tier_values():
    """Test ProcessingTier enum values."""
    assert ProcessingTier.LOCAL.value == "local"
    assert ProcessingTier.HOSTED.value == "hosted"
    assert len(ProcessingTier) == 2


# GameContext Tests
def test_game_context_creation():
    """Test creating a GameContext with valid data."""
    context = create_test_game_context(
        player_id="test_player",
        language_proficiency={"reading": 0.5, "speaking": 0.3},
        conversation_history=[]
    )
    assert context.player_id == "test_player"
    assert context.language_proficiency["reading"] == 0.5
    assert context.language_proficiency["speaking"] == 0.3
    assert context.conversation_history == []


def test_game_context_optional_fields():
    """Test GameContext with only required fields."""
    minimal_context = create_test_game_context(
        player_id="test_player",
        language_proficiency={"reading": 0.5}
    )
    assert minimal_context.conversation_history is None


def test_game_context_to_dict():
    """Test GameContext to_dict method."""
    context = create_test_game_context(
        player_id="test_player",
        language_proficiency={"reading": 0.5, "speaking": 0.3},
        conversation_history=[]
    )
    context_dict = context.to_dict()
    assert context_dict["player_id"] == "test_player"
    assert context_dict["language_proficiency"]["reading"] == 0.5
    assert context_dict["language_proficiency"]["speaking"] == 0.3
    assert context_dict["conversation_history"] == []


# CompanionRequest Tests
def test_companion_request_creation():
    """Test creating a CompanionRequest with valid data."""
    game_context = create_test_game_context(conversation_history=[])
    request = create_test_request(
        request_id="test_req_001",
        player_input="Where is platform 3?",
        game_context=game_context
    )
    
    assert request.request_id == "test_req_001"
    assert request.player_input == "Where is platform 3?"
    assert isinstance(request.game_context, GameContext)


def test_companion_request_without_context():
    """Test creating a CompanionRequest without game context."""
    request = CompanionRequest(
        request_id="test_req_001",
        player_input="Where is platform 3?"
    )
    assert request.game_context is None


def test_companion_request_to_dict():
    """Test CompanionRequest to_dict method."""
    game_context = create_test_game_context(conversation_history=[])
    request = create_test_request(
        request_id="test_req_001",
        player_input="Where is platform 3?",
        game_context=game_context
    )
    
    request_dict = request.to_dict()
    assert request_dict["request_id"] == "test_req_001"
    assert request_dict["player_input"] == "Where is platform 3?"
    assert request_dict["game_context"] == game_context.to_dict()


# NPCRequest Tests
def test_npc_request_creation():
    """Test creating a NPCRequest with valid data."""
    game_context = create_test_game_context(conversation_history=[])
    request = create_test_request(
        request_id="test_req_001",
        player_input="Where is platform 3?",
        game_context=game_context,
        processing_tier=ProcessingTier.LOCAL
    )
    assert request.processing_tier == ProcessingTier.LOCAL


def test_npc_request_to_dict():
    """Test NPCRequest to_dict method."""
    game_context = create_test_game_context(conversation_history=[])
    request = create_test_request(
        request_id="test_req_001",
        player_input="Where is platform 3?",
        game_context=game_context,
        processing_tier=ProcessingTier.LOCAL
    )
    
    request_dict = request.to_dict()
    assert request_dict["processing_tier"] == "local"
    assert "game_context" in request_dict
    assert request_dict["request_id"] == "test_req_001"
    assert request_dict["player_input"] == "Where is platform 3?"


# CompanionResponse Tests
def test_companion_response_creation():
    """Test creating a CompanionResponse with valid data."""
    response = create_test_response(
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
    response = create_test_response(
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


def test_conversation_context_add_interaction():
    """Test adding an interaction to ConversationContext."""
    context = ConversationContext(conversation_id="test_conv_001")
    
    # Create request and response
    game_context = create_test_game_context(conversation_history=[])
    request = create_test_request(
        request_id="test_req_001",
        player_input="Where is platform 3?",
        game_context=game_context
    )
    
    response = create_test_response(
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


def test_conversation_context_multiple_interactions():
    """Test adding multiple interactions to ConversationContext."""
    context = ConversationContext(conversation_id="test_conv_001")
    game_context = create_test_game_context(conversation_history=[])
    
    # Add multiple interactions
    for i in range(3):
        request = create_test_request(
            request_id=f"test_req_{i}",
            player_input=f"Question {i}",
            game_context=game_context
        )
        response = create_test_response(
            request_id=request.request_id,
            response_text=f"Answer {i}",
            processing_tier=ProcessingTier.LOCAL
        )
        context.add_interaction(request, response)
    
    assert len(context.request_history) == 3
    assert len(context.response_history) == 3
    assert context.request_history[0].player_input == "Question 0"
    assert context.response_history[2].response_text == "Answer 2"


# NPCProfileType Tests
def test_npc_profile_type_enum():
    """Test NPCProfileType enum values."""
    # Test enum values
    assert NPCProfileType.STATION_ATTENDANT.value == "station_attendant"
    assert NPCProfileType.STATION_ATTENDANT_KYOTO.value == "station_attendant_kyoto"
    assert NPCProfileType.STATION_ATTENDANT_ODAWARA.value == "station_attendant_odawara"
    assert NPCProfileType.INFORMATION_BOOTH_ATTENDANT.value == "information_booth_attendant"
    assert NPCProfileType.TICKET_BOOTH_ATTENDANT.value == "ticket_booth_attendant"
    assert NPCProfileType.COMPANION_DOG.value == "companion_dog"


def test_npc_profile_type_from_string():
    """Test NPCProfileType.from_string method."""
    # Test valid profile IDs
    assert NPCProfileType.from_string("station_attendant") == NPCProfileType.STATION_ATTENDANT
    assert NPCProfileType.from_string("companion_dog") == NPCProfileType.COMPANION_DOG
    
    # Test invalid profile ID
    assert NPCProfileType.from_string("nonexistent_profile") is None


def test_game_context_with_npc_profile_type():
    """Test creating GameContext with NPCProfileType."""
    # Create with enum
    context1 = GameContext(
        player_id="test1",
        language_proficiency={"english": 1.0},
        npc_id=NPCProfileType.STATION_ATTENDANT
    )
    assert context1.npc_id == NPCProfileType.STATION_ATTENDANT
    
    # Test to_dict conversion
    context_dict = context1.to_dict()
    assert context_dict["npc_id"] == "station_attendant"
    
    # Create with string
    context2 = GameContext(
        player_id="test2",
        language_proficiency={"english": 1.0},
        npc_id="station_attendant"
    )
    assert isinstance(context2.npc_id, str)
    assert context2.npc_id == "station_attendant" 