"""
Integration Tests for NPC Profile Usage in Prompts

This module ensures that NPC profiles are correctly integrated into the prompt building process,
verifying that:
1. Different NPC profiles result in appropriately different prompts
2. Profile properties (personality, name, role) appear correctly in generated prompts
3. The prompt manager correctly incorporates profile data into the final prompt
"""

import pytest
import logging
from unittest.mock import patch, MagicMock, AsyncMock
import json
import os
from pathlib import Path

from src.ai.npc.core.models import NPCRequest, GameContext, ProcessingTier, ClassifiedRequest
from src.ai.npc.core.profile.profile import NPCProfile, NPCProfileRegistry
from src.ai.npc.core.prompt_manager import PromptManager
from src.ai.npc.local.local_processor import LocalProcessor
from src.ai.npc.local.ollama_client import OllamaClient
from src.ai.npc.core.profile.profile_loader import ProfileLoader

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.fixture
def profile_loader():
    """Create a ProfileLoader instance for testing."""
    profiles_dir = os.path.join(Path(__file__).resolve().parent.parent.parent, "data", "profiles")
    return ProfileLoader(profiles_dir)

class TestNPCProfilesInPrompts:
    """Test suite for verifying NPC profile integration into prompts."""
    
    @pytest.fixture
    def prompt_manager(self):
        """Create a prompt manager for testing."""
        return PromptManager(max_prompt_tokens=1000)
    
    @pytest.fixture
    def station_attendant_profile(self):
        """Create a station attendant profile for testing."""
        return NPCProfile(
            profile_id="station_attendant",
            name="Yamada",
            role="Station Information Assistant",
            personality_traits={
                "helpfulness": 0.9,
                "patience": 0.8,
                "efficiency": 0.9,
                "politeness": 0.9
            },
            knowledge_areas=[
                "Tokyo Station layout",
                "Train schedules",
                "Ticket information",
                "Station facilities"
            ],
            backstory="A knowledgeable station staff member dedicated to helping travelers.",
            response_formats={
                "default": "{name}: {response}"
            },
            language_profile={
                "default_language": "japanese",
                "japanese_level": "native",
                "speech_patterns": [
                    "Polite formal speech",
                    "Clear pronunciation",
                    "Standard Tokyo dialect"
                ]
            }
        )
    
    @pytest.fixture
    def hachiko_profile(self):
        """Create a Hachiko profile for testing."""
        return NPCProfile(
            profile_id="companion_dog",
            name="Hachiko",
            role="Companion Dog",
            personality_traits={
                "friendliness": 0.95,
                "loyalty": 0.99,
                "enthusiasm": 0.85,
                "helpfulness": 0.9
            },
            knowledge_areas=[
                "Japanese language basics",
                "Tokyo Station layout",
                "Japanese culture",
                "Tourist information"
            ],
            backstory="A friendly Akita dog who helps tourists navigate Tokyo Station and learn basic Japanese.",
            response_formats={
                "default": "{name}: {response}"
            },
            language_profile={
                "default_language": "bilingual",
                "japanese_level": "N1",
                "speech_patterns": [
                    "Enthusiastic and friendly tone",
                    "Clear pronunciation for learners",
                    "Educational explanations"
                ]
            }
        )
    
    @pytest.fixture
    def game_context(self):
        """Create a game context for testing."""
        return GameContext(
            player_id="test_player",
            player_location="tokyo_station",
            current_objective="Find the ticket counter",
            language_proficiency={"japanese": 0.3, "english": 0.9}
        )
    
    @pytest.fixture
    def basic_request(self, game_context):
        """Create a basic request that can be used with different NPCs."""
        return ClassifiedRequest(
            request_id="test_request",
            player_input="Where can I buy a ticket to Kyoto?",
            game_context=game_context,
            processing_tier=ProcessingTier.LOCAL,
            additional_params={
                "conversation_id": "test_conversation"
            }
        )
    
    def test_different_profiles_produce_different_prompts(self, 
                                                          prompt_manager, 
                                                          station_attendant_profile, 
                                                          hachiko_profile, 
                                                          basic_request):
        """Test that different NPC profiles result in different prompts."""
        # Generate prompts with different profiles
        attendant_prompt = prompt_manager.create_prompt(
            request=basic_request,
            profile=station_attendant_profile
        )
        
        hachiko_prompt = prompt_manager.create_prompt(
            request=basic_request,
            profile=hachiko_profile
        )
        
        # Verify the prompts are different
        assert attendant_prompt != hachiko_prompt
        
        # Check for profile-specific content in each prompt
        assert "Yamada" in attendant_prompt
        assert "Station Information Assistant" in attendant_prompt
        assert "knowledgeable station staff member" in attendant_prompt
        
        assert "Hachiko" in hachiko_prompt
        assert "Companion Dog" in hachiko_prompt
        assert "friendly Akita dog" in hachiko_prompt
    
    def test_profile_attributes_appear_in_prompt(self, prompt_manager, station_attendant_profile, basic_request):
        """Test that all important profile attributes appear in the generated prompt."""
        # Generate prompt
        prompt = prompt_manager.create_prompt(
            request=basic_request,
            profile=station_attendant_profile
        )
        
        # Check that all important profile attributes appear in the prompt
        # Name and role
        assert station_attendant_profile.name in prompt
        assert station_attendant_profile.role in prompt
        
        # Personality traits
        for trait, value in station_attendant_profile.personality_traits.items():
            assert trait in prompt
            assert str(value) in prompt
        
        # Knowledge areas
        for area in station_attendant_profile.knowledge_areas:
            assert area in prompt
        
        # Backstory
        assert station_attendant_profile.backstory in prompt
    
    def test_prompt_manager_formats_profile_correctly(self, prompt_manager, hachiko_profile, basic_request):
        """Test that the prompt manager formats the profile correctly in the prompt."""
        # Generate prompt
        prompt = prompt_manager.create_prompt(
            request=basic_request,
            profile=hachiko_profile
        )
        
        # The profile should be formatted as a proper system prompt
        expected_start = f"You are {hachiko_profile.name}, a {hachiko_profile.role}."
        assert prompt.startswith(expected_start)
        
        # Check for structured sections
        assert "Your personality traits are:" in prompt
        
        # Verify the prompt contains both profile information and the user's request
        assert hachiko_profile.backstory in prompt
        assert basic_request.player_input in prompt
    
    @pytest.mark.asyncio
    async def test_local_processor_uses_profile(self, hachiko_profile, game_context):
        """Test that the LocalProcessor correctly uses the profile when processing a request."""
        # Set up a mock Ollama client to capture the prompt
        mock_ollama = MagicMock()
        mock_ollama.generate = AsyncMock(return_value="This is a test response")
        mock_ollama.close = AsyncMock()
        
        # Set up mock conversation manager and knowledge store
        mock_conv_manager = AsyncMock()
        mock_conv_manager.get_player_history = AsyncMock(return_value=[])
        
        mock_knowledge_store = AsyncMock()
        mock_knowledge_store.contextual_search = AsyncMock(return_value=[])
        mock_knowledge_store.collection = MagicMock()
        mock_knowledge_store.collection.count = MagicMock(return_value=0)
        
        # Mock profile registry to return our test profile
        mock_profile_registry = MagicMock()
        mock_profile_registry.get_profile = MagicMock(return_value=hachiko_profile)
        
        # Create a request with NPC ID matching our profile
        game_context.npc_id = hachiko_profile.profile_id
        request = NPCRequest(
            request_id="test_request",
            player_input="Can you help me find the Shinkansen platform?",
            game_context=game_context,
            processing_tier=ProcessingTier.LOCAL,
            additional_params={"conversation_id": "test_conversation"}
        )
        
        # Patch the prompt manager to capture the profile that's used
        original_create_prompt = PromptManager.create_prompt
        
        profile_used = []
        def mock_create_prompt(self, request, history=None, profile=None, knowledge_context=None):
            profile_used.append(profile)
            return original_create_prompt(self, request, history, profile, knowledge_context)
        
        # Use our patched method and create processor
        with patch.object(PromptManager, 'create_prompt', mock_create_prompt):
            processor = LocalProcessor(
                ollama_client=mock_ollama,
                conversation_manager=mock_conv_manager,
                knowledge_store=mock_knowledge_store
            )
            
            # Replace the processor's profile_registry with our mock
            processor.profile_registry = mock_profile_registry
            
            # Process the request
            await processor.process(request)
            
            # Verify the profile was retrieved and used
            mock_profile_registry.get_profile.assert_called_once_with(hachiko_profile.profile_id, as_object=True)
            
            # Verify a profile was used in create_prompt
            assert len(profile_used) > 0
            assert profile_used[0] is not None
            assert profile_used[0].profile_id == hachiko_profile.profile_id
            
    def test_profile_customizes_prompt_for_npc_type(self, prompt_manager, basic_request):
        """Test that different types of NPCs get appropriately customized prompts."""
        # Create profiles for different NPC types
        merchant_profile = NPCProfile(
            profile_id="merchant",
            name="Tanaka",
            role="Souvenir Shop Owner",
            personality_traits={"business_savvy": 0.9, "friendliness": 0.7},
            knowledge_areas=["Japanese souvenirs", "Tourist preferences"],
            backstory="Runs a family souvenir shop in Tokyo Station."
        )
        
        security_profile = NPCProfile(
            profile_id="security",
            name="Officer Sato",
            role="Station Security Guard",
            personality_traits={"vigilance": 0.95, "helpfulness": 0.8, "seriousness": 0.9},
            knowledge_areas=["Station rules", "Security procedures", "Emergency protocols"],
            backstory="A veteran security officer who ensures safety at Tokyo Station."
        )
        
        # Generate prompts for different NPC types
        merchant_prompt = prompt_manager.create_prompt(
            request=basic_request,
            profile=merchant_profile
        )
        
        security_prompt = prompt_manager.create_prompt(
            request=basic_request,
            profile=security_profile
        )
        
        # Verify the prompts contain appropriate role-specific information
        assert "Souvenir Shop Owner" in merchant_prompt
        assert "business_savvy: 0.9" in merchant_prompt
        assert "family souvenir shop" in merchant_prompt
        
        assert "Station Security Guard" in security_prompt
        assert "vigilance: 0.95" in security_prompt
        assert "veteran security officer" in security_prompt
        
        # Ensure prompts are appropriately different
        assert merchant_prompt != security_prompt 

