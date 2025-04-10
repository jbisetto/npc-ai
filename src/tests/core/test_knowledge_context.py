"""
Tests for knowledge context functionality in processors.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any
from datetime import datetime

from src.ai.npc.core.models import (
    ClassifiedRequest,
    GameContext,
    ProcessingTier
)
from src.ai.npc.local.local_processor import LocalProcessor
from src.ai.npc.local.ollama_client import OllamaClient, OllamaError
from src.ai.npc.hosted.hosted_processor import HostedProcessor
from src.ai.npc.hosted.bedrock_client import BedrockClient
from src.ai.npc.core.vector.knowledge_store import KnowledgeStore

@pytest.fixture
def mock_knowledge_store():
    """Create a mock knowledge store."""
    store = Mock(spec=KnowledgeStore)
    # Add a mock collection attribute with a count method
    mock_collection = Mock()
    mock_collection.count = Mock(return_value=10)  # Mock 10 documents in the collection
    store.collection = mock_collection
    
    store.contextual_search = AsyncMock(return_value=[
        {
            "text": "Test knowledge context",
            "metadata": {"source": "test_source"}
        }
    ])
    return store

@pytest.fixture
def mock_ollama_client():
    """Create a mock Ollama client."""
    client = Mock(spec=OllamaClient)
    client.generate = AsyncMock(return_value="Test response from Ollama")
    return client

@pytest.fixture
def mock_bedrock_client():
    """Create a mock Bedrock client."""
    client = Mock(spec=BedrockClient)
    client.generate = AsyncMock(return_value="Test response from Bedrock")
    return client

@pytest.fixture
def test_request():
    """Create a test request."""
    game_context = GameContext(
        player_id="test_player",
        language_proficiency={"en": 1.0, "ja": 0.5},
        player_location="station"
    )
    
    return ClassifiedRequest(
        request_id="test_request",
        player_input="Hello",
        game_context=game_context,
        processing_tier=ProcessingTier.LOCAL,
        additional_params={"conversation_id": "test_conversation"}
    )

@pytest.mark.asyncio
async def test_local_processor_knowledge_context(mock_knowledge_store, mock_ollama_client, test_request):
    """Test that LocalProcessor uses knowledge store from base class."""
    # Create processor with mock knowledge store
    processor = LocalProcessor(
        ollama_client=mock_ollama_client,
        knowledge_store=mock_knowledge_store
    )
    
    # Process request
    result = await processor.process(test_request)
    
    # Verify knowledge store was used with standardized_format=True
    mock_knowledge_store.contextual_search.assert_called_once_with(test_request, standardized_format=True)
    
    # Verify response
    assert result is not None
    assert result["response_text"] == "Test response from Ollama"

@pytest.mark.asyncio
async def test_hosted_processor_knowledge_context(mock_knowledge_store, mock_bedrock_client, test_request):
    """Test that HostedProcessor uses knowledge store from base class."""
    # Create processor with mock knowledge store
    with patch('src.ai.npc.hosted.hosted_processor.get_config') as mock_config, \
         patch.object(HostedProcessor, '_create_bedrock_client', return_value=mock_bedrock_client):
        # Mock the configuration
        mock_config.return_value = {
            'bedrock': {
                'model_id': 'test-model',
                'max_tokens': 1000,
                'temperature': 0.7
            }
        }
        
        processor = HostedProcessor(knowledge_store=mock_knowledge_store)
        
        # Process request
        result = await processor.process(test_request)
        
        # Verify knowledge store was used with standardized_format=True
        mock_knowledge_store.contextual_search.assert_called_once_with(test_request, standardized_format=True)
        
        # Verify response
        assert result is not None
        assert result["response_text"] == "Test response from Bedrock"

@pytest.mark.asyncio
async def test_knowledge_context_optimization(mock_knowledge_store, mock_ollama_client, test_request):
    """Test that knowledge context is properly included in prompts."""
    # Create processor with mock knowledge store
    with patch('src.ai.npc.core.prompt_manager.get_config') as mock_config:
        # Mock the prompt configuration to ensure knowledge context is included
        mock_config.return_value = {
            'include_knowledge_context': True,
            'include_conversation_history': True
        }
        
        processor = LocalProcessor(
            ollama_client=mock_ollama_client,
            knowledge_store=mock_knowledge_store
        )
        
        # Process request
        result = await processor.process(test_request)
        
        # Verify knowledge store was used with standardized_format=True
        mock_knowledge_store.contextual_search.assert_called_once_with(test_request, standardized_format=True)
        
        # Verify prompt includes knowledge context
        prompt_args = mock_ollama_client.generate.call_args[0][0]
        assert "Test knowledge context" in prompt_args

@pytest.mark.asyncio
async def test_empty_knowledge_context(mock_ollama_client, test_request):
    """Test that processor works with empty knowledge context."""
    # Create mock knowledge store that returns empty results
    empty_store = Mock(spec=KnowledgeStore)
    # Add mock collection for the empty store too
    mock_collection = Mock()
    mock_collection.count = Mock(return_value=0)  # Mock 0 documents
    empty_store.collection = mock_collection
    
    empty_store.contextual_search = AsyncMock(return_value=[])
    
    # Create processor with empty knowledge store
    processor = LocalProcessor(
        ollama_client=mock_ollama_client,
        knowledge_store=empty_store
    )
    
    # Process request
    result = await processor.process(test_request)
    
    # Verify knowledge store was used with standardized_format=True
    empty_store.contextual_search.assert_called_once_with(test_request, standardized_format=True)
    
    # Verify response still works
    assert result is not None
    assert result["response_text"] == "Test response from Ollama"

@pytest.mark.asyncio
async def test_knowledge_context_metadata(mock_knowledge_store, mock_ollama_client, test_request):
    """Test that knowledge context metadata is properly handled."""
    # Create processor with mock knowledge store
    with patch('src.ai.npc.core.prompt_manager.get_config') as mock_config:
        # Mock the prompt configuration to ensure knowledge context is included
        mock_config.return_value = {
            'include_knowledge_context': True,
            'include_conversation_history': True
        }
        
        processor = LocalProcessor(
            ollama_client=mock_ollama_client,
            knowledge_store=mock_knowledge_store
        )
        
        # Process request
        result = await processor.process(test_request)
        
        # Verify knowledge store was used with standardized_format=True
        mock_knowledge_store.contextual_search.assert_called_once_with(test_request, standardized_format=True)
        
        # Verify prompt includes metadata
        prompt_args = mock_ollama_client.generate.call_args[0][0]
        assert "test_source" in prompt_args 