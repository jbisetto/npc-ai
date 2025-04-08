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
        )
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