def test_prompt_manager_includes_npc_profile_in_prompt():
    """Test that the prompt manager includes NPC profile information in prompts."""
    # Create a profile
    profile = NPCProfile(
        profile_id="test_npc",
        name="Test NPC",
        role="Test Role",
        personality_traits={"friendly": 0.9, "helpful": 0.8},
        knowledge_areas=["Test Knowledge", "Sample Info"],
        backstory="This is a test NPC for testing."
    )
    
    # Create a request
    game_context = GameContext(
        player_id="test_player",
        npc_id="test_npc",
        language_proficiency={"english": 0.9, "japanese": 0.5}
    )
    
    request = ClassifiedRequest(
        request_id="test_request",
        player_input="Hello there",
        game_context=game_context,
        processing_tier=ProcessingTier.LOCAL
    )
    
    # Create prompt with profile
    prompt_manager = PromptManager()
    prompt = prompt_manager.create_prompt(
        request=request,
        profile=profile
    )
    
    # Verify profile information is in the prompt
    assert profile.name in prompt, f"Profile name not found in prompt"
    assert profile.role in prompt, f"Profile role not found in prompt"
    
    # Check for personality traits
    for trait, value in profile.personality_traits.items():
        assert trait in prompt, f"Personality trait '{trait}' not found in prompt"
        
    # Check for knowledge areas
    for area in profile.knowledge_areas:
        assert area in prompt, f"Knowledge area '{area}' not found in prompt"
    
    # Verify backstory is included
    assert profile.backstory in prompt, f"Backstory not found in prompt"

