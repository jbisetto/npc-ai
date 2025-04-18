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

@pytest.mark.asyncio
async def test_get_player_history_empty(conversation_manager):
    """Test getting history for a player with no previous conversations."""
    history = await conversation_manager.get_player_history("test_player")
    assert isinstance(history, list)
    assert len(history) == 0

@pytest.mark.asyncio
async def test_add_to_history(conversation_manager):
    """Test adding a conversation entry to history."""
    await conversation_manager.add_to_history(
        conversation_id="test_conv_1",
        user_query="Hello",
        response="Hi there!",
        npc_id="test_npc",
        player_id="test_player"
    )
    
    # Get history and verify entry
    history = await conversation_manager.get_player_history("test_player")
    assert len(history) == 1
    entry = history[0]
    assert entry.user == "Hello"
    assert entry.assistant == "Hi there!"
    
    # Check that entry has metadata and timestamp
    assert hasattr(entry, "metadata")
    assert hasattr(entry, "timestamp")
    
    # Check that we have the right conversation ID
    assert entry.conversation_id == "test_conv_1"

@pytest.mark.asyncio
async def test_add_multiple_entries(conversation_manager):
    """Test adding multiple entries to history."""
    # Add three entries
    for i in range(3):
        await conversation_manager.add_to_history(
            conversation_id="test_conv_1",
            user_query=f"Query {i}",
            response=f"Response {i}",
            npc_id="test_npc",
            player_id="test_player"
        )
    
    # Get history and verify entries
    history = await conversation_manager.get_player_history("test_player")
    assert len(history) == 3
    for i, entry in enumerate(reversed(history)):  # Reversed because newest are first
        assert entry.user == f"Query {i}"
        assert entry.assistant == f"Response {i}"

@pytest.mark.asyncio
async def test_history_persistence(temp_storage_dir):
    """Test that history is persisted to disk and can be loaded by a new manager."""
    # Create first manager and add entries
    manager1 = ConversationManager(storage_dir=temp_storage_dir)
    await manager1.add_to_history(
        conversation_id="test_conv_1",
        user_query="Hello",
        response="Hi there!",
        npc_id="test_npc",
        player_id="test_player"
    )
    
    # Create second manager and verify it loads the history
    manager2 = ConversationManager(storage_dir=temp_storage_dir)
    history = await manager2.get_player_history("test_player")
    assert len(history) == 1
    assert history[0].user == "Hello"
    assert history[0].assistant == "Hi there!"
    assert history[0].conversation_id == "test_conv_1"

@pytest.mark.asyncio
async def test_max_entries_limit(conversation_manager):
    """Test that get_player_history respects the max_entries limit."""
    # Add 5 entries
    for i in range(5):
        await conversation_manager.add_to_history(
            conversation_id="test_conv_1",
            user_query=f"Query {i}",
            response=f"Response {i}",
            npc_id="test_npc",
            player_id="test_player"
        )
    
    # Get history with limit of 3
    history = await conversation_manager.get_player_history("test_player", max_entries=3)
    assert len(history) == 3
    # Should get the most recent entries
    for i, entry in enumerate(reversed(history)):  # Reversed because newest are first
        expected_idx = i + 2  # Should get entries 2, 3, 4
        assert entry.user == f"Query {expected_idx}"
        assert entry.assistant == f"Response {expected_idx}"

@pytest.mark.asyncio
async def test_metadata_handling(conversation_manager):
    """Test handling of optional metadata in conversation entries."""
    metadata = {
        "language_level": "N5",
        "location": "tokyo_station"
    }
    
    await conversation_manager.add_to_history(
        conversation_id="test_conv_1",
        user_query="Hello",
        response="Hi there!",
        npc_id="test_npc",
        player_id="test_player",
        metadata=metadata
    )
    
    history = await conversation_manager.get_player_history("test_player")
    assert len(history) == 1
    entry = history[0]
    assert "language_level" in entry.metadata
    assert entry.metadata["language_level"] == "N5"

@pytest.mark.asyncio
async def test_error_handling_corrupted_file(temp_storage_dir):
    """Test handling of corrupted history files."""
    # Create a corrupted JSON file
    file_path = os.path.join(temp_storage_dir, "corrupted_player.json")
    with open(file_path, 'w') as f:
        f.write("{ invalid json")
    
    manager = ConversationManager(storage_dir=temp_storage_dir)
    history = await manager.get_player_history("corrupted_player")
    assert isinstance(history, list)
    assert len(history) == 0

@pytest.mark.asyncio
async def test_multiple_conversations_per_player(conversation_manager):
    """Test that a player can have multiple conversations."""
    # Add entries in different conversations
    for conv_id in ["conv1", "conv2", "conv3"]:
        await conversation_manager.add_to_history(
            conversation_id=conv_id,
            user_query=f"Hello from {conv_id}",
            response=f"Hi {conv_id}!",
            npc_id="test_npc",
            player_id="test_player"
        )
    
    # Get history and verify all entries are returned
    history = await conversation_manager.get_player_history("test_player")
    assert len(history) == 3
    # Entries should be in reverse chronological order
    conv_ids = []
    for entry in history:
        # Extract conversation_id from entry
        conv_ids.append(entry.conversation_id)
        
    # Check that all conversation IDs are present
    assert "conv1" in conv_ids
    assert "conv2" in conv_ids
    assert "conv3" in conv_ids

@pytest.mark.asyncio
async def test_multiple_players(conversation_manager):
    """Test handling conversations from multiple players."""
    # Add entries for different players
    for player_id in ["player1", "player2", "player3"]:
        await conversation_manager.add_to_history(
            conversation_id=f"conv_{player_id}",
            user_query=f"Hello from {player_id}",
            response=f"Hi {player_id}!",
            npc_id="test_npc",
            player_id=player_id
        )
    
    # Verify each player's history is separate
    for player_id in ["player1", "player2", "player3"]:
        history = await conversation_manager.get_player_history(player_id)
        assert len(history) == 1
        assert history[0].user == f"Hello from {player_id}"
        assert history[0].assistant == f"Hi {player_id}!"
        assert history[0].conversation_id == f"conv_{player_id}"

@pytest.mark.asyncio
async def test_get_history_by_npc_id(conversation_manager):
    """Test filtering conversation history by NPC ID."""
    # Add entries for different NPCs
    for npc_id in ["npc1", "npc2", "npc3"]:
        for i in range(2):  # 2 entries per NPC
            await conversation_manager.add_to_history(
                conversation_id=f"conv_{npc_id}_{i}",
                user_query=f"Hello {npc_id} - {i}",
                response=f"Hi from {npc_id} - {i}!",
                npc_id=npc_id,
                player_id="test_player"
            )
    
    # Verify we can filter by NPC ID
    for npc_id in ["npc1", "npc2", "npc3"]:
        history = await conversation_manager.get_player_history(
            player_id="test_player", 
            npc_id=npc_id
        )
        assert len(history) == 2
        for entry in history:
            assert f"Hello {npc_id}" in entry.user
            assert f"Hi from {npc_id}" in entry.assistant
    
    # Also test with an enum-like object that has a 'value' attribute
    class MockEnum:
        def __init__(self, value):
            self.value = value
    
    # Test with a mock enum
    mock_enum = MockEnum("npc2")
    history = await conversation_manager.get_player_history(
        player_id="test_player", 
        npc_id=mock_enum
    )
    assert len(history) == 2
    for entry in history:
        assert "Hello npc2" in entry.user
        assert "Hi from npc2" in entry.assistant 