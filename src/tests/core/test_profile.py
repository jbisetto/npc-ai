"""
Tests for NPC Profile System

This module contains tests for the NPCProfile and ProfileLoader classes.
"""

import pytest
from pathlib import Path
from src.ai.npc.core.profile.profile import NPCProfile, NPCProfileRegistry
from src.ai.npc.core.profile.profile_loader import ProfileLoader
from src.tests.utils.fs_helpers import create_temp_json_file, cleanup_test_files

# Test data
SAMPLE_PROFILE_DATA = {
    "profile_id": "test_npc",
    "name": "Test NPC",
    "role": "Test Role",
    "personality_traits": {
        "friendliness": 0.8,
        "helpfulness": 0.9
    },
    "knowledge_areas": ["testing", "programming"],
    "backstory": "A test NPC for testing purposes.",
    "extends": ["base_japanese_npc"],
    "response_formats": {
        "default": "{name}: {response}",
        "greeting": "Hello! {name} here: {response}"
    }
}

@pytest.fixture
def sample_profile():
    """Create a sample NPCProfile instance."""
    return NPCProfile(
        profile_id="test_npc",
        name="Test NPC",
        role="Test Role",
        personality_traits={"friendliness": 0.8, "helpfulness": 0.9},
        knowledge_areas=["testing", "programming"],
        backstory="A test NPC for testing purposes."
    )

@pytest.fixture
def profile_loader(tmp_path):
    """Create a ProfileLoader instance with a temporary directory."""
    # Create a temporary profiles directory
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    
    # Create a base profile using fs_helpers
    base_profile = {
        "profile_id": "base_japanese_npc",
        "name": "Base NPC",
        "role": "Base Role",
        "personality_traits": {
            "formality": 0.7
        },
        "knowledge_areas": ["japanese"],
        "backstory": "A base NPC profile."
    }
    
    create_temp_json_file(base_profile, profiles_dir, "base_japanese_npc.json")
    
    return ProfileLoader(str(profiles_dir))

@pytest.fixture(autouse=True)
def cleanup():
    """Clean up test files after each test."""
    yield
    cleanup_test_files()

# NPCProfile Tests
def test_profile_creation(sample_profile):
    """Test basic profile creation."""
    assert sample_profile.profile_id == "test_npc"
    assert sample_profile.name == "Test NPC"
    assert sample_profile.role == "Test Role"
    assert sample_profile.personality_traits == {"friendliness": 0.8, "helpfulness": 0.9}
    assert sample_profile.knowledge_areas == ["testing", "programming"]
    assert sample_profile.backstory == "A test NPC for testing purposes."

def test_profile_from_dict():
    """Test creating profile from dictionary."""
    profile = NPCProfile.from_dict(SAMPLE_PROFILE_DATA)
    assert profile.profile_id == SAMPLE_PROFILE_DATA["profile_id"]
    assert profile.name == SAMPLE_PROFILE_DATA["name"]
    assert profile.role == SAMPLE_PROFILE_DATA["role"]
    assert profile.personality_traits == SAMPLE_PROFILE_DATA["personality_traits"]
    assert profile.knowledge_areas == SAMPLE_PROFILE_DATA["knowledge_areas"]
    assert profile.backstory == SAMPLE_PROFILE_DATA["backstory"]
    assert profile.extends == SAMPLE_PROFILE_DATA["extends"]
    assert profile.response_formats == SAMPLE_PROFILE_DATA["response_formats"]

def test_profile_to_dict(sample_profile):
    """Test converting profile to dictionary."""
    profile_dict = sample_profile.to_dict()
    assert profile_dict["profile_id"] == sample_profile.profile_id
    assert profile_dict["name"] == sample_profile.name
    assert profile_dict["role"] == sample_profile.role
    assert profile_dict["personality_traits"] == sample_profile.personality_traits
    assert profile_dict["knowledge_areas"] == sample_profile.knowledge_areas
    assert profile_dict["backstory"] == sample_profile.backstory
    assert "response_formats" in profile_dict

def test_get_system_prompt(sample_profile):
    """Test system prompt generation."""
    prompt = sample_profile.get_system_prompt()
    assert "Test NPC" in prompt
    assert "Test Role" in prompt
    assert "A test NPC for testing purposes" in prompt
    assert "friendliness: 0.8" in prompt
    assert "helpfulness: 0.9" in prompt
    assert "testing, programming" in prompt

def test_format_response(sample_profile):
    """Test response formatting."""
    response = "Hello there!"
    formatted = sample_profile.format_response(response)
    assert formatted == "Test NPC: Hello there!"

def test_get_personality_trait(sample_profile):
    """Test getting personality trait values."""
    assert sample_profile.get_personality_trait("friendliness") == 0.8
    assert sample_profile.get_personality_trait("helpfulness") == 0.9
    assert sample_profile.get_personality_trait("nonexistent") == 0.5  # Default value

# ProfileLoader Tests
def test_profile_loader_initialization(profile_loader):
    """Test profile loader initialization."""
    assert len(profile_loader.base_profiles) == 1
    assert "base_japanese_npc" in profile_loader.base_profiles

def test_load_profile(profile_loader):
    """Test loading a concrete profile."""
    # Create a concrete profile that extends the base profile
    concrete_profile = {
        "profile_id": "concrete_npc",
        "name": "Concrete NPC",
        "role": "Concrete Role",
        "personality_traits": {
            "friendliness": 0.8
        },
        "knowledge_areas": ["english"],
        "backstory": "A concrete NPC profile.",
        "extends": ["base_japanese_npc"]
    }
    
    # Save the profile using fs_helpers
    create_temp_json_file(concrete_profile, Path(profile_loader.profiles_directory), "concrete_npc.json")
    
    # Load the profile
    profile_loader._load_profile(profile_loader.profiles_directory + "/concrete_npc.json")
    
    # Check that the profile was loaded and inheritance was applied
    assert "concrete_npc" in profile_loader.profiles
    loaded_profile = profile_loader.profiles["concrete_npc"]
    assert loaded_profile["name"] == "Concrete NPC"
    assert loaded_profile["role"] == "Concrete Role"
    assert "formality" in loaded_profile["personality_traits"]  # Inherited from base
    assert "japanese" in loaded_profile["knowledge_areas"]  # Inherited from base
    assert "english" in loaded_profile["knowledge_areas"]  # From concrete profile

def test_get_profile(profile_loader):
    """Test getting a profile by ID."""
    # Create and load a profile using fs_helpers
    profile_data = {
        "profile_id": "test_profile",
        "name": "Test Profile",
        "role": "Test Role",
        "personality_traits": {"friendliness": 0.8},
        "knowledge_areas": ["testing"],
        "backstory": "Test profile"
    }
    
    create_temp_json_file(profile_data, Path(profile_loader.profiles_directory), "test_profile.json")
    profile_loader._load_profile(profile_loader.profiles_directory + "/test_profile.json")
    
    # Test getting as dictionary
    profile_dict = profile_loader.get_profile("test_profile")
    assert profile_dict is not None
    assert profile_dict["name"] == "Test Profile"
    
    # Test getting as object
    profile_obj = profile_loader.get_profile("test_profile", as_object=True)
    assert profile_obj is not None
    assert isinstance(profile_obj, NPCProfile)
    assert profile_obj.name == "Test Profile" 