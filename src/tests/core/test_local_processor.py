"""
Tests for local processor module.

This module contains unit tests for the LocalProcessor class.
"""

import pytest
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.ai.npc.core.models import (
    NPCRequest,
    GameContext,
    ProcessingTier,
    NPCProfileType
)
from src.ai.npc.local.local_processor import LocalProcessor
from src.ai.npc.local.ollama_client import OllamaClient, OllamaError
from src.ai.npc.core.conversation_manager import ConversationManager
from src.ai.npc.core.vector.knowledge_store import KnowledgeStore
from src.ai.npc.core.adapters import ConversationHistoryEntry, KnowledgeDocument

# Configure logging for tests
logging.basicConfig(level=logging.INFO)

@pytest.fixture
def mock_ollama_client():
    """Create a mock Ollama client for testing."""
    client = AsyncMock(spec=OllamaClient)
    client.generate = AsyncMock(return_value="<thinking>Test thinking</thinking>\n\nTest response")
    client.request_id = None
    return client

@pytest.fixture
def mock_conversation_manager():
    """Create a mock conversation manager for testing."""
    manager = AsyncMock()
    
    # Mock get_player_history to return a single conversation entry
    manager.get_player_history = AsyncMock(return_value=[
        ConversationHistoryEntry(
            user="Previous message",
            assistant="Previous response",
            timestamp=datetime.now().isoformat(),
            conversation_id="test_conversation"
        )
    ])
    
    # Mock add_to_history
    manager.add_to_history = AsyncMock()
    
    return manager

@pytest.fixture
def mock_knowledge_store():
    """Create a mock knowledge store for testing."""
    store = AsyncMock()
    
    # Mock collection
    store.collection = MagicMock()
    store.collection.count = MagicMock(return_value=10)
    
    # Mock contextual_search
    async def mock_search(request, standardized_format=False):
        # Return a simple mock knowledge item
        if standardized_format:
            return [
                KnowledgeDocument(
                    text="Test knowledge content",
                    id="test_doc_1",
                    metadata={
                        "source": "test_source",
                        "id": "test_id",
                        "relevance_score": 0.95
                    }
                )
            ]
        else:
            return [{"document": "Test knowledge content", "metadata": {"source": "test_source"}}]
    
    store.contextual_search = AsyncMock(side_effect=mock_search)
    
    return store

@pytest.fixture
def local_processor(mock_ollama_client, mock_conversation_manager, mock_knowledge_store):
    """Create a LocalProcessor instance for testing."""
    return LocalProcessor(
        ollama_client=mock_ollama_client,
        conversation_manager=mock_conversation_manager,
        knowledge_store=mock_knowledge_store
    )

@pytest.fixture
def test_request():
    """Create a test request for testing."""
    return NPCRequest(
        request_id="test_request",
        player_input="Hello",
        game_context=GameContext(
            player_id="test_player",
            npc_id=NPCProfileType.STATION_ATTENDANT,
            language_proficiency={"japanese": 0.5, "english": 1.0}
        ),
        processing_tier=ProcessingTier.LOCAL,
        additional_params={
            "conversation_id": "test_conversation"
        }
    )

@pytest.mark.asyncio
async def test_local_processor_initialization():
    """Test that LocalProcessor requires an OllamaClient."""
    with pytest.raises(TypeError):
        LocalProcessor()  # Should fail without ollama_client

@pytest.mark.asyncio
async def test_local_processor_process_request(local_processor, test_request, mock_ollama_client, mock_conversation_manager):
    """Test processing a request with the local processor."""
    # Process the request
    result = await local_processor.process(test_request)
    
    # Verify the result
    assert result is not None
    assert "response_text" in result
    assert "Test response" in result["response_text"]
    
    # Verify the Ollama client was called
    mock_ollama_client.generate.assert_called_once()
    
    # Verify conversation history was updated
    mock_conversation_manager.add_to_history.assert_called_once()
    call_args = mock_conversation_manager.add_to_history.call_args
    assert call_args.kwargs["conversation_id"] == "test_conversation"
    assert call_args.kwargs["user_query"] == "Hello"
    assert call_args.kwargs["response"] == result["response_text"]
    assert call_args.kwargs["player_id"] == "test_player"
    assert hasattr(call_args.kwargs["npc_id"], "value")  # Should be an enum
    assert call_args.kwargs["npc_id"].value == "station_attendant"  # With correct value

