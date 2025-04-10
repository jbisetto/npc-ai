"""
Tests for processor selection based on configuration.
"""

import pytest
import os
import yaml
from unittest.mock import patch, MagicMock, AsyncMock

from src.ai.npc import process_request
from src.ai.npc.core.models import CompanionRequest, GameContext, ProcessingTier

@pytest.fixture
def mock_config():
    """Create a mock config file."""
    config = {
        'local': {
            'enabled': False,
            'ollama': {
                'base_url': 'http://localhost:11434',
                'default_model': 'deepseek-r1:latest'
            }
        },
        'hosted': {
            'enabled': True,
            'bedrock': {
                'default_model': 'amazon.nova-micro-v1:0',
                'max_tokens': 1000,
                'temperature': 0.7
            }
        }
    }
    return config

@pytest.fixture
def mock_request():
    """Create a mock request."""
    return CompanionRequest(
        request_id="test-request-id",
        player_input="Hello",
        game_context=GameContext(
            player_id="test-player",
            language_proficiency={"en": 0.8, "ja": 0.3},
            player_location="station",
            current_objective="Test objective"
        ),
        additional_params={}
    )

@pytest.fixture
def mock_bedrock_client():
    """Create a mock BedrockClient."""
    return MagicMock()

@pytest.mark.asyncio
async def test_processor_selection_hosted(mock_config, mock_request, mock_bedrock_client):
    """Test that hosted processor is selected when local is disabled and hosted is enabled."""
    with patch('src.ai.npc.config.get_full_config', return_value=mock_config), \
         patch('src.ai.npc.hosted.hosted_processor.BedrockClient', return_value=mock_bedrock_client):
        with patch('src.ai.npc.get_hosted_processor') as mock_get_hosted, \
             patch('src.ai.npc.get_local_processor') as mock_get_local:
            # Setup mock hosted processor
            mock_hosted = AsyncMock()
            mock_hosted.process.return_value = {
                'response_text': 'Test response',
                'processing_tier': ProcessingTier.HOSTED
            }
            mock_get_hosted.return_value = mock_hosted
            
            # Process request
            response = await process_request(mock_request)
            
            # Verify hosted processor was used
            mock_get_hosted.assert_called_once()
            mock_get_local.assert_not_called()
            assert response['processing_tier'] == ProcessingTier.HOSTED

@pytest.mark.asyncio
async def test_processor_selection_local(mock_config, mock_request, mock_bedrock_client):
    """Test that local processor is selected when local is enabled and hosted is disabled."""
    # Modify config to enable local and disable hosted
    mock_config['local']['enabled'] = True
    mock_config['hosted']['enabled'] = False
    
    with patch('src.ai.npc.config.get_full_config', return_value=mock_config), \
         patch('src.ai.npc.hosted.hosted_processor.BedrockClient', return_value=mock_bedrock_client):
        with patch('src.ai.npc.get_local_processor') as mock_get_local, \
             patch('src.ai.npc.get_hosted_processor') as mock_get_hosted:
            # Setup mock local processor
            mock_local = AsyncMock()
            mock_local.process.return_value = {
                'response_text': 'Test response',
                'processing_tier': ProcessingTier.LOCAL
            }
            mock_get_local.return_value = mock_local
            
            # Process request
            response = await process_request(mock_request)
            
            # Verify local processor was used
            mock_get_local.assert_called_once()
            mock_get_hosted.assert_not_called()
            assert response['processing_tier'] == ProcessingTier.LOCAL

@pytest.mark.asyncio
async def test_processor_selection_error(mock_config, mock_request, mock_bedrock_client):
    """Test that an error is raised when no processor is enabled."""
    # Modify config to disable both processors
    mock_config['local']['enabled'] = False
    mock_config['hosted']['enabled'] = False
    
    with patch('src.ai.npc.config.get_full_config', return_value=mock_config), \
         patch('src.ai.npc.hosted.hosted_processor.BedrockClient', return_value=mock_bedrock_client):
        with pytest.raises(ValueError, match="No processing tier enabled in config"):
            await process_request(mock_request)