def test_real_profiles_work_with_prompt_manager(profile_loader):
    """Test that real profiles from the system can be correctly used by the PromptManager."""
    # Get available profile IDs (skip base profiles)
    profile_ids = [pid for pid in profile_loader.profiles.keys() 
                  if not pid.startswith("base_")]
    
    if not profile_ids:
        pytest.skip("No profiles available for testing")
    
    # Use the first available profile
    profile_id = profile_ids[0]
    profile = profile_loader.get_profile(profile_id, as_object=True)
    
    # Create a request
    game_context = GameContext(
        player_id="test_player",
        npc_id=profile_id,
        language_proficiency={"english": 0.9, "japanese": 0.5}
    )
    
    request = ClassifiedRequest(
        request_id="test_request",
        player_input="Hello there",
        game_context=game_context,
        processing_tier=ProcessingTier.LOCAL
    )
    
    # Create prompt with profile
    prompt_manager = PromptManager()
    prompt = prompt_manager.create_prompt(
        request=request,
        profile=profile
    )
    
    # Verify profile information is in the prompt
    assert profile.name in prompt, f"Profile name not found in prompt"
    assert profile.role in prompt, f"Profile role not found in prompt"
    
    # Log the profile details and prompt for inspection
    logger.info(f"Successfully generated prompt using profile: {profile_id}")
    logger.info(f"Profile name: {profile.name}, role: {profile.role}")
    
    # Verify backstory is included
    assert profile.backstory in prompt, f"Backstory not found in prompt"

