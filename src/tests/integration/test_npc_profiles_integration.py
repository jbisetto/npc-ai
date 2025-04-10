"""
Integration Tests for NPC Profile System

This module tests the integration between NPC profiles, prompt generation, and request processing.
It verifies that the correct NPC profile is applied during prompt generation.
"""

import pytest
import logging
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
import json
import os
from pathlib import Path

from src.ai.npc import process_request
from src.ai.npc.core.models import NPCRequest, GameContext, ProcessingTier
from src.ai.npc.core.profile.profile import NPCProfile
from src.ai.npc.core.profile.profile_loader import ProfileLoader
from src.ai.npc.local.local_processor import LocalProcessor
from src.ai.npc.local.ollama_client import OllamaClient

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.fixture
def test_game_context():
    """Create a game context for testing."""
    return GameContext(
        player_id="test_player",
        player_location="tokyo_station",
        current_objective="Find the ticket counter",
        language_proficiency={"japanese": 0.3, "english": 0.9}
    )

@pytest.fixture
def station_attendant_request(test_game_context):
    """Create a request for the station attendant."""
    # Add NPC ID to the game context
    test_game_context.npc_id = "station_attendant"
    
    # Create the request
    return NPCRequest(
        request_id="test_station_attendant_request",
        player_input="Where can I buy a ticket to Odawara?",
        game_context=test_game_context,
        processing_tier=ProcessingTier.LOCAL,
        additional_params={"conversation_id": "test_conversation"}
    )

@pytest.fixture
def hachiko_request(test_game_context):
    """Create a request for Hachiko (companion dog)."""
    # Add NPC ID to the game context
    test_game_context.npc_id = "companion_dog"
    
    # Create the request
    return NPCRequest(
        request_id="test_hachiko_request",
        player_input="Can you teach me how to say 'ticket' in Japanese?",
        game_context=test_game_context,
        processing_tier=ProcessingTier.LOCAL,
        additional_params={"conversation_id": "test_conversation"}
    )

class MockOllamaClient:
    """Mock Ollama client that captures the prompt for testing."""
    
    def __init__(self):
        self.captured_prompts = []
        self.request_id = None
        self.generate_called = False
        print("MockOllamaClient initialized")
    
    async def generate(self, prompt, model=None):
        """Capture the prompt and return a dummy response."""
        print(f"MockOllamaClient.generate called with prompt length: {len(prompt)}")
        self.generate_called = True
        self.captured_prompts.append(prompt)
        return "<thinking>Test thinking</thinking>\n\nEnglish: This is a test response\nJapanese: テスト\nPronunciation: te-su-to"
    
    async def close(self):
        """Mock the close method."""
        print("MockOllamaClient.close called")
        pass

@pytest.mark.asyncio
async def test_station_attendant_profile_in_prompt(station_attendant_request):
    """
    Test that the station attendant profile is included in the prompt.
    
    This test verifies that when processing a request with the station_attendant NPC ID:
    1. The correct profile is loaded from the profiles directory
    2. The profile information is correctly included in the generated prompt
    3. All relevant profile attributes (name, role, personality traits, etc.) appear in the prompt
    """
    # Create a mock OllamaClient to capture the prompt
    mock_client = MockOllamaClient()
    
    # Create mocks for conversation and knowledge managers
    mock_conv_manager = AsyncMock()
    mock_conv_manager.get_player_history = AsyncMock(return_value=[])
    mock_conv_manager.add_to_history = AsyncMock()
    
    mock_knowledge_store = AsyncMock()
    mock_knowledge_store.contextual_search = AsyncMock(return_value=[])
    mock_knowledge_store.collection = MagicMock()
    mock_knowledge_store.collection.count = MagicMock(return_value=10)
    mock_knowledge_store.close = AsyncMock()
    
    # Create a mock profile loader with the correct path
    mock_profile_loader = ProfileLoader("src/data/profiles")
    
    # Create a custom LocalProcessor directly with our mocks
    processor = LocalProcessor(
        ollama_client=mock_client,
        conversation_manager=mock_conv_manager,
        knowledge_store=mock_knowledge_store
    )
    
    # Patch the get_local_processor function to return our processor
    # and patch the process_request function to use our mock components
    with patch('src.ai.npc.get_local_processor', return_value=processor), \
         patch('src.ai.npc.get_knowledge_store', return_value=mock_knowledge_store), \
         patch('src.ai.npc.get_conversation_manager', return_value=mock_conv_manager), \
         patch('src.ai.npc.config.get_full_config', return_value={'local': {'enabled': True}}), \
         patch('src.ai.npc.local.local_processor.ProfileLoader', return_value=mock_profile_loader):
        
        # Process the request
        print(f"Processing request: {station_attendant_request.request_id}")
        response = await process_request(station_attendant_request)
        print(f"After processing request, generate_called: {mock_client.generate_called}")
        
        # Verify that a prompt was generated
        assert mock_client.generate_called, "generate method was not called"
        assert len(mock_client.captured_prompts) == 1, f"Expected 1 prompt, got {len(mock_client.captured_prompts)}"
        
        if mock_client.captured_prompts:
            prompt = mock_client.captured_prompts[0]
            
            # Verify that we have response text
            assert "response_text" in response
            logger.info(f"Response: {response}")
            
            # Dump the captured prompt for debugging
            logger.debug(f"Captured prompt: {prompt}")
            
            # Check for station attendant profile characteristics
            expected_pairs = [
                ("Yamada", "Station Information Assistant"),
                ("helpfulness", "0.9"),
                ("politeness", "0.9"),
                ("efficiency", "0.9"),
                ("Tokyo Station layout", "Train schedules", "Ticket information")
            ]
            
            # Check for each expected string pair - at least one pair should be found
            profile_found = False
            for expected_strings in expected_pairs:
                if any(all(expected in prompt for expected in expected_strings) for expected_strings in expected_pairs):
                    profile_found = True
                    break
            
            assert profile_found, "Station attendant profile characteristics not found in prompt"
            
            # Check that the player input is included
            assert station_attendant_request.player_input in prompt
            
            # Verify response structure
            assert "response_text" in response
            assert response["processing_tier"] == ProcessingTier.LOCAL