@pytest.mark.asyncio
async def test_processor_selection_both_enabled(mock_config, mock_request, mock_bedrock_client):
    """Test that hosted processor is preferred when both are enabled."""
    # Modify config to enable both processors
    mock_config['local']['enabled'] = True
    mock_config['hosted']['enabled'] = True
    
    with patch('src.ai.npc.config.get_full_config', return_value=mock_config), \
         patch('src.ai.npc.hosted.hosted_processor.BedrockClient', return_value=mock_bedrock_client):
        with patch('src.ai.npc.get_hosted_processor') as mock_get_hosted, \
             patch('src.ai.npc.get_local_processor') as mock_get_local:
            # Setup mock hosted processor
            mock_hosted = AsyncMock()
            mock_hosted.process.return_value = {
                'response_text': 'Test response',
                'processing_tier': ProcessingTier.HOSTED
            }
            mock_get_hosted.return_value = mock_hosted
            
            # Process request
            response = await process_request(mock_request)
            
            # Verify hosted processor was used (preferred over local)
            mock_get_hosted.assert_called_once()
            mock_get_local.assert_not_called()
            assert response['processing_tier'] == ProcessingTier.HOSTED

@pytest.mark.asyncio
async def test_processor_conversation_history_integration(mock_config, mock_request, mock_bedrock_client):
    """Test that conversation history is properly integrated when using process_request."""
    # Set up test data
    conversation_id = "test-conversation-id"
    conversation_history = [
        {
            "user": "Previous user message",
            "assistant": "Previous assistant response",
            "timestamp": "2023-01-01T12:00:00Z",
            "conversation_id": conversation_id
        }
    ]
    
    # Add conversation_id to request
    mock_request.additional_params = {"conversation_id": conversation_id}
    
    # Test with local processor
    mock_config['local']['enabled'] = True
    mock_config['hosted']['enabled'] = False
    
    with patch('src.ai.npc.config.get_full_config', return_value=mock_config), \
         patch('src.ai.npc.get_conversation_manager') as mock_get_manager, \
         patch('src.ai.npc.local.ollama_client.OllamaClient') as mock_ollama_client, \
         patch('src.ai.npc.get_knowledge_store') as mock_get_knowledge_store:
        
        # Setup mock conversation manager
        mock_manager = AsyncMock()
        mock_manager.get_player_history.return_value = conversation_history
        mock_manager.add_to_history.return_value = None
        mock_get_manager.return_value = mock_manager
        
        # Setup mock knowledge store
        mock_knowledge_store = AsyncMock()
        mock_knowledge_store.contextual_search.return_value = []
        mock_knowledge_store.collection.count.return_value = 0
        mock_get_knowledge_store.return_value = mock_knowledge_store
        
        # Setup mock Ollama client
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="Test response")
        mock_ollama_client.return_value = mock_client
        
        # Process request
        response = await process_request(mock_request)
        
        # Verify conversation history was retrieved and used
        mock_manager.get_player_history.assert_called_once()
        
        # Capture the prompt that was passed to generate
        generate_calls = mock_client.generate.call_args_list
        assert len(generate_calls) == 1
        prompt = generate_calls[0][0][0]  # First call, first arg
        
        # Verify the prompt contains the conversation history
        assert "Previous conversation:" in prompt
        assert "Previous user message" in prompt
        assert "Previous assistant response" in prompt
        
        # Verify conversation history was updated
        mock_manager.add_to_history.assert_called_once()
    
    # Now test with hosted processor
    mock_config['local']['enabled'] = False
    mock_config['hosted']['enabled'] = True
    
    with patch('src.ai.npc.config.get_full_config', return_value=mock_config), \
         patch('src.ai.npc.get_conversation_manager') as mock_get_manager, \
         patch('src.ai.npc.hosted.hosted_processor.BedrockClient') as mock_bedrock_class, \
         patch('src.ai.npc.get_knowledge_store') as mock_get_knowledge_store:
        
        # Setup mock conversation manager
        mock_manager = AsyncMock()
        mock_manager.get_player_history.return_value = conversation_history
        mock_manager.add_to_history.return_value = None
        mock_get_manager.return_value = mock_manager
        
        # Setup mock knowledge store
        mock_knowledge_store = AsyncMock()
        mock_knowledge_store.contextual_search.return_value = []
        mock_knowledge_store.collection.count.return_value = 0
        mock_get_knowledge_store.return_value = mock_knowledge_store
        
        # Setup mock Bedrock client
        mock_bedrock = AsyncMock()
        mock_bedrock.generate = AsyncMock(return_value="Test response")
        mock_bedrock_class.return_value = mock_bedrock
        
        # Process request
        response = await process_request(mock_request)
        
        # Verify conversation history was retrieved and used
        mock_manager.get_player_history.assert_called_once()
        
        # Capture the prompt that was passed to generate
        generate_calls = mock_bedrock.generate.call_args_list
        assert len(generate_calls) == 1
        prompt = generate_calls[0][0][0]  # First call, first arg
        
        # Verify the prompt contains the conversation history
        assert "Previous conversation:" in prompt
        assert "Previous user message" in prompt
        assert "Previous assistant response" in prompt
        
        # Verify conversation history was updated
        mock_manager.add_to_history.assert_called_once()