def test_language_profile_instructions_in_prompt(profile_loader):
    """Test that language_profile configurations produce appropriate language instructions in the prompt."""
    # Create a prompt manager
    prompt_manager = PromptManager()
    
    # Create profiles with different language settings
    japanese_npc = NPCProfile(
        profile_id="japanese_test_npc",
        name="Tanaka",
        role="Station Attendant",
        personality_traits={"politeness": 0.9, "helpfulness": 0.8},
        knowledge_areas=["Train schedules", "Station layout"],
        backstory="A helpful station attendant at Tokyo Station.",
        language_profile={
            "default_language": "japanese",
            "japanese_level": "native"
        }
    )
    
    english_npc = NPCProfile(
        profile_id="english_test_npc",
        name="Smith",
        role="Tourist Guide",
        personality_traits={"friendliness": 0.9, "knowledge": 0.8},
        knowledge_areas=["Tokyo attractions", "Transportation"],
        backstory="An English-speaking guide helping tourists in Tokyo.",
        language_profile={
            "default_language": "english"
        }
    )
    
    bilingual_npc = NPCProfile(
        profile_id="bilingual_test_npc",
        name="Hachiko",
        role="Companion Dog",
        personality_traits={"friendliness": 0.9, "patience": 1.0},
        knowledge_areas=["Japanese basics", "Station layout"],
        backstory="A friendly companion helping tourists learn Japanese.",
        language_profile={
            "default_language": "bilingual",
            "japanese_level": "N1"
        }
    )
    
    # Create a basic game context
    game_context = GameContext(
        player_id="test_player",
        language_proficiency={"japanese": 0.3, "english": 0.9}
    )
    
    # Create a request using the game context
    request = ClassifiedRequest(
        request_id="test_request",
        player_input="Where is the ticket counter?",
        game_context=game_context,
        processing_tier=ProcessingTier.LOCAL
    )
    
    # Generate prompts for each profile
    japanese_prompt = prompt_manager.create_prompt(request=request, profile=japanese_npc)
    english_prompt = prompt_manager.create_prompt(request=request, profile=english_npc)
    bilingual_prompt = prompt_manager.create_prompt(request=request, profile=bilingual_npc)
    
    # Verify language-specific instructions in each prompt
    # Japanese NPC should have instructions to respond only in Japanese
    assert "IMPORTANT: You must ONLY respond in Japanese" in japanese_prompt
    assert "Keep your answers extremely brief with 2 short sentences maximum" in japanese_prompt
    assert "Do not include any English translations" in japanese_prompt
    
    # English NPC should have instructions to respond only in English
    assert "IMPORTANT: You must ONLY respond in English" in english_prompt
    assert "always respond in English only" in english_prompt
    
    # Bilingual NPC should have instructions to respond in the same language as the input
    if "instructor" in bilingual_npc.role.lower() or "teacher" in bilingual_npc.role.lower() or "learning" in bilingual_npc.role.lower():
        # For language instructors, check for new English-first approach
        assert "Respond primarily in English (1 sentence for explanation)" in bilingual_prompt
        assert "Include just 1 relevant Japanese phrase/example" in bilingual_prompt
    else:
        # For regular bilingual NPCs, check for standard bilingual instructions
        assert "IMPORTANT: You should respond in the same language the user addresses you in" in bilingual_prompt
        assert "If they speak Japanese, respond in Japanese" in bilingual_prompt
        assert "If they speak English, respond in English" in bilingual_prompt


