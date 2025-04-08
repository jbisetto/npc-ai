"""
Tests for the hosted processor implementation.

This module tests the HostedProcessor class, which handles request processing
using Amazon Bedrock. All external services are mocked.
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
from src.ai.npc.hosted.hosted_processor import HostedProcessor
from src.ai.npc.hosted.bedrock_client import BedrockClient, BedrockError
from src.ai.npc.hosted.usage_tracker import UsageTracker
from src.ai.npc.core.context_manager import ContextManager
from src.ai.npc.core.conversation_manager import ConversationManager

@pytest.fixture
def mock_bedrock_client():
    """Create a mock Bedrock client."""
    with patch('src.ai.npc.hosted.hosted_processor.BedrockClient') as mock:
        client = Mock(spec=BedrockClient)
        client.generate = AsyncMock(return_value="Test response from Bedrock")
        mock.return_value = client
        yield client

@pytest.fixture
def mock_usage_tracker():
    """Create a mock usage tracker."""
    tracker = Mock(spec=UsageTracker)
    tracker.track_usage = AsyncMock()
    return tracker

@pytest.fixture
def mock_context_manager():
    """Create a mock context manager."""
    manager = Mock(spec=ContextManager)
    manager.get_context = AsyncMock()
    manager.update_context = AsyncMock()
    return manager

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
def hosted_processor(mock_bedrock_client, mock_usage_tracker, mock_context_manager, mock_conversation_manager):
    """Create a hosted processor with mocked dependencies."""
    with patch('src.ai.npc.hosted.hosted_processor.get_config') as mock_config:
        # Mock the configuration
        mock_config.return_value = {
            'bedrock': {
                'model_id': 'test-model',
                'max_tokens': 1000,
                'temperature': 0.7,
                'top_p': 0.9,
                'top_k': 50,
                'stop_sequences': ["\n\n"]
            }
        }
        return HostedProcessor(
            usage_tracker=mock_usage_tracker,
            context_manager=mock_context_manager,
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
            npc_id="test_npc",
            language_proficiency={"japanese": 0.5, "english": 1.0}
        ),
        processing_tier=ProcessingTier.HOSTED,
        additional_params={
            "conversation_id": "test_conversation"
        }
    )

@pytest.mark.asyncio
async def test_hosted_processor_initialization(mock_bedrock_client, mock_usage_tracker):
    """Test that HostedProcessor initializes correctly."""
    processor = HostedProcessor(usage_tracker=mock_usage_tracker)
    assert processor.client is not None
    assert processor.prompt_manager is not None
    assert processor.response_parser is not None

@pytest.mark.asyncio
async def test_hosted_processor_process_request(
    hosted_processor,
    test_request,
    mock_bedrock_client,
    mock_conversation_manager
):
    """Test processing a request with the hosted processor."""
    # Process the request
    result = await hosted_processor.process(test_request)
    
    # Verify the result
    assert result is not None
    assert "response_text" in result
    assert result["response_text"] == "Test response from Bedrock"
    
    # Verify the Bedrock client was called
    mock_bedrock_client.generate.assert_called_once()
    
    # Verify conversation history was updated
    mock_conversation_manager.add_to_history.assert_called_once_with(
        conversation_id="test_conversation",
        user_query="Hello",
        response="Test response from Bedrock",
        npc_id="test_npc",
        player_id="test_player"
    )

@pytest.mark.asyncio
async def test_hosted_processor_quota_error(hosted_processor, test_request, mock_bedrock_client):
    """Test handling of quota exceeded errors."""
    # Make the Bedrock client raise a quota error
    quota_error = BedrockError("Quota exceeded", error_type=BedrockError.QUOTA_ERROR)
    mock_bedrock_client.generate.side_effect = quota_error
    
    # Process the request
    result = await hosted_processor.process(test_request)
    
    # Verify we got the quota-specific fallback response
    assert result is not None
    assert "response_text" in result
    assert "reached my limit" in result["response_text"].lower()
    assert result["is_fallback"] is True

@pytest.mark.asyncio
async def test_hosted_processor_general_error(hosted_processor, test_request, mock_bedrock_client):
    """Test handling of general errors."""
    # Make the Bedrock client raise a general error
    mock_bedrock_client.generate.side_effect = Exception("Test error")
    
    # Process the request
    result = await hosted_processor.process(test_request)
    
    # Verify we got the general fallback response
    assert result is not None
    assert "response_text" in result
    assert "trouble understanding" in result["response_text"].lower()
    assert result["is_fallback"] is True

@pytest.mark.asyncio
async def test_hosted_processor_with_history(hosted_processor, test_request, mock_bedrock_client, mock_conversation_manager):
    """Test processing a request with conversation history."""
    # Set up mock conversation history
    history = [
        {"role": "user", "content": "Previous question"},
        {"role": "assistant", "content": "Previous answer"}
    ]
    mock_conversation_manager.get_player_history.return_value = history
    
    # Process the request
    result = await hosted_processor.process(test_request)
    
    # Verify the result
    assert result is not None
    assert result["response_text"] == "Test response from Bedrock"
    
    # Verify conversation history was retrieved and used
    mock_conversation_manager.get_player_history.assert_called_once_with(test_request.game_context.player_id)
    mock_bedrock_client.generate.assert_called_once()

@pytest.mark.asyncio
async def test_hosted_processor_without_conversation_manager(mock_bedrock_client, mock_usage_tracker):
    """Test that processor works without a conversation manager."""
    # Create processor without conversation manager
    processor = HostedProcessor(usage_tracker=mock_usage_tracker)
    
    # Create request without conversation_id
    request = ClassifiedRequest(
        request_id="test_request",
        player_input="Hello",
        game_context=GameContext(
            player_id="test_player",
            language_proficiency={"japanese": 0.5, "english": 1.0}
        ),
        processing_tier=ProcessingTier.HOSTED
    )
    
    # Process the request
    result = await processor.process(request)
    
    # Verify the result
    assert result is not None
    assert result["response_text"] == "Test response from Bedrock" 