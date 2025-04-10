"""
Tests for OllamaClient class.
"""

import pytest
import aiohttp
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from contextlib import asynccontextmanager

from src.ai.npc.local.ollama_client import OllamaClient, OllamaError

@pytest.mark.asyncio
async def test_generate_success():
    """Test successful generation."""
    # Create a mock response with the expected return data
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"response": "Test response"})
    
    # Create a mock for the session's post method that returns our mock response
    mock_post_cm = AsyncMock()
    mock_post_cm.__aenter__.return_value = mock_response
    
    # Create a mock session with the post method returning our context manager
    mock_session = MagicMock()
    mock_session.post.return_value = mock_post_cm
    
    # Create a mock for the ClientSession that returns our mock session
    mock_client_session_cm = AsyncMock()
    mock_client_session_cm.__aenter__.return_value = mock_session
    
    # Patch ClientSession to return our mock context manager
    with patch('aiohttp.ClientSession', return_value=mock_client_session_cm):
        client = OllamaClient()
        response = await client.generate("Test prompt")
        
        # Verify the response
        assert response == "Test response"
        
        # Verify the post was called with expected arguments
        mock_session.post.assert_called_once()

@pytest.mark.asyncio
async def test_consecutive_requests():
    """Test that multiple requests create new sessions each time."""
    # Create two mock responses
    mock_response1 = MagicMock()
    mock_response1.status = 200
    mock_response1.json = AsyncMock(return_value={"response": "Response 1"})
    
    mock_response2 = MagicMock()
    mock_response2.status = 200
    mock_response2.json = AsyncMock(return_value={"response": "Response 2"})
    
    # Create mocks for post context managers
    mock_post_cm1 = AsyncMock()
    mock_post_cm1.__aenter__.return_value = mock_response1
    
    mock_post_cm2 = AsyncMock()
    mock_post_cm2.__aenter__.return_value = mock_response2
    
    # Create mock sessions with post methods
    mock_session1 = MagicMock()
    mock_session1.post.return_value = mock_post_cm1
    
    mock_session2 = MagicMock()
    mock_session2.post.return_value = mock_post_cm2
    
    # Create mocks for ClientSession context managers
    mock_client_session_cm1 = AsyncMock()
    mock_client_session_cm1.__aenter__.return_value = mock_session1
    
    mock_client_session_cm2 = AsyncMock()
    mock_client_session_cm2.__aenter__.return_value = mock_session2
    
    # Set up the ClientSession mock to return our context managers in sequence
    with patch('aiohttp.ClientSession', side_effect=[mock_client_session_cm1, mock_client_session_cm2]):
        client = OllamaClient()
        
        # Make first request
        response1 = await client.generate("Prompt 1")
        
        # Make second request
        response2 = await client.generate("Prompt 2")
        
        # Verify responses
        assert response1 == "Response 1"
        assert response2 == "Response 2"

@pytest.mark.asyncio
async def test_generate_error():
    """Test error handling during generation."""
    # Create a mock session that raises an exception
    mock_session = MagicMock()
    mock_session.post = MagicMock(side_effect=aiohttp.ClientError("Connection error"))
    
    # Create a mock context manager that returns our mock session
    mock_client_session_cm = AsyncMock()
    mock_client_session_cm.__aenter__.return_value = mock_session
    
    with patch('aiohttp.ClientSession', return_value=mock_client_session_cm):
        client = OllamaClient()
        
        # Should raise OllamaError
        with pytest.raises(OllamaError) as excinfo:
            await client.generate("Test prompt")
        
        # Verify error message
        assert "Connection error" in str(excinfo.value)

@pytest.mark.asyncio
async def test_close():
    """Test that close method works correctly."""
    mock_session = AsyncMock()
    mock_session.closed = False
    
    client = OllamaClient()
    client.session = mock_session
    
    await client.close()
    
    # Verify session was closed if it existed
    if hasattr(client, 'session') and client.session:
        mock_session.close.assert_called_once() 