"""
Tests for the Context Manager

This module contains tests for the ContextManager class and related components.
Following our testing guidelines, each test is isolated and uses no shared resources.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from src.ai.npc.core.context_manager import (
    ContextManager,
    ConversationContext,
    ContextEntry
)
from src.ai.npc.core.models import (
    ClassifiedRequest,
    GameContext,
    ProcessingTier
)

# Test Data Fixtures
@pytest.fixture
def sample_game_context() -> GameContext:
    """Create a sample game context for testing."""
    return GameContext(
        player_id="test_player",
        language_proficiency={"JLPT": 5, "speaking": 0.3, "listening": 0.4}
    )

@pytest.fixture
def sample_request(sample_game_context) -> ClassifiedRequest:
    """Create a sample classified request for testing."""
    return ClassifiedRequest(
        request_id="test_req_001",
        player_input="Where is the ticket gate?",
        game_context=sample_game_context,
        processing_tier=ProcessingTier.LOCAL
    )

@pytest.fixture
def sample_response() -> str:
    """Create a sample response for testing."""
    return "The ticket gate is straight ahead. 改札口はまっすぐです。(kaisatsuguchi wa massugu desu)"

@pytest.fixture
def context_manager() -> ContextManager:
    """Create a fresh context manager for testing."""
    return ContextManager()

# Basic Functionality Tests
def test_context_manager_creation():
    """Test creating a context manager."""
    manager = ContextManager()
    assert manager is not None
    assert isinstance(manager.contexts, dict)
    assert len(manager.contexts) == 0

def test_create_context(context_manager):
    """Test creating a new conversation context."""
    context = context_manager.create_context(
        player_id="test_player",
        player_language_level="N5",
        current_location="tokyo_station"
    )
    
    assert context is not None
    assert context.player_id == "test_player"
    assert context.player_language_level == "N5"
    assert context.current_location == "tokyo_station"
    assert context.conversation_id in context_manager.contexts

def test_get_context(context_manager):
    """Test retrieving a conversation context."""
    # Create a context first
    context = context_manager.create_context(player_id="test_player")
    
    # Retrieve it
    retrieved = context_manager.get_context(context.conversation_id)
    assert retrieved is not None
    assert retrieved.conversation_id == context.conversation_id
    assert retrieved.player_id == "test_player"

def test_update_context(context_manager, sample_request, sample_response):
    """Test updating a conversation context."""
    # Create a context
    context = context_manager.create_context(player_id="test_player")
    original_update_time = context.updated_at
    
    # Update it
    updated = context_manager.update_context(
        context.conversation_id,
        sample_request,
        sample_response
    )
    
    assert updated is not None
    assert len(updated.entries) == 1
    assert updated.updated_at > original_update_time
    assert updated.entries[0].player_input == sample_request.player_input
    assert updated.entries[0].response == sample_response

def test_delete_context(context_manager):
    """Test deleting a conversation context."""
    # Create a context
    context = context_manager.create_context(player_id="test_player")
    
    # Delete it
    result = context_manager.delete_context(context.conversation_id)
    assert result is True
    assert context.conversation_id not in context_manager.contexts

def test_get_or_create_context(context_manager):
    """Test get_or_create_context functionality."""
    # First call should create
    context1 = context_manager.get_or_create_context(
        player_id="test_player",
        player_language_level="N5"
    )
    assert context1 is not None
    
    # Second call with same ID should return existing
    context2 = context_manager.get_or_create_context(
        conversation_id=context1.conversation_id
    )
    assert context2 is context1
    
    # Call without ID should create new
    context3 = context_manager.get_or_create_context(
        player_id="test_player",
        player_language_level="N5"
    )
    assert context3 is not context1

# Edge Cases and Error Handling
def test_get_nonexistent_context(context_manager):
    """Test getting a context that doesn't exist."""
    context = context_manager.get_context("nonexistent-id")
    assert context is None

def test_update_nonexistent_context(context_manager, sample_request, sample_response):
    """Test updating a context that doesn't exist."""
    result = context_manager.update_context(
        "nonexistent-id",
        sample_request,
        sample_response
    )
    assert result is None

def test_delete_nonexistent_context(context_manager):
    """Test deleting a context that doesn't exist."""
    result = context_manager.delete_context("nonexistent-id")
    assert result is False

def test_create_context_without_player_id(context_manager):
    """Test creating a context without a player ID."""
    context = context_manager.create_context()
    assert context is not None
    assert context.player_id is None
    assert context.player_language_level == "N5"  # Default value

# State Management Tests
def test_context_timestamps(context_manager, sample_request, sample_response):
    """Test that timestamps are properly managed."""
    # Create context
    context = context_manager.create_context()
    creation_time = context.created_at
    
    # Wait a tiny bit
    import time
    time.sleep(0.001)
    
    # Update context
    context = context_manager.update_context(
        context.conversation_id,
        sample_request,
        sample_response
    )
    
    assert context.created_at == creation_time
    assert context.updated_at > creation_time
    assert context.entries[0].timestamp >= creation_time

def test_multiple_updates(context_manager, sample_request, sample_response):
    """Test multiple updates to the same context."""
    context = context_manager.create_context()
    
    # Add three entries
    for i in range(3):
        modified_request = ClassifiedRequest(
            request_id=f"req_{i}",
            player_input=f"Input {i}",
            game_context=sample_request.game_context,
            processing_tier=ProcessingTier.LOCAL
        )
        context = context_manager.update_context(
            context.conversation_id,
            modified_request,
            f"Response {i}"
        )
    
    assert len(context.entries) == 3
    assert [e.player_input for e in context.entries] == [
        "Input 0", "Input 1", "Input 2"
    ]
    assert [e.response for e in context.entries] == [
        "Response 0", "Response 1", "Response 2"
    ]

def test_context_entry_serialization(context_manager, sample_request, sample_response):
    """Test that context entries can be properly serialized and deserialized."""
    # Create and update context
    context = context_manager.create_context(
        player_id="test_player",
        player_language_level="N5",
        current_location="tokyo_station"
    )
    context = context_manager.update_context(
        context.conversation_id,
        sample_request,
        sample_response
    )
    
    # Convert to dict
    context_dict = context.to_dict()
    
    # Create new context from dict
    new_context = ConversationContext(
        conversation_id=context_dict["conversation_id"],
        player_id=context_dict["player_id"],
        player_language_level=context_dict["player_language_level"],
        current_location=context_dict["current_location"],
        created_at=datetime.fromisoformat(context_dict["created_at"]),
        updated_at=datetime.fromisoformat(context_dict["updated_at"])
    )
    
    # Add entries
    for entry_data in context_dict["entries"]:
        entry = ContextEntry(
            player_input=entry_data["player_input"],
            response=entry_data["response"],
            game_context=GameContext(**entry_data["game_context"]),
            timestamp=datetime.fromisoformat(entry_data["timestamp"])
        )
        new_context.add_entry(entry)
    
    # Verify all data is preserved
    assert new_context.conversation_id == context.conversation_id
    assert new_context.player_id == context.player_id
    assert new_context.player_language_level == context.player_language_level
    assert len(new_context.entries) == len(context.entries)
    assert new_context.entries[0].player_input == context.entries[0].player_input
    assert new_context.entries[0].response == context.entries[0].response
    assert new_context.entries[0].game_context.player_id == context.entries[0].game_context.player_id
    assert new_context.entries[0].game_context.language_proficiency == context.entries[0].game_context.language_proficiency 