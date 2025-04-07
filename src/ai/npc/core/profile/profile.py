"""
NPC Profile System

This module provides the NPCProfile class for managing NPC personalities and behavior.
"""

from typing import Dict, List, Any, Optional
import json
import random
from pathlib import Path

class NPCProfile:
    """NPC Profile class for managing NPC personalities and behavior."""
    
    def __init__(
        self,
        profile_id: str,
        name: str,
        role: str,
        personality_traits: Dict[str, float],
        knowledge_areas: List[str],
        backstory: str,
        extends: Optional[List[str]] = None,
        response_format: Optional[Dict[str, str]] = None
    ):
        """Initialize an NPC profile.
        
        Args:
            profile_id: Unique identifier for the profile
            name: NPC's name
            role: NPC's role in the game
            personality_traits: Dictionary of personality traits and their values (0-1)
            knowledge_areas: List of topics this NPC is knowledgeable about
            backstory: NPC's background story
            extends: Optional list of base profile IDs to extend
            response_format: Optional dictionary of intent-specific response formats
        """
        self.profile_id = profile_id
        self.name = name
        self.role = role
        self.personality_traits = personality_traits
        self.knowledge_areas = knowledge_areas
        self.backstory = backstory
        self.extends = extends or []
        self.response_format = response_format or {
            "default": "{name}: {response}"
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NPCProfile":
        """Create an NPCProfile instance from a dictionary.
        
        Args:
            data: Dictionary containing profile data
            
        Returns:
            NPCProfile instance
        """
        return cls(
            profile_id=data["profile_id"],
            name=data["name"],
            role=data["role"],
            personality_traits=data["personality_traits"],
            knowledge_areas=data["knowledge_areas"],
            backstory=data["backstory"],
            extends=data.get("extends"),
            response_format=data.get("response_format")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the profile to a dictionary.
        
        Returns:
            Dictionary containing profile data
        """
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "role": self.role,
            "personality_traits": self.personality_traits,
            "knowledge_areas": self.knowledge_areas,
            "backstory": self.backstory,
            "extends": self.extends,
            "response_format": self.response_format
        }
    
    def get_system_prompt(self) -> str:
        """Generate the system prompt for this NPC.
        
        Returns:
            System prompt string
        """
        prompt = f"""You are {self.name}, a {self.role}. {self.backstory}

Your personality traits are:
"""
        for trait, value in self.personality_traits.items():
            prompt += f"- {trait}: {value}\n"
            
        prompt += f"\nYou are knowledgeable about: {', '.join(self.knowledge_areas)}"
        
        return prompt
    
    def format_response(self, response: str, request: Optional[Dict[str, Any]] = None) -> str:
        """Format a response according to the NPC's personality.
        
        Args:
            response: The response text to format
            request: Optional request data for context
            
        Returns:
            Formatted response string
        """
        # Get the appropriate format based on intent or use default
        intent = request.get("intent") if request else None
        format_str = self.response_format.get(intent, self.response_format["default"])
        
        # Format the response
        return format_str.format(
            name=self.name,
            response=response
        )
    
    def get_personality_trait(self, trait: str) -> float:
        """Get the value of a personality trait.
        
        Args:
            trait: Name of the trait
            
        Returns:
            Trait value between 0 and 1
        """
        return self.personality_traits.get(trait, 0.5)

class NPCProfileRegistry:
    """Registry for managing NPC profiles."""
    
    def __init__(self, profiles_dir: str = "src/data/profiles"):
        """Initialize the registry.
        
        Args:
            profiles_dir: Directory containing profile JSON files
        """
        self.profiles_dir = Path(profiles_dir)
        self.profiles: Dict[str, NPCProfile] = {}
        self._load_profiles()
    
    def _load_profiles(self) -> None:
        """Load all profile files from the profiles directory."""
        for profile_file in self.profiles_dir.glob("*.json"):
            with open(profile_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                profile = NPCProfile.from_dict(data)
                self.profiles[profile.profile_id] = profile
    
    def get_profile(self, profile_id: str) -> Optional[NPCProfile]:
        """Get a profile by ID.
        
        Args:
            profile_id: ID of the profile to get
            
        Returns:
            NPCProfile instance or None if not found
        """
        return self.profiles.get(profile_id)
    
    def get_all_profiles(self) -> List[NPCProfile]:
        """Get all loaded profiles.
        
        Returns:
            List of NPCProfile instances
        """
        return list(self.profiles.values()) 