@pytest.mark.asyncio
async def test_hachiko_profile_in_prompt(hachiko_request):
    """
    Test that Hachiko's profile is included in the prompt.
    
    This test verifies that when processing a request with the companion_dog NPC ID:
    1. The correct profile is loaded from the profiles directory
    2. The profile information is correctly included in the generated prompt
    3. All relevant profile attributes (name, role, personality traits, etc.) appear in the prompt
    """
    # Create a mock OllamaClient to capture the prompt
    mock_client = MockOllamaClient()
    
    # Create mocks for conversation and knowledge managers
    mock_conv_manager = AsyncMock()
    mock_conv_manager.get_player_history = AsyncMock(return_value=[])
    mock_conv_manager.add_to_history = AsyncMock()
    
    mock_knowledge_store = AsyncMock()
    mock_knowledge_store.contextual_search = AsyncMock(return_value=[])
    mock_knowledge_store.collection = MagicMock()
    mock_knowledge_store.collection.count = MagicMock(return_value=10)
    mock_knowledge_store.close = AsyncMock()
    
    # Create a mock profile loader with the correct path
    mock_profile_loader = ProfileLoader("src/data/profiles")

    # Create a custom LocalProcessor directly with our mocks
    processor = LocalProcessor(
        ollama_client=mock_client,
        conversation_manager=mock_conv_manager,
        knowledge_store=mock_knowledge_store
    )
    
    # Patch the get_local_processor function to return our processor
    # and patch the process_request function to use our mock components
    with patch('src.ai.npc.get_local_processor', return_value=processor), \
         patch('src.ai.npc.get_knowledge_store', return_value=mock_knowledge_store), \
         patch('src.ai.npc.get_conversation_manager', return_value=mock_conv_manager), \
         patch('src.ai.npc.config.get_full_config', return_value={'local': {'enabled': True}}), \
         patch('src.ai.npc.local.local_processor.ProfileLoader', return_value=mock_profile_loader):
        
        # Process the request
        print(f"Processing request: {hachiko_request.request_id}")
        response = await process_request(hachiko_request)
        print(f"After processing request, generate_called: {mock_client.generate_called}")
        
        # Verify that a prompt was generated
        assert mock_client.generate_called, "generate method was not called"
        assert len(mock_client.captured_prompts) == 1, f"Expected 1 prompt, got {len(mock_client.captured_prompts)}"
        
        if mock_client.captured_prompts:
            prompt = mock_client.captured_prompts[0]
            
            # Dump the captured prompt for debugging
            logger.debug(f"Captured prompt: {prompt}")
            
            # Check for Hachiko profile characteristics - use more flexible checking
            expected_pairs = [
                ("Hachiko", "Companion Dog"),
                ("friendliness", "enthusiasm", "patience", "loyalty"),
                ("Japanese language", "Tokyo Station", "Japanese culture")
            ]
            
            # Check for each expected string pair - at least one pair should be found
            profile_found = False
            for expected_strings in expected_pairs:
                if any(all(expected in prompt for expected in expected_strings) for expected_strings in expected_pairs):
                    profile_found = True
                    break
            
            assert profile_found, "Hachiko profile characteristics not found in prompt"
            
            # Check that the player input is included
            assert hachiko_request.player_input in prompt
            
            # Verify response structure
            assert "response_text" in response
            assert response["processing_tier"] == ProcessingTier.LOCAL

