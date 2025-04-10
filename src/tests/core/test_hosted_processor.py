"""
Tests for the hosted processor implementation.

This module tests the HostedProcessor class, which handles request processing
using Amazon Bedrock. All external services are mocked.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any
from datetime import datetime

from src.ai.npc.core.models import (
    ClassifiedRequest,
    GameContext,
    ProcessingTier,
    NPCRequest
)
from src.ai.npc.hosted.hosted_processor import HostedProcessor
from src.ai.npc.hosted.bedrock_client import BedrockClient, BedrockError
from src.ai.npc.hosted.usage_tracker import UsageTracker
from src.ai.npc.core.context_manager import ContextManager
from src.ai.npc.core.conversation_manager import ConversationManager
from src.ai.npc.core.adapters import ConversationHistoryEntry, KnowledgeDocument
from src.ai.npc.core.vector.knowledge_store import KnowledgeStore

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
    # Return standardized format conversation history
    manager.get_player_history = AsyncMock(return_value=[
        ConversationHistoryEntry(
            user="Previous question",
            assistant="Previous answer",
            timestamp=datetime.now().isoformat(),
            conversation_id="test_conversation"
        )
    ])
    manager.add_to_history = AsyncMock()
    return manager

@pytest.fixture
def mock_knowledge_store():
    """Create a mock knowledge store."""
    store = Mock(spec=KnowledgeStore)
    # Add a mock collection attribute with a count method
    mock_collection = Mock()
    mock_collection.count = Mock(return_value=10)  # Mock 10 documents in the collection
    store.collection = mock_collection
    
    # Setup the contextual_search method
    store.contextual_search = AsyncMock(return_value=[
        KnowledgeDocument(
            text="Test knowledge context",
            id="test_doc_1",
            metadata={"source": "test_source"},
            relevance_score=0.9
        )
    ])
    return store

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
    return NPCRequest(
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
    # Process the request
    result = await hosted_processor.process(test_request)
    
    # Verify the result
    assert result is not None
    assert result["response_text"] == "Test response from Bedrock"
    
    # Verify conversation history was retrieved and used
    mock_conversation_manager.get_player_history.assert_called_once_with(
        test_request.game_context.player_id,
        standardized_format=True
    )
    mock_bedrock_client.generate.assert_called_once()

@pytest.mark.asyncio
async def test_hosted_processor_without_conversation_manager(mock_bedrock_client, mock_usage_tracker):
    """Test that processor works without a conversation manager."""
    # Create processor without conversation manager
    processor = HostedProcessor(usage_tracker=mock_usage_tracker)
    
    # Create request without conversation_id
    request = NPCRequest(
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

@pytest.mark.asyncio
async def test_hosted_processor_history_in_prompt(hosted_processor, test_request, mock_bedrock_client, mock_conversation_manager):
    """Test that conversation history is correctly included in the generated prompt."""
    # Create a test request with a conversation ID
    test_request.additional_params["conversation_id"] = "test_conversation"
    
    # Process the request
    result = await hosted_processor.process(test_request)
    
    # Verify conversation history was retrieved
    mock_conversation_manager.get_player_history.assert_called_once_with(
        test_request.game_context.player_id,
        standardized_format=True
    )
    
    # Verify the Bedrock client was called
    mock_bedrock_client.generate.assert_called_once()
    
    # Extract the prompt from the call to the Bedrock client
    call_args = mock_bedrock_client.generate.call_args[0][0]
    
    # Assert that the prompt contains conversation history
    assert "Previous conversation:" in call_args
    assert "Previous question" in call_args
    assert "Previous answer" in call_args
    
    # Verify that debug info contains history count
    assert "debug_info" in result
    assert "history_count" in result["debug_info"]
    assert result["debug_info"]["history_count"] == 1
    
    # Verify conversation history was updated with the new exchange
    mock_conversation_manager.add_to_history.assert_called_once_with(
        conversation_id="test_conversation",
        user_query="Hello",
        response="Test response from Bedrock",
        npc_id="test_npc",
        player_id="test_player"
    )

@pytest.mark.asyncio
async def test_hosted_processor_multiple_history_exchanges(hosted_processor, test_request, mock_bedrock_client, mock_conversation_manager):
    """Test that multiple conversation exchanges are correctly maintained in history."""
    # Update the mock to return multiple history entries in reverse chronological order
    mock_conversation_manager.get_player_history.return_value = [
        ConversationHistoryEntry(
            user="Second question",
            assistant="Second answer",
            timestamp=datetime.now().isoformat(),
            conversation_id="test_conversation"
        ),
        ConversationHistoryEntry(
            user="First question",
            assistant="First answer",
            timestamp=datetime.now().isoformat(),
            conversation_id="test_conversation"
        )
    ]
    
    # Set the conversation ID
    test_request.additional_params["conversation_id"] = "test_conversation"
    
    # Process the request
    result = await hosted_processor.process(test_request)
    
    # Verify conversation history was retrieved
    mock_conversation_manager.get_player_history.assert_called_once()
    
    # Extract the prompt from the call to the Bedrock client
    call_args = mock_bedrock_client.generate.call_args[0][0]
    
    # Assert that the prompt contains both conversation entries
    assert "Previous conversation:" in call_args
    assert "First question" in call_args
    assert "First answer" in call_args
    assert "Second question" in call_args
    assert "Second answer" in call_args
    
    # Verify that debug info contains correct history count
    assert result["debug_info"]["history_count"] == 2
    
    # Verify conversation history was updated with the new exchange
    mock_conversation_manager.add_to_history.assert_called_once()

@pytest.mark.asyncio
async def test_hosted_processor_multiple_conversations(
    hosted_processor, 
    test_request, 
    mock_bedrock_client, 
    mock_conversation_manager
):
    """Test that different conversations for the same player with different NPCs are handled correctly."""
    # First conversation with NPC1
    test_request.additional_params["conversation_id"] = "conversation_with_npc1"
    test_request.game_context.npc_id = "npc1"
    
    # Mock the conversation history for NPC1
    mock_conversation_manager.get_player_history.return_value = [
        ConversationHistoryEntry(
            user="Question for NPC1",
            assistant="Answer from NPC1",
            timestamp=datetime.now().isoformat(),
            conversation_id="conversation_with_npc1"
        )
    ]
    
    # Process first request
    await hosted_processor.process(test_request)
    
    # Verify the correct history was retrieved and used for NPC1
    call_args_npc1 = mock_bedrock_client.generate.call_args[0][0]
    assert "Question for NPC1" in call_args_npc1
    assert "Answer from NPC1" in call_args_npc1
    
    # Reset the mocks
    mock_bedrock_client.generate.reset_mock()
    mock_conversation_manager.get_player_history.reset_mock()
    
    # Second conversation with NPC2
    test_request.additional_params["conversation_id"] = "conversation_with_npc2"
    test_request.game_context.npc_id = "npc2"
    
    # Mock the conversation history for NPC2
    mock_conversation_manager.get_player_history.return_value = [
        ConversationHistoryEntry(
            user="Question for NPC2",
            assistant="Answer from NPC2",
            timestamp=datetime.now().isoformat(),
            conversation_id="conversation_with_npc2"
        )
    ]
    
    # Process second request
    await hosted_processor.process(test_request)
    
    # Verify the correct history was retrieved and used for NPC2
    call_args_npc2 = mock_bedrock_client.generate.call_args[0][0]
    assert "Question for NPC2" in call_args_npc2
    assert "Answer from NPC2" in call_args_npc2
    
    # Verify NPC1's conversation is not in NPC2's prompt
    assert "Question for NPC1" not in call_args_npc2
    assert "Answer from NPC1" not in call_args_npc2

@pytest.mark.asyncio
async def test_hosted_processor_empty_history(
    hosted_processor, 
    test_request, 
    mock_bedrock_client, 
    mock_conversation_manager
):
    """Test that the processor correctly handles empty conversation history."""
    # Set the conversation ID but return empty history
    test_request.additional_params["conversation_id"] = "test_conversation"
    mock_conversation_manager.get_player_history.return_value = []
    
    # Process the request
    result = await hosted_processor.process(test_request)
    
    # Verify conversation history was retrieved but was empty
    mock_conversation_manager.get_player_history.assert_called_once()
    
    # Extract the prompt from the call to the Bedrock client
    call_args = mock_bedrock_client.generate.call_args[0][0]
    
    # Assert that the prompt doesn't contain conversation history section
    assert "Previous conversation:" not in call_args
    
    # Verify that debug info shows zero history entries
    assert result["debug_info"]["history_count"] == 0
    
    # Verify conversation history was updated with the new exchange (first entry)
    mock_conversation_manager.add_to_history.assert_called_once()

@pytest.mark.asyncio
async def test_hosted_processor_long_history(
    hosted_processor, 
    test_request, 
    mock_bedrock_client, 
    mock_conversation_manager
):
    """Test that the processor correctly handles long conversation history."""
    # Create a long history with 20 entries
    long_history = []
    for i in range(20):
        long_history.append(
            ConversationHistoryEntry(
                user=f"Question {i}",
                assistant=f"Answer {i}",
                timestamp=datetime.now().isoformat(),
                conversation_id="test_conversation"
            )
        )
    
    mock_conversation_manager.get_player_history.return_value = long_history
    test_request.additional_params["conversation_id"] = "test_conversation"
    
    # Process the request
    result = await hosted_processor.process(test_request)
    
    # Verify history was retrieved
    mock_conversation_manager.get_player_history.assert_called_once()
    
    # Extract the prompt
    call_args = mock_bedrock_client.generate.call_args[0][0]
    
    # The prompt should contain history, but might be truncated by the prompt optimizer
    assert "Previous conversation:" in call_args
    
    # Verify debug info contains correct history count
    assert result["debug_info"]["history_count"] == 20
    
    # History optimization should keep more recent conversations, check for the most recent ones
    assert "Question 19" in call_args
    assert "Answer 19" in call_args 