@pytest.mark.asyncio
async def test_local_processor_error_handling(local_processor, test_request, mock_ollama_client):
    """Test error handling in the local processor."""
    # Make the Ollama client raise an error
    mock_ollama_client.generate.side_effect = OllamaError("Test error")
    
    # Process the request
    result = await local_processor.process(test_request)
    
    # Verify we got a fallback response
    assert result is not None
    assert "response_text" in result
    assert "trouble" in result["response_text"].lower()
    assert result["is_fallback"] is True
    
    # Verify the client was called exactly once (no retries)
    mock_ollama_client.generate.assert_called_once()

@pytest.mark.asyncio
async def test_local_processor_with_history(local_processor, test_request, mock_ollama_client, mock_conversation_manager):
    """Test that the processor uses conversation history when available."""
    # Process the request
    result = await local_processor.process(test_request)
    
    # Verify the result
    assert result is not None
    assert "Test response" in result["response_text"]
    
    # Verify history was retrieved
    mock_conversation_manager.get_player_history.assert_called_once_with(
        test_request.game_context.player_id,
        standardized_format=True
    )
    
    # Verify the Ollama client was called with history
    mock_ollama_client.generate.assert_called_once()
    call_args = mock_ollama_client.generate.call_args[0][0]
    assert "Previous message" in call_args
    assert "Previous response" in call_args
    
    # Verify conversation history was updated
    mock_conversation_manager.add_to_history.assert_called_once()
    call_args = mock_conversation_manager.add_to_history.call_args
    assert call_args.kwargs["conversation_id"] == "test_conversation"
    assert call_args.kwargs["user_query"] == "Hello"
    assert call_args.kwargs["response"] == result["response_text"]
    assert call_args.kwargs["player_id"] == "test_player"
    assert hasattr(call_args.kwargs["npc_id"], "value")  # Should be an enum
    assert call_args.kwargs["npc_id"].value == "station_attendant"  # With correct value

@pytest.mark.asyncio
async def test_local_processor_without_conversation_manager(mock_ollama_client, mock_knowledge_store):
    """Test that processor works without a conversation manager."""
    # Create processor without conversation manager
    processor = LocalProcessor(
        ollama_client=mock_ollama_client,
        knowledge_store=mock_knowledge_store
    )
    
    # Create request without conversation_id
    request = NPCRequest(
        request_id="test_request",
        player_input="Hello",
        game_context=GameContext(
            player_id="test_player",
            language_proficiency={"japanese": 0.5, "english": 1.0}
        ),
        processing_tier=ProcessingTier.LOCAL
    )
    
    # Process the request
    result = await processor.process(request)
    
    # Verify the result
    assert result is not None
    assert "Test response" in result["response_text"]
    
    # Verify the Ollama client was called
    mock_ollama_client.generate.assert_called_once() 

@pytest.mark.asyncio
async def test_local_processor_history_in_prompt(local_processor, test_request, mock_ollama_client, mock_conversation_manager):
    """Test that conversation history is correctly included in the generated prompt."""
    # Create a test request with a conversation ID
    test_request.additional_params["conversation_id"] = "test_conversation"
    
    # Process the request
    result = await local_processor.process(test_request)
    
    # Verify conversation history was retrieved
    mock_conversation_manager.get_player_history.assert_called_once_with(
        test_request.game_context.player_id,
        standardized_format=True
    )
    
    # Verify the Ollama client was called
    mock_ollama_client.generate.assert_called_once()
    
    # Extract the prompt from the call to the Ollama client
    call_args = mock_ollama_client.generate.call_args[0][0]
    
    # Assert that the prompt contains conversation history
    assert "Previous conversation:" in call_args
    assert "Previous message" in call_args
    assert "Previous response" in call_args
    
    # Verify that debug info contains history count
    assert "debug_info" in result
    assert "history_count" in result["debug_info"]
    assert result["debug_info"]["history_count"] == 1
    
    # Verify conversation history was updated with the new exchange
    mock_conversation_manager.add_to_history.assert_called_once()
    call_args = mock_conversation_manager.add_to_history.call_args
    assert call_args.kwargs["conversation_id"] == "test_conversation"
    assert call_args.kwargs["user_query"] == "Hello"
    assert call_args.kwargs["response"] == result["response_text"]
    assert call_args.kwargs["player_id"] == "test_player"
    assert hasattr(call_args.kwargs["npc_id"], "value")  # Should be an enum
    assert call_args.kwargs["npc_id"].value == "station_attendant"  # With correct value

