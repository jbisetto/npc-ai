"""
Tests for the local processor implementation.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from src.ai.npc.core.models import (
    ClassifiedRequest,
    GameContext,
    ProcessingTier
)
from src.ai.npc.local.local_processor import LocalProcessor
from src.ai.npc.local.ollama_client import OllamaClient, OllamaError
from src.ai.npc.core.conversation_manager import ConversationManager

@pytest.fixture
def mock_ollama_client():
    """Create a mock Ollama client."""
    client = Mock(spec=OllamaClient)
    client.generate = AsyncMock(return_value="Test response")
    return client

@pytest.fixture
def mock_conversation_manager():
    """Create a mock conversation manager."""
    manager = Mock(spec=ConversationManager)
    manager.get_player_history = AsyncMock(return_value=[
        {"role": "user", "content": "Previous message"},
        {"role": "assistant", "content": "Previous response"}
    ])
    manager.add_to_history = AsyncMock()
    return manager

@pytest.fixture
def local_processor(mock_ollama_client, mock_conversation_manager):
    """Create a local processor with mocked dependencies."""
    return LocalProcessor(
        ollama_client=mock_ollama_client,
        conversation_manager=mock_conversation_manager
    )

@pytest.fixture
def test_request():
    """Create a test request."""
    return ClassifiedRequest(
        request_id="test_request",
        player_input="Hello",
        game_context=GameContext(
            player_id="test_player",
            player_location="main_entrance",
            current_objective="test",
            nearby_npcs=["npc1"],
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
    assert result["response_text"] == "Test response"
    
    # Verify the Ollama client was called
    mock_ollama_client.generate.assert_called_once()
    
    # Verify conversation history was updated
    mock_conversation_manager.add_to_history.assert_called_once_with(
        conversation_id="test_conversation",
        user_query="Hello",
        response="Test response",
        npc_id=None,  # Not set in test request
        player_id="test_player"
    )

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
    # Set up conversation history
    mock_history = [
        {"user": "Previous message", "assistant": "Previous response"}
    ]
    mock_conversation_manager.get_player_history.return_value = mock_history
    
    # Process the request
    result = await local_processor.process(test_request)
    
    # Verify the result
    assert result is not None
    assert result["response_text"] == "Test response"
    
    # Verify history was retrieved
    mock_conversation_manager.get_player_history.assert_called_once_with(
        test_request.game_context.player_id
    )
    
    # Verify the Ollama client was called with history
    mock_ollama_client.generate.assert_called_once()
    call_args = mock_ollama_client.generate.call_args[0][0]
    assert "Previous message" in call_args
    assert "Previous response" in call_args
    
    # Verify conversation history was updated
    mock_conversation_manager.add_to_history.assert_called_once_with(
        conversation_id="test_conversation",
        user_query="Hello",
        response="Test response",
        npc_id=None,  # Not set in test request
        player_id="test_player"
    )

@pytest.mark.asyncio
async def test_local_processor_without_conversation_manager(mock_ollama_client):
    """Test that processor works without a conversation manager."""
    # Create processor without conversation manager
    processor = LocalProcessor(ollama_client=mock_ollama_client)
    
    # Create request without conversation_id
    request = ClassifiedRequest(
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
    assert result["response_text"] == "Test response"
    
    # Verify the Ollama client was called
    mock_ollama_client.generate.assert_called_once() 