def test_language_profile_from_real_profiles(profile_loader):
    """Test that real profiles from the system include language instructions in their prompts."""
    # Get the Japanese NPC base profile
    japanese_npc_profile = profile_loader.get_profile("base_japanese_npc", as_object=True)
    
    # Skip if the profile doesn't exist
    if not japanese_npc_profile:
        pytest.skip("Japanese NPC profile not found")
    
    # Create a prompt manager
    prompt_manager = PromptManager()
    
    # Create a game context
    game_context = GameContext(
        player_id="test_player",
        language_proficiency={"japanese": 0.3, "english": 0.9}
    )
    
    # Create requests with different languages
    english_request = ClassifiedRequest(
        request_id="english_test",
        player_input="Where is the ticket counter?",
        game_context=game_context,
        processing_tier=ProcessingTier.LOCAL
    )
    
    japanese_request = ClassifiedRequest(
        request_id="japanese_test",
        player_input="切符売り場はどこですか？",
        game_context=game_context,
        processing_tier=ProcessingTier.LOCAL
    )
    
    # Generate prompts for each request
    prompt_en = prompt_manager.create_prompt(request=english_request, profile=japanese_npc_profile)
    prompt_ja = prompt_manager.create_prompt(request=japanese_request, profile=japanese_npc_profile)
    
    # Verify Japanese language instructions in both prompts
    assert "IMPORTANT: You must ONLY respond in Japanese" in prompt_en
    assert "Keep your answers extremely brief with 2 short sentences maximum" in prompt_en
    assert "Do not include any English translations" in prompt_en
    
    assert "IMPORTANT: You must ONLY respond in Japanese" in prompt_ja
    assert "Keep your answers extremely brief with 2 short sentences maximum" in prompt_ja
    assert "Do not include any English translations" in prompt_ja
    
    # The prompts should be almost identical except for the user input part
    prompt_en_without_input = prompt_en.replace(english_request.player_input, "")
    prompt_ja_without_input = prompt_ja.replace(japanese_request.player_input, "")
    assert prompt_en_without_input == prompt_ja_without_input
    
    # Check that language profile settings are included
    assert japanese_npc_profile.language_profile["default_language"] == "japanese"

def test_hachiko_bilingual_language_profile(profile_loader):
    """Test that Hachiko's bilingual language profile works correctly."""
    # Get the Hachiko profile
    hachiko_profile = profile_loader.get_profile("companion_dog", as_object=True)
    
    # Skip if the profile doesn't exist
    if not hachiko_profile:
        pytest.skip("Hachiko profile not found")
    
    # Create a prompt manager
    prompt_manager = PromptManager()
    
    # Create a game context
    game_context = GameContext(
        player_id="test_player",
        language_proficiency={"japanese": 0.5, "english": 0.9}
    )
    
    # Create requests in different languages
    english_request = ClassifiedRequest(
        request_id="english_test",
        player_input="Can you help me learn some basic Japanese phrases?",
        game_context=game_context,
        processing_tier=ProcessingTier.LOCAL
    )
    
    japanese_request = ClassifiedRequest(
        request_id="japanese_test",
        player_input="日本語を少し教えてくれませんか？",
        game_context=game_context,
        processing_tier=ProcessingTier.LOCAL
    )
    
    # Generate prompts for each request
    prompt_en = prompt_manager.create_prompt(request=english_request, profile=hachiko_profile)
    prompt_ja = prompt_manager.create_prompt(request=japanese_request, profile=hachiko_profile)
    
    # Verify language instructor instructions for Hachiko
    english_first = "Respond primarily in English (1 sentence for explanation)"
    japanese_example = "Include just 1 relevant Japanese phrase/example"
    
    # Since Hachiko is a Language Learning Assistant, it should have the updated instructor prompts
    assert english_first in prompt_en
    assert japanese_example in prompt_en
    assert english_first in prompt_ja
    assert japanese_example in prompt_ja
    
    # Verify the brevity requirement
    assert "Maximum 2 sentences total" in prompt_en
    assert "Maximum 2 sentences total" in prompt_ja
    
    # Verify the language profile is set to bilingual
    assert hachiko_profile.language_profile["default_language"] == "bilingual"
    
    # Hachiko should have a high Japanese level (N1)
    assert hachiko_profile.language_profile["japanese_level"] == "N1"