@pytest.mark.asyncio
async def test_conversation_continuity_across_requests(mock_config, mock_request, mock_bedrock_client):
    """Test that conversation history is continuous across multiple requests."""
    # Set up test data
    conversation_id = "test-conversation-id"
    player_id = mock_request.game_context.player_id
    
    # Add conversation_id to request
    mock_request.additional_params = {"conversation_id": conversation_id}
    
    # Configure for local processor
    mock_config['local']['enabled'] = True
    mock_config['hosted']['enabled'] = False
    
    # Setup in-memory history storage to simulate real history accumulation
    conversation_history = []
    
    # Test with multiple requests to the local processor
    with patch('src.ai.npc.config.get_full_config', return_value=mock_config), \
         patch('src.ai.npc.get_conversation_manager') as mock_get_manager, \
         patch('src.ai.npc.local.ollama_client.OllamaClient') as mock_ollama_client, \
         patch('src.ai.npc.get_knowledge_store') as mock_get_knowledge_store, \
         patch('src.ai.npc.get_local_processor') as mock_get_local_processor:
        
        # Setup mock knowledge store
        mock_knowledge_store = AsyncMock()
        mock_knowledge_store.contextual_search.return_value = []
        mock_knowledge_store.collection.count.return_value = 0
        mock_get_knowledge_store.return_value = mock_knowledge_store
        
        # Setup mock Ollama client
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(side_effect=["Response 1", "Response 2", "Response 3"])
        mock_ollama_client.return_value = mock_client
        
        # Setup mock local processor
        mock_local = AsyncMock()
        responses = ["Response 1", "Response 2", "Response 3"]
        async def process_with_history_update(request):
            response_text = responses.pop(0)
            result = {
                "response_text": response_text, 
                "processing_tier": ProcessingTier.LOCAL
            }
            # Update conversation history
            await mock_manager.add_to_history(
                conversation_id=request.additional_params.get("conversation_id"),
                user_query=request.player_input,
                response=result["response_text"],
                npc_id=request.game_context.npc_id,
                player_id=request.game_context.player_id
            )
            return result
            
        mock_local.process = process_with_history_update
        mock_get_local_processor.return_value = mock_local
        
        # Setup mock conversation manager that simulates real history accumulation
        mock_manager = AsyncMock()
        mock_manager.get_player_history.side_effect = lambda player_id, **kwargs: conversation_history.copy()
        
        # Define a function to accumulate history
        async def add_to_history_func(
            conversation_id, 
            user_query, 
            response, 
            npc_id, 
            player_id, 
            **kwargs
        ):
            conversation_history.insert(0, {
                "user": user_query,
                "assistant": response,
                "timestamp": "2023-01-01T12:00:00Z",
                "conversation_id": conversation_id
            })
            
        mock_manager.add_to_history.side_effect = add_to_history_func
        mock_get_manager.return_value = mock_manager
        
        # First request: "Hello"
        mock_request.player_input = "Hello"
        response1 = await process_request(mock_request)
        
        # Second request: "How are you?"
        mock_request.player_input = "How are you?"
        response2 = await process_request(mock_request)
        
        # Third request: "Thank you"
        mock_request.player_input = "Thank you"
        response3 = await process_request(mock_request)
        
        # At this point, we should have 3 conversation turns in the history
        assert len(conversation_history) == 3
        
        # Check that history was properly maintained
        assert conversation_history[0]["user"] == "Thank you"  # Most recent first
        assert conversation_history[1]["user"] == "How are you?"
        assert conversation_history[2]["user"] == "Hello"
        
        # Check that we got different responses for each request
        assert response1["response_text"] == "Response 1"
        assert response2["response_text"] == "Response 2"
        assert response3["response_text"] == "Response 3"