@pytest.mark.asyncio
async def test_local_processor_multiple_history_exchanges(local_processor, test_request, mock_ollama_client, mock_conversation_manager):
    """Test that multiple conversation exchanges are correctly maintained in history."""
    # Update the mock to return multiple history entries in reverse chronological order
    mock_conversation_manager.get_player_history.return_value = [
        ConversationHistoryEntry(
            user="Second message",
            assistant="Second response",
            timestamp=datetime.now().isoformat(),
            conversation_id="test_conversation"
        ),
        ConversationHistoryEntry(
            user="First message",
            assistant="First response",
            timestamp=datetime.now().isoformat(),
            conversation_id="test_conversation"
        )
    ]
    
    # Set the conversation ID
    test_request.additional_params["conversation_id"] = "test_conversation"
    
    # Process the request
    result = await local_processor.process(test_request)
    
    # Verify conversation history was retrieved
    mock_conversation_manager.get_player_history.assert_called_once()
    
    # Extract the prompt from the call to the Ollama client
    call_args = mock_ollama_client.generate.call_args[0][0]
    
    # Assert that the prompt contains both conversation entries
    assert "Previous conversation:" in call_args
    assert "First message" in call_args
    assert "First response" in call_args
    assert "Second message" in call_args
    assert "Second response" in call_args
    
    # Verify that debug info contains correct history count
    assert result["debug_info"]["history_count"] == 2
    
    # Verify conversation history was updated with the new exchange
    mock_conversation_manager.add_to_history.assert_called_once()
    call_args = mock_conversation_manager.add_to_history.call_args
    assert call_args.kwargs["conversation_id"] == "test_conversation"
    assert call_args.kwargs["user_query"] == "Hello"
    assert call_args.kwargs["response"] == result["response_text"]
    assert call_args.kwargs["player_id"] == "test_player"
    assert hasattr(call_args.kwargs["npc_id"], "value")  # Should be an enum
    assert call_args.kwargs["npc_id"].value == "station_attendant"  # With correct value

@pytest.mark.asyncio
async def test_local_processor_multiple_conversations(
    local_processor, 
    test_request, 
    mock_ollama_client, 
    mock_conversation_manager
):
    """Test that different conversations for the same player with different NPCs are handled correctly."""
    # First conversation with NPC1
    test_request.additional_params["conversation_id"] = "conversation_with_npc1"
    test_request.game_context.npc_id = NPCProfileType.STATION_ATTENDANT
    
    # Mock the conversation history for NPC1
    mock_conversation_manager.get_player_history.return_value = [
        ConversationHistoryEntry(
            user="Message for NPC1",
            assistant="Response from NPC1",
            timestamp=datetime.now().isoformat(),
            conversation_id="conversation_with_npc1"
        )
    ]
    
    # Process first request
    await local_processor.process(test_request)
    
    # Verify the correct history was retrieved and used for NPC1
    call_args_npc1 = mock_ollama_client.generate.call_args[0][0]
    assert "Message for NPC1" in call_args_npc1
    assert "Response from NPC1" in call_args_npc1
    
    # Reset the mocks
    mock_ollama_client.generate.reset_mock()
    mock_conversation_manager.get_player_history.reset_mock()
    
    # Second conversation with NPC2
    test_request.additional_params["conversation_id"] = "conversation_with_npc2"
    test_request.game_context.npc_id = NPCProfileType.COMPANION_DOG
    
    # Mock the conversation history for NPC2
    mock_conversation_manager.get_player_history.return_value = [
        ConversationHistoryEntry(
            user="Message for NPC2",
            assistant="Response from NPC2",
            timestamp=datetime.now().isoformat(),
            conversation_id="conversation_with_npc2"
        )
    ]
    
    # Process second request
    await local_processor.process(test_request)
    
    # Verify the correct history was retrieved and used for NPC2
    call_args_npc2 = mock_ollama_client.generate.call_args[0][0]
    assert "Message for NPC2" in call_args_npc2
    assert "Response from NPC2" in call_args_npc2
    
    # Verify NPC1's conversation is not in NPC2's prompt
    assert "Message for NPC1" not in call_args_npc2
    assert "Response from NPC1" not in call_args_npc2

