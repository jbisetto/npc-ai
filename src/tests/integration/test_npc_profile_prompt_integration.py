"""
Integration Tests for NPC Profile Usage in Prompts

This module tests the end-to-end integration of NPC profiles into prompt generation,
verifying that when an NPC ID is specified in a request, the corresponding profile
information is properly incorporated into the generated prompt.
"""

import pytest
import logging
import os
from unittest.mock import patch, MagicMock, AsyncMock
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

# Create mock profile data
HACHIKO_PROFILE = {
    "profile_id": "companion_dog",
    "name": "Hachiko",
    "role": "Companion Dog",
    "personality_traits": {
        "friendliness": 0.9,
        "enthusiasm": 0.8,
        "patience": 1.0,
        "playfulness": 0.7,
        "loyalty": 1.0
    },
    "knowledge_areas": [
        "Japanese language basics",
        "Tokyo Station",
        "Japanese culture",
        "Daily life in Japan"
    ],
    "backstory": "Hachiko is a friendly AI dog companion stationed at Tokyo Station."
}

STATION_ATTENDANT_PROFILE = {
    "profile_id": "station_attendant",
    "name": "Yamada",
    "role": "Station Information Assistant",
    "personality_traits": {
        "helpfulness": 0.9,
        "patience": 0.9,
        "efficiency": 0.9,
        "politeness": 0.9,
        "friendliness": 0.7
    },
    "knowledge_areas": [
        "Tokyo Station layout",
        "Train schedules",
        "Ticket information",
        "Station facilities",
        "Emergency procedures",
        "Local attractions"
    ],
    "backstory": "Yamada is a dedicated station attendant at Tokyo Station."
}

@pytest.fixture
def mock_profile_loader():
    """Create a mocked profile loader with predefined profiles."""
    loader = MagicMock(spec=ProfileLoader)
    
    # Setup the profiles dictionary
    loader.profiles = {
        "companion_dog": HACHIKO_PROFILE,
        "station_attendant": STATION_ATTENDANT_PROFILE
    }
    
    # Setup the get_profile method
    def get_profile_mock(profile_id, as_object=False):
        profile_data = loader.profiles.get(profile_id)
        if not profile_data:
            return None
        if as_object:
            return NPCProfile.from_dict(profile_data)
        return profile_data
    
    loader.get_profile.side_effect = get_profile_mock
    
    return loader

@pytest.fixture
def available_profile_ids(mock_profile_loader):
    """Get a list of available profile IDs."""
    return list(mock_profile_loader.profiles.keys())

@pytest.mark.asyncio
async def test_profile_included_in_prompt(available_profile_ids, mock_profile_loader):
    """
    Test that when a request specifies an NPC ID, the corresponding profile
    is loaded and included in the generated prompt.
    """
    # Skip if no profiles are available
    if not available_profile_ids:
        pytest.skip("No profiles available for testing")
    
    # Use the first available profile
    profile_id = available_profile_ids[0]
    
    # Create a mock OllamaClient to capture the generated prompt
    mock_client = MagicMock()
    mock_client.generate = AsyncMock(return_value="This is a test response")
    mock_client.close = AsyncMock()
    
    # Create mocks for conversation and knowledge stores
    mock_conv_manager = AsyncMock()
    mock_conv_manager.get_player_history = AsyncMock(return_value=[])
    mock_conv_manager.add_to_history = AsyncMock()
    
    mock_knowledge_store = AsyncMock()
    mock_knowledge_store.contextual_search = AsyncMock(return_value=[])
    mock_knowledge_store.collection = MagicMock()
    mock_knowledge_store.collection.count = MagicMock(return_value=0)
    
    # Create a local processor with our mocks
    mock_processor = LocalProcessor(
        ollama_client=mock_client,
        conversation_manager=mock_conv_manager,
        knowledge_store=mock_knowledge_store
    )
    mock_processor.process = AsyncMock()
    
    # Patch the profile_registry
    mock_processor.profile_registry = mock_profile_loader
    
    # Create a request with the selected profile ID
    game_context = GameContext(
        player_id="test_player",
        player_location="tokyo_station",
        current_objective="Find the ticket counter",
        language_proficiency={"japanese": 0.3, "english": 0.9},
        npc_id=profile_id
    )
    
    request = NPCRequest(
        request_id="test_request",
        player_input="Can you help me find the Shinkansen platform?",
        game_context=game_context,
        processing_tier=ProcessingTier.LOCAL,
        additional_params={"conversation_id": "test_conversation"}
    )
    
    # Patch necessary components
    with patch('src.ai.npc._local_processor', mock_processor), \
         patch('src.ai.npc.config.get_full_config', return_value={'local': {'enabled': True}}):
        
        # Process the request
        await process_request(request)
        
        # Verify that process was called
        mock_processor.process.assert_called_once_with(request)
        
        # Now directly test with a non-mocked processor
        # Create a real processor but with our mock client
        real_processor = LocalProcessor(
            ollama_client=mock_client,
            conversation_manager=mock_conv_manager,
            knowledge_store=mock_knowledge_store
        )
        
        # Patch the profile_registry on the real processor
        real_processor.profile_registry = mock_profile_loader
        
        # Process the request directly
        await real_processor.process(request)
        
        # Verify that the client's generate method was called
        mock_client.generate.assert_called_once()
        
        # Get the generated prompt
        generated_prompt = mock_client.generate.call_args[0][0]
        
        # Get the profile to check
        profile = mock_profile_loader.get_profile(profile_id, as_object=True)
        
        # Verify profile details in prompt
        assert profile.name in generated_prompt, f"Profile name '{profile.name}' not found in prompt"
        assert profile.role in generated_prompt, f"Profile role '{profile.role}' not found in prompt"
        
        # Check for personality traits
        for trait in profile.personality_traits.keys():
            assert trait in generated_prompt, f"Personality trait '{trait}' not found in prompt"
        
        # Check for knowledge areas
        for area in profile.knowledge_areas:
            assert area in generated_prompt, f"Knowledge area '{area}' not found in prompt"