def test_language_profile_fallback_for_incomprehensible_input(profile_loader):
    """Test that language profiles include appropriate fallback instructions for when the NPC cannot understand input."""
    # Create a prompt manager
    prompt_manager = PromptManager()
    
    # Create a Japanese NPC profile
    japanese_npc = NPCProfile(
        profile_id="japanese_test_npc",
        name="Tanaka",
        role="Station Attendant",
        personality_traits={"politeness": 0.9, "helpfulness": 0.8},
        knowledge_areas=["Train schedules", "Station layout"],
        backstory="A helpful station attendant at Tokyo Station.",
        language_profile={
            "default_language": "japanese",
            "japanese_level": "native"
        }
    )
    
    # Create a basic game context
    game_context = GameContext(
        player_id="test_player",
        language_proficiency={"japanese": 0.1, "english": 0.9}  # Very low Japanese proficiency
    )
    
    # Create a request
    request = ClassifiedRequest(
        request_id="test_request",
        player_input="Where is the bathroom?",  # Simple English that the NPC might not understand
        game_context=game_context,
        processing_tier=ProcessingTier.LOCAL
    )
    
    # Generate prompt
    prompt = prompt_manager.create_prompt(request=request, profile=japanese_npc)
    
    # Verify fallback instructions are included
    assert "If you cannot understand the input at all, you may briefly explain in Japanese that you don't understand" in prompt
    assert "suggest they try again" in prompt

def test_debug_japanese_npc_language_instructions(profile_loader):
    """Debug test to print the language instructions in a Japanese NPC prompt."""
    # Create a prompt manager
    prompt_manager = PromptManager()
    
    # Create a Japanese NPC profile
    japanese_npc = NPCProfile(
        profile_id="japanese_test_npc",
        name="Tanaka",
        role="Station Attendant",
        personality_traits={"politeness": 0.9, "helpfulness": 0.8},
        knowledge_areas=["Train schedules", "Station layout"],
        backstory="A helpful station attendant at Tokyo Station.",
        language_profile={
            "default_language": "japanese",
            "japanese_level": "native"
        }
    )
    
    # Create a game context
    game_context = GameContext(
        player_id="test_player",
        language_proficiency={"japanese": 0.3, "english": 0.9}
    )
    
    # Create a request
    request = ClassifiedRequest(
        request_id="test_request",
        player_input="Where is the ticket counter?",
        game_context=game_context,
        processing_tier=ProcessingTier.LOCAL
    )
    
    # Generate prompt
    prompt = prompt_manager.create_prompt(request=request, profile=japanese_npc)
    
    # Print important information for debugging
    print("\n============ DEBUG INFO ============")
    print(f"Profile default language: {japanese_npc.language_profile.get('default_language')}")
    
    # Find the language instruction sections
    if "IMPORTANT: You must ONLY respond in Japanese" in prompt:
        print("Found instruction to respond in Japanese ✓")
    else:
        print("Japanese instruction NOT found ✗")
        
    if "Keep your answers extremely brief with 2 short sentences maximum" in prompt:
        print("Found instruction for brevity ✓")
    else:
        print("Brevity instruction NOT found ✗")
    
    if "Do not include any English translations" in prompt:
        print("Found instruction to avoid English translations ✓")
    else:
        print("No English translations instruction NOT found ✗")
    
    # Find the actual language section
    language_section_start = prompt.find("IMPORTANT: You must ONLY respond in")
    if language_section_start != -1:
        # Extract about 100 characters around this point
        start_idx = max(0, language_section_start - 20)
        end_idx = min(len(prompt), language_section_start + 150)
        language_context = prompt[start_idx:end_idx]
        print(f"\nLanguage Context: \n{language_context}\n")
    else:
        print("\nNo language section found")
    
    print("============ END DEBUG ============\n")
    
    # Verify correct language instruction
    assert "IMPORTANT: You must ONLY respond in Japanese" in prompt, "Japanese instruction missing"
    assert "IMPORTANT: You must ONLY respond in English" not in prompt, "English instruction found" 