@pytest.mark.asyncio
async def test_local_processor_empty_history(
    local_processor, 
    test_request, 
    mock_ollama_client, 
    mock_conversation_manager
):
    """Test that the processor correctly handles empty conversation history."""
    # Set the conversation ID but return empty history
    test_request.additional_params["conversation_id"] = "test_conversation"
    mock_conversation_manager.get_player_history.return_value = []
    
    # Process the request
    result = await local_processor.process(test_request)
    
    # Verify conversation history was retrieved but was empty
    mock_conversation_manager.get_player_history.assert_called_once()
    
    # Extract the prompt from the call to the Ollama client
    call_args = mock_ollama_client.generate.call_args[0][0]
    
    # Assert that the prompt doesn't contain conversation history section
    assert "Previous conversation:" not in call_args
    
    # Verify that debug info shows zero history entries
    assert result["debug_info"]["history_count"] == 0
    
    # Verify conversation history was updated with the new exchange (first entry)
    mock_conversation_manager.add_to_history.assert_called_once()
    call_args = mock_conversation_manager.add_to_history.call_args
    assert call_args.kwargs["conversation_id"] == "test_conversation"
    assert call_args.kwargs["user_query"] == "Hello"
    assert call_args.kwargs["response"] == result["response_text"]
    assert call_args.kwargs["player_id"] == "test_player"
    assert hasattr(call_args.kwargs["npc_id"], "value")  # Should be an enum
    assert call_args.kwargs["npc_id"].value == "station_attendant"  # With correct value

@pytest.mark.asyncio
async def test_local_processor_long_history(
    local_processor, 
    test_request, 
    mock_ollama_client, 
    mock_conversation_manager
):
    """Test that the processor correctly handles long conversation history."""
    # Create a long history with 20 entries
    long_history = []
    for i in range(20):
        long_history.append(
            ConversationHistoryEntry(
                user=f"Message {i}",
                assistant=f"Response {i}",
                timestamp=datetime.now().isoformat(),
                conversation_id="test_conversation"
            )
        )
    
    mock_conversation_manager.get_player_history.return_value = long_history
    test_request.additional_params["conversation_id"] = "test_conversation"
    
    # Process the request
    result = await local_processor.process(test_request)
    
    # Verify history was retrieved
    mock_conversation_manager.get_player_history.assert_called_once()
    
    # Extract the prompt
    call_args = mock_ollama_client.generate.call_args[0][0]
    
    # The prompt should contain history, but might be truncated by the prompt optimizer
    assert "Previous conversation:" in call_args
    
    # Verify debug info contains correct history count
    assert result["debug_info"]["history_count"] == 20
    
    # History optimization should keep more recent conversations, check for the most recent ones
    assert "Message 19" in call_args
    assert "Response 19" in call_args
    
    # Verify conversation history was updated with the new exchange
    mock_conversation_manager.add_to_history.assert_called_once()
    call_args = mock_conversation_manager.add_to_history.call_args
    assert call_args.kwargs["conversation_id"] == "test_conversation"
    assert call_args.kwargs["user_query"] == "Hello"
    assert call_args.kwargs["response"] == result["response_text"]
    assert call_args.kwargs["player_id"] == "test_player"
    assert hasattr(call_args.kwargs["npc_id"], "value")  # Should be an enum
    assert call_args.kwargs["npc_id"].value == "station_attendant"  # With correct value

@pytest.mark.asyncio
async def test_local_processor_close(local_processor, mock_ollama_client):
    """Test that the close method properly closes the Ollama client."""
    # Setup the close method as an AsyncMock
    mock_ollama_client.close = AsyncMock()
    
    # Call the close method
    await local_processor.close()
    
    # Verify that the Ollama client's close method was called exactly once
    mock_ollama_client.close.assert_called_once() 