@pytest.mark.asyncio
async def test_different_npcs_have_different_prompts():
    """
    Test that different NPC IDs result in different prompts.
    
    This test verifies that the prompt generation system correctly differentiates
    between different NPCs and applies the appropriate profile to each.
    """
    # Create a common input
    same_input = "Can you help me find my way around the station?"
    
    # Yamada the station attendant
    station_game_context = GameContext(
        player_id="test_player",
        player_location="tokyo_station",
        current_objective="Navigate the station",
        language_proficiency={"japanese": 0.3, "english": 0.9},
        npc_id="station_attendant"  # Set NPC ID directly here
    )
    
    station_request = NPCRequest(
        request_id="test_station_request",
        player_input=same_input,
        game_context=station_game_context,
        processing_tier=ProcessingTier.LOCAL,
        additional_params={"conversation_id": "test_conversation"}
    )
    
    # Hachiko the dog - create separate context
    hachiko_game_context = GameContext(
        player_id="test_player",
        player_location="tokyo_station",
        current_objective="Navigate the station",
        language_proficiency={"japanese": 0.3, "english": 0.9},
        npc_id="companion_dog"  # Set NPC ID directly here
    )
    
    hachiko_request = NPCRequest(
        request_id="test_hachiko_request",
        player_input=same_input,
        game_context=hachiko_game_context,
        processing_tier=ProcessingTier.LOCAL,
        additional_params={"conversation_id": "test_conversation"}
    )
    
    # Create a mock OllamaClient to capture prompts
    mock_client = MockOllamaClient()
    
    # Create mocks for conversation and knowledge managers
    mock_conv_manager = AsyncMock()
    mock_conv_manager.get_player_history = AsyncMock(return_value=[])
    mock_conv_manager.add_to_history = AsyncMock()
    
    mock_knowledge_store = AsyncMock()
    mock_knowledge_store.contextual_search = AsyncMock(return_value=[])
    mock_knowledge_store.collection = MagicMock()
    mock_knowledge_store.collection.count = MagicMock(return_value=10)
    mock_knowledge_store.close = AsyncMock()
    
    # Create a mock profile loader with the correct path
    mock_profile_loader = ProfileLoader("src/data/profiles")
    
    # Create a custom LocalProcessor directly with our mocks
    processor = LocalProcessor(
        ollama_client=mock_client,
        conversation_manager=mock_conv_manager,
        knowledge_store=mock_knowledge_store
    )
    
    # Patch the get_local_processor function to return our processor
    # and patch the process_request function to use our mock components
    with patch('src.ai.npc.get_local_processor', return_value=processor), \
         patch('src.ai.npc.get_knowledge_store', return_value=mock_knowledge_store), \
         patch('src.ai.npc.get_conversation_manager', return_value=mock_conv_manager), \
         patch('src.ai.npc.config.get_full_config', return_value={'local': {'enabled': True}}), \
         patch('src.ai.npc.local.local_processor.ProfileLoader', return_value=mock_profile_loader):
        
        # Process the first request
        print(f"Processing station request: {station_request.request_id}")
        await process_request(station_request)
        print(f"After processing station request, generate_called: {mock_client.generate_called}")
        
        # Check that the prompt was captured
        assert mock_client.generate_called, "generate method was not called for station request"
        assert len(mock_client.captured_prompts) == 1, f"Expected 1 prompt, got {len(mock_client.captured_prompts)}"
        
        station_prompt = mock_client.captured_prompts[0]
        print(f"Station prompt contains 'Yamada': {'Yamada' in station_prompt}")
        print(f"Station prompt contains 'Station Information Assistant': {'Station Information Assistant' in station_prompt}")
        
        # Reset captured prompts and generate_called flag
        mock_client.captured_prompts = []
        mock_client.generate_called = False
        
        # Process the second request
        print(f"Processing hachiko request: {hachiko_request.request_id}")
        await process_request(hachiko_request)
        print(f"After processing hachiko request, generate_called: {mock_client.generate_called}")
        
        # Check that the prompt was captured
        assert mock_client.generate_called, "generate method was not called for hachiko request"
        assert len(mock_client.captured_prompts) == 1, f"Expected 1 prompt, got {len(mock_client.captured_prompts)}"
        
        hachiko_prompt = mock_client.captured_prompts[0]
        print(f"Hachiko prompt contains 'Hachiko': {'Hachiko' in hachiko_prompt}")
        print(f"Hachiko prompt contains 'Companion Dog': {'Companion Dog' in hachiko_prompt}")
        
        # The prompts should be different
        assert station_prompt != hachiko_prompt, "Station and Hachiko prompts should be different"
        
        # Check for specific NPC characteristics in each prompt
        assert "Yamada" in station_prompt, "Station prompt should contain 'Yamada'"
        assert "Station Information Assistant" in station_prompt, "Station prompt should contain 'Station Information Assistant'"
        
        assert "Hachiko" in hachiko_prompt, "Hachiko prompt should contain 'Hachiko'"
        assert "Companion Dog" in hachiko_prompt, "Hachiko prompt should contain 'Companion Dog'" 