"""
Tests for the ConversationManager class.

This module tests the conversation history management functionality.
"""

import os
import json
import pytest
from datetime import datetime
from typing import Dict, Any

from src.ai.npc.core.conversation_manager import ConversationManager

@pytest.fixture
def temp_storage_dir(tmp_path):
    """Create a temporary directory for storing conversation histories."""
    storage_dir = tmp_path / "test_conversations"
    storage_dir.mkdir()
    return str(storage_dir)

@pytest.fixture
def conversation_manager(temp_storage_dir):
    """Create a ConversationManager instance with a temporary storage directory."""
    return ConversationManager(storage_dir=temp_storage_dir)

def test_conversation_manager_creation(temp_storage_dir):
    """Test creating a conversation manager."""
    manager = ConversationManager(storage_dir=temp_storage_dir)
    assert manager is not None
    assert manager.storage_dir == temp_storage_dir
    assert os.path.exists(temp_storage_dir)

def test_get_player_history_empty(conversation_manager):
    """Test getting history for a player with no previous conversations."""
    history = conversation_manager.get_player_history("test_player")
    assert isinstance(history, list)
    assert len(history) == 0

def test_add_to_history(conversation_manager):
    """Test adding a conversation entry to history."""
    conversation_manager.add_to_history(
        conversation_id="test_conv_1",
        user_query="Hello",
        response="Hi there!",
        npc_id="test_npc",
        player_id="test_player"
    )
    
    # Get history and verify entry
    history = conversation_manager.get_player_history("test_player")
    assert len(history) == 1
    entry = history[0]
    assert entry["user_query"] == "Hello"
    assert entry["response"] == "Hi there!"
    assert entry["npc_id"] == "test_npc"
    assert entry["player_id"] == "test_player"
    assert "timestamp" in entry

def test_add_multiple_entries(conversation_manager):
    """Test adding multiple entries to history."""
    # Add three entries
    for i in range(3):
        conversation_manager.add_to_history(
            conversation_id="test_conv_1",
            user_query=f"Query {i}",
            response=f"Response {i}",
            npc_id="test_npc",
            player_id="test_player"
        )
    
    # Get history and verify entries
    history = conversation_manager.get_player_history("test_player")
    assert len(history) == 3
    for i, entry in enumerate(reversed(history)):  # Reversed because newest are first
        assert entry["user_query"] == f"Query {i}"
        assert entry["response"] == f"Response {i}"

def test_history_persistence(temp_storage_dir):
    """Test that history is persisted to disk and can be loaded by a new manager."""
    # Create first manager and add entries
    manager1 = ConversationManager(storage_dir=temp_storage_dir)
    manager1.add_to_history(
        conversation_id="test_conv_1",
        user_query="Hello",
        response="Hi there!",
        npc_id="test_npc",
        player_id="test_player"
    )
    
    # Create second manager and verify it loads the history
    manager2 = ConversationManager(storage_dir=temp_storage_dir)
    history = manager2.get_player_history("test_player")
    assert len(history) == 1
    assert history[0]["user_query"] == "Hello"
    assert history[0]["response"] == "Hi there!"
    assert history[0]["player_id"] == "test_player"

def test_max_entries_limit(conversation_manager):
    """Test that get_player_history respects the max_entries limit."""
    # Add 5 entries
    for i in range(5):
        conversation_manager.add_to_history(
            conversation_id="test_conv_1",
            user_query=f"Query {i}",
            response=f"Response {i}",
            npc_id="test_npc",
            player_id="test_player"
        )
    
    # Get history with limit of 3
    history = conversation_manager.get_player_history("test_player", max_entries=3)
    assert len(history) == 3
    # Should get the most recent entries
    for i, entry in enumerate(reversed(history)):  # Reversed because newest are first
        expected_idx = i + 2  # Should get entries 2, 3, 4
        assert entry["user_query"] == f"Query {expected_idx}"
        assert entry["response"] == f"Response {expected_idx}"

def test_metadata_handling(conversation_manager):
    """Test handling of optional metadata in conversation entries."""
    metadata = {
        "language_level": "N5",
        "location": "tokyo_station"
    }
    
    conversation_manager.add_to_history(
        conversation_id="test_conv_1",
        user_query="Hello",
        response="Hi there!",
        npc_id="test_npc",
        player_id="test_player",
        metadata=metadata
    )
    
    history = conversation_manager.get_player_history("test_player")
    assert len(history) == 1
    entry = history[0]
    assert entry["metadata"] == metadata

def test_error_handling_corrupted_file(temp_storage_dir):
    """Test handling of corrupted history files."""
    # Create a corrupted JSON file
    file_path = os.path.join(temp_storage_dir, "corrupted_conv.json")
    with open(file_path, 'w') as f:
        f.write("{ invalid json")
    
    manager = ConversationManager(storage_dir=temp_storage_dir)
    history = manager.get_player_history("test_player")
    assert isinstance(history, list)
    assert len(history) == 0

def test_multiple_conversations_per_player(conversation_manager):
    """Test that a player can have multiple conversations."""
    # Add entries in different conversations
    for conv_id in ["conv1", "conv2", "conv3"]:
        conversation_manager.add_to_history(
            conversation_id=conv_id,
            user_query=f"Hello from {conv_id}",
            response=f"Hi {conv_id}!",
            npc_id="test_npc",
            player_id="test_player"
        )
    
    # Get history and verify all entries are returned
    history = conversation_manager.get_player_history("test_player")
    assert len(history) == 3
    # Entries should be in reverse chronological order
    for i, entry in enumerate(history):
        conv_id = f"conv{3-i}"  # conv3, conv2, conv1
        assert entry["user_query"] == f"Hello from {conv_id}"
        assert entry["response"] == f"Hi {conv_id}!"

def test_multiple_players(conversation_manager):
    """Test handling conversations from multiple players."""
    # Add entries for different players
    for player_id in ["player1", "player2", "player3"]:
        conversation_manager.add_to_history(
            conversation_id=f"conv_{player_id}",
            user_query=f"Hello from {player_id}",
            response=f"Hi {player_id}!",
            npc_id="test_npc",
            player_id=player_id
        )
    
    # Verify each player's history is separate
    for player_id in ["player1", "player2", "player3"]:
        history = conversation_manager.get_player_history(player_id)
        assert len(history) == 1
        assert history[0]["user_query"] == f"Hello from {player_id}"
        assert history[0]["response"] == f"Hi {player_id}!"
        assert history[0]["player_id"] == player_id 