@pytest.mark.asyncio
async def test_different_profiles_produce_different_prompts(available_profile_ids, mock_profile_loader):
    """
    Test that different NPC IDs result in different prompts with profile-specific content.
    """
    # Skip if we don't have at least two profiles
    if len(available_profile_ids) < 2:
        pytest.skip("Need at least two profiles for comparison testing")
    
    # Take two different profiles
    profile_id_1 = available_profile_ids[0]
    profile_id_2 = available_profile_ids[1]
    
    # Create a mock OllamaClient that captures prompts
    mock_client = MagicMock()
    prompts = []
    
    # Side effect to capture prompts
    def capture_prompt(prompt):
        prompts.append(prompt)
        return "This is a test response"
    
    mock_client.generate = AsyncMock(side_effect=capture_prompt)
    mock_client.close = AsyncMock()
    
    # Create common mocks
    mock_conv_manager = AsyncMock()
    mock_conv_manager.get_player_history = AsyncMock(return_value=[])
    
    mock_knowledge_store = AsyncMock()
    mock_knowledge_store.contextual_search = AsyncMock(return_value=[])
    mock_knowledge_store.collection = MagicMock()
    mock_knowledge_store.collection.count = MagicMock(return_value=0)
    
    # Create processor
    processor = LocalProcessor(
        ollama_client=mock_client,
        conversation_manager=mock_conv_manager,
        knowledge_store=mock_knowledge_store
    )
    
    # Patch the profile_registry
    processor.profile_registry = mock_profile_loader
    
    # Create and process first request
    game_context_1 = GameContext(
        player_id="test_player",
        language_proficiency={"english": 0.9, "japanese": 0.5},
        npc_id=profile_id_1 
    )
    
    request_1 = NPCRequest(
        request_id="test_1",
        player_input="Can you help me find my way?",
        game_context=game_context_1,
        processing_tier=ProcessingTier.LOCAL
    )
    
    await processor.process(request_1)
    
    # Create and process second request
    game_context_2 = GameContext(
        player_id="test_player",
        language_proficiency={"english": 0.9, "japanese": 0.5},
        npc_id=profile_id_2
    )
    
    request_2 = NPCRequest(
        request_id="test_2",
        player_input="Can you help me find my way?",  # Same input
        game_context=game_context_2,
        processing_tier=ProcessingTier.LOCAL
    )
    
    await processor.process(request_2)
    
    # Verify we captured two prompts
    assert len(prompts) == 2, "Failed to generate prompts for both profiles"
    
    # Verify the prompts are different
    assert prompts[0] != prompts[1], "Prompts are identical despite different profiles"
    
    # Get the profiles for verification
    profile_1 = mock_profile_loader.get_profile(profile_id_1, as_object=True)
    profile_2 = mock_profile_loader.get_profile(profile_id_2, as_object=True)
    
    # Verify each prompt contains profile-specific information
    assert profile_1.name in prompts[0], f"Profile 1 name not found in first prompt"
    assert profile_1.role in prompts[0], f"Profile 1 role not found in first prompt"
    
    assert profile_2.name in prompts[1], f"Profile 2 name not found in second prompt"
    assert profile_2.role in prompts[1], f"Profile 2 role not found in second prompt"
    
    # Check for cross-contamination (unless names are substrings)
    if profile_1.name not in profile_2.name and profile_2.name not in profile_1.name:
        assert profile_1.name not in prompts[1], "Profile 1 name incorrectly found in Profile 2's prompt"
        assert profile_2.name not in prompts[0], "Profile 2 name incorrectly found in Profile 1's prompt" 