@pytest.mark.asyncio
async def test_cross_processor_conversation_continuity(mock_config, mock_request, mock_bedrock_client):
    """Test that conversation history is maintained when switching between processor types."""
    # Set up test data
    conversation_id = "test-conversation-id"
    player_id = mock_request.game_context.player_id
    
    # Add conversation_id to request
    mock_request.additional_params = {"conversation_id": conversation_id}
    
    # Setup in-memory history storage
    conversation_history = []
    
    # Mock add_to_history to accumulate conversation
    async def add_to_history_func(
        conversation_id, 
        user_query, 
        response, 
        npc_id, 
        player_id, 
        **kwargs
    ):
        conversation_history.insert(0, {
            "user": user_query,
            "assistant": response,
            "timestamp": "2023-01-01T12:00:00Z",
            "conversation_id": conversation_id
        })

    # Define common test setup
    def setup_mocks():
        # Setup mock conversation manager
        mock_manager = AsyncMock()
        mock_manager.get_player_history.side_effect = lambda player_id, **kwargs: conversation_history.copy()
        mock_manager.add_to_history.side_effect = add_to_history_func
        
        # Setup mock knowledge store
        mock_knowledge_store = AsyncMock()
        mock_knowledge_store.contextual_search.return_value = []
        mock_knowledge_store.collection.count.return_value = 0
        
        return mock_manager, mock_knowledge_store
    
    # First request with local processor
    mock_config['local']['enabled'] = True
    mock_config['hosted']['enabled'] = False
    
    with patch('src.ai.npc.config.get_full_config', return_value=mock_config), \
         patch('src.ai.npc.get_conversation_manager') as mock_get_manager, \
         patch('src.ai.npc.local.ollama_client.OllamaClient') as mock_ollama_client, \
         patch('src.ai.npc.get_knowledge_store') as mock_get_knowledge_store, \
         patch('src.ai.npc.get_local_processor') as mock_get_local:
        
        mock_manager, mock_knowledge_store_obj = setup_mocks()
        mock_get_manager.return_value = mock_manager
        mock_get_knowledge_store.return_value = mock_knowledge_store_obj
        
        # Setup mock Ollama client
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="Local response")
        mock_ollama_client.return_value = mock_client
        
        # Setup mock local processor
        mock_local_processor = AsyncMock()
        async def process_with_history_update(request):
            result = {"response_text": "Local response", "processing_tier": ProcessingTier.LOCAL}
            # Update conversation history
            await mock_manager.add_to_history(
                conversation_id=request.additional_params.get("conversation_id"),
                user_query=request.player_input,
                response=result["response_text"],
                npc_id=request.game_context.npc_id,
                player_id=request.game_context.player_id
            )
            return result
            
        mock_local_processor.process = process_with_history_update
        mock_get_local.return_value = mock_local_processor
        
        # First request with local processor
        mock_request.player_input = "Hello from local"
        response_local = await process_request(mock_request)
        
        assert response_local["response_text"] == "Local response"
        assert len(conversation_history) == 1
        assert conversation_history[0]["user"] == "Hello from local"
        assert conversation_history[0]["assistant"] == "Local response"
    
    # Second request with hosted processor
    mock_config['local']['enabled'] = False
    mock_config['hosted']['enabled'] = True
    
    with patch('src.ai.npc.config.get_full_config', return_value=mock_config), \
         patch('src.ai.npc.get_conversation_manager') as mock_get_manager, \
         patch('src.ai.npc.hosted.hosted_processor.BedrockClient') as mock_bedrock_class, \
         patch('src.ai.npc.get_knowledge_store') as mock_get_knowledge_store, \
         patch('src.ai.npc.get_hosted_processor') as mock_get_hosted:
        
        mock_manager, mock_knowledge_store_obj = setup_mocks()
        mock_get_manager.return_value = mock_manager
        mock_get_knowledge_store.return_value = mock_knowledge_store_obj
        
        # Setup mock Bedrock client
        mock_bedrock = AsyncMock()
        mock_bedrock.generate = AsyncMock(return_value="Hosted response")
        mock_bedrock_class.return_value = mock_bedrock
        
        # Setup mock hosted processor
        mock_hosted_processor = AsyncMock()
        async def process_with_history_update(request):
            result = {"response_text": "Hosted response", "processing_tier": ProcessingTier.HOSTED}
            # Update conversation history
            await mock_manager.add_to_history(
                conversation_id=request.additional_params.get("conversation_id"),
                user_query=request.player_input,
                response=result["response_text"],
                npc_id=request.game_context.npc_id,
                player_id=request.game_context.player_id
            )
            return result
            
        mock_hosted_processor.process = process_with_history_update
        mock_get_hosted.return_value = mock_hosted_processor
        
        # Second request with hosted processor
        mock_request.player_input = "Hello from hosted"
        response_hosted = await process_request(mock_request)
        
        # Verify response
        assert response_hosted["response_text"] == "Hosted response"
        
        # Check history has been updated and maintained across processors
        assert len(conversation_history) == 2
        assert conversation_history[0]["user"] == "Hello from hosted"
        assert conversation_history[0]["assistant"] == "Hosted response"
        assert conversation_history[1]["user"] == "Hello from local"
        assert conversation_history[1]["assistant"] == "Local response" 