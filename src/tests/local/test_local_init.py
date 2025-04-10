"""
Tests for local module initialization.
"""

import pytest
from unittest.mock import patch, MagicMock
import asyncio

from src.ai.npc.local import get_local_processor
from src.ai.npc.local.local_processor import LocalProcessor

@pytest.mark.asyncio
async def test_get_local_processor_closes_existing():
    """Test that get_local_processor closes any existing processor."""
    # Create a mock LocalProcessor
    mock_processor = MagicMock(spec=LocalProcessor)
    
    # Simple mock for asyncio.run that doesn't try to execute the coroutine
    mock_run = MagicMock()
    
    # Patch the global _local_processor variable and asyncio.run
    with patch('src.ai.npc.local._local_processor', mock_processor), \
         patch('asyncio.run', mock_run):
        # Patch the import and constructor to return a new mock
        new_processor = MagicMock(spec=LocalProcessor)
        with patch('src.ai.npc.local.local_processor.LocalProcessor', return_value=new_processor):
            # Call get_local_processor
            result = get_local_processor()
            
            # Verify that close was called on the processor
            mock_processor.close.assert_called_once()
            
            # Verify that asyncio.run was called
            mock_run.assert_called_once()
            
            # Verify that the result is the new processor
            assert result is new_processor

@pytest.mark.asyncio
async def test_get_local_processor_creates_new_when_none_exists():
    """Test that get_local_processor creates a new processor when none exists."""
    # Patch the global _local_processor variable to None
    mock_run = MagicMock()
    with patch('src.ai.npc.local._local_processor', None), \
         patch('asyncio.run', mock_run):  # Also patch asyncio.run though it shouldn't be called
        # Patch the import and constructor to return a mock
        mock_processor = MagicMock(spec=LocalProcessor)
        with patch('src.ai.npc.local.local_processor.LocalProcessor', return_value=mock_processor):
            # Call get_local_processor
            result = get_local_processor()
            
            # Verify that the result is the new processor
            assert result is mock_processor
            
            # Verify that asyncio.run was not called
            mock_run.assert_not_called() 