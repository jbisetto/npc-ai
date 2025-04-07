"""
NPCProfile system for modular NPC personalities.

This module provides the classes and functionality needed to define and use
different NPC personality profiles within the companion AI system, allowing
for modular and configurable NPC behaviors.
"""

import json
import os
import random
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from src.ai.npc.core.models import ClassifiedRequest

logger = logging.getLogger(__name__)


class NPCProfile:
    """
    Defines a personality profile for an NPC in the game.
    
    This class encapsulates all the personality attributes, speech patterns,
    knowledge areas, and other characteristics that define how an NPC
    behaves and responds to player interactions.
    """
    
    def __init__(
        self,
        profile_id: str,
        name: str,
        role: str,
        personality_traits: Dict[str, float],
        speech_patterns: Dict[str, Any],
        knowledge_areas: List[str],
        backstory: str,
        visual_traits: Dict[str, str] = None,
        emotion_expressions: Dict[str, List[str]] = None,
        response_format: Dict[str, str] = None
    ):
        """
        Initialize an NPC profile.
        
        Args:
            profile_id: Unique identifier for the profile
            name: NPC's name
            role: NPC's role in the game (e.g., "Station Attendant")
            personality_traits: Dict of personality traits with values 0-1
            speech_patterns: Dict with common phrases and speaking style
            knowledge_areas: List of topics this NPC is knowledgeable about
            backstory: NPC's background story
            visual_traits: Optional dict of visual characteristics
            emotion_expressions: Optional dict mapping emotions to expressions
            response_format: Optional dict of intent-specific response formats
        """
        self.profile_id = profile_id
        self.name = name
        self.role = role
        self.personality_traits = personality_traits
        self.speech_patterns = speech_patterns
        self.knowledge_areas = knowledge_areas
        self.backstory = backstory
        self.visual_traits = visual_traits or {}
        self.emotion_expressions = emotion_expressions or {}
        self.response_format = response_format or {}
        
        # Set default emotion expressions if not provided
        if not self.emotion_expressions:
            self._set_default_emotion_expressions()
            
        logger.debug(f"Created NPC profile: {self.profile_id} ({self.name}, {self.role})")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NPCProfile":
        """
        Create an NPCProfile from a dictionary.
        
        Args:
            data: Dictionary containing profile attributes
            
        Returns:
            An NPCProfile instance
        """
        return cls(
            profile_id=data["profile_id"],
            name=data["name"],
            role=data["role"],
            personality_traits=data["personality_traits"],
            speech_patterns=data["speech_patterns"],
            knowledge_areas=data["knowledge_areas"],
            backstory=data["backstory"],
            visual_traits=data.get("visual_traits", {}),
            emotion_expressions=data.get("emotion_expressions", {}),
            response_format=data.get("response_format", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the profile to a dictionary.
        
        Returns:
            Dictionary representation of the profile
        """
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "role": self.role,
            "personality_traits": self.personality_traits,
            "speech_patterns": self.speech_patterns,
            "knowledge_areas": self.knowledge_areas,
            "backstory": self.backstory,
            "visual_traits": self.visual_traits,
            "emotion_expressions": self.emotion_expressions,
            "response_format": self.response_format
        }
    
    def get_system_prompt_additions(self) -> str:
        """
        Get profile-specific additions to system prompts.
        
        This provides context to the LLM about the NPC's personality,
        role, and other characteristics.
        
        Returns:
            String with prompt additions for this profile
        """
        # Construct personality description
        personality_desc = []
        for trait, value in self.personality_traits.items():
            if value > 0.7:
                personality_desc.append(f"very {trait}")
            elif value > 0.4:
                personality_desc.append(f"moderately {trait}")
            else:
                personality_desc.append(f"not very {trait}")
        
        personality_text = ", ".join(personality_desc)
        
        # Create the prompt addition
        prompt = f"""
You are {self.name}, a {self.role} in Tokyo Station. 

About you:
- {self.backstory}
- Your personality is {personality_text}
- You speak in a {self.speech_patterns.get('formality_level', 'neutral')} and {self.speech_patterns.get('speaking_style', 'conversational')} manner
- You are knowledgeable about: {', '.join(self.knowledge_areas)}

Remember to always stay in character and respond as {self.name} would.
"""
        return prompt
    
    def get_response_format(self, request: ClassifiedRequest) -> str:
        """
        Get the response format for the request.
        
        Args:
            request: The classified request
            
        Returns:
            The response format to use
        """
        # Simple response format for now
        return "You are a helpful NPC. Respond naturally to: {input}"
    
    def get_emotion_expression(self, emotion: str) -> str:
        """
        Get a random emotion expression for the specified emotion.
        
        Args:
            emotion: The emotion to express
            
        Returns:
            A string with an appropriate expression, or a fallback if the 
            emotion isn't defined
        """
        if emotion in self.emotion_expressions and self.emotion_expressions[emotion]:
            return random.choice(self.emotion_expressions[emotion])
        
        # Fallback to neutral or any available emotion
        if "neutral" in self.emotion_expressions and self.emotion_expressions["neutral"]:
            return random.choice(self.emotion_expressions["neutral"])
        
        # Last resort fallback
        for expressions in self.emotion_expressions.values():
            if expressions:
                return random.choice(expressions)
        
        # If no expressions are available
        return f"*{self.name} acknowledges*"
    
    def format_response(self, response: str, request: ClassifiedRequest, emotion: str = "neutral") -> str:
        """
        Format a response according to this NPC's personality.
        
        Args:
            response: The raw response text
            request: The classified request being responded to
            emotion: Optional emotion to express
            
        Returns:
            Formatted response with personality elements
        """
        # Get an emotion expression
        emotion_expr = self.get_emotion_expression(emotion)
        
        # Get a common phrase based on the personality traits
        common_phrase = None
        if random.random() < 0.3:  # 30% chance to add a common phrase
            common_phrase = self.get_common_phrase()
        
        # Format the response with personality elements
        formatted = f"{self.name}: {response}"
        
        if emotion_expr:
            if random.random() < 0.5:  # 50% chance to put expression at the end
                formatted += f" {emotion_expr}"
            else:
                formatted = f"{self.name}: {emotion_expr} {response}"
        
        if common_phrase:
            if random.random() < 0.3:  # 30% chance to add at the beginning
                formatted = f"{self.name}: {common_phrase} {response}"
            else:
                formatted += f" {common_phrase}"
        
        return formatted
    
    def get_common_phrase(self) -> str:
        """
        Get a random common phrase used by this NPC.
        
        Returns:
            A common phrase string, or None if no phrases are defined
        """
        phrases = self.speech_patterns.get("common_phrases", [])
        if phrases:
            return random.choice(phrases)
        return None
    
    def has_knowledge_area(self, area: str) -> bool:
        """
        Check if this NPC has knowledge in a specific area.
        
        Args:
            area: The knowledge area to check
            
        Returns:
            True if the NPC has this knowledge area, False otherwise
        """
        return area in self.knowledge_areas
    
    def _set_default_emotion_expressions(self):
        """Set default emotion expressions based on personality traits."""
        # Generic expressions for different formality levels
        formal_expressions = {
            "happy": [
                "I'm pleased to assist you.",
                "*gives a professional smile*",
                "I'm glad I could help."
            ],
            "neutral": [
                "*nods politely*",
                "I understand.",
                "I see."
            ],
            "concerned": [
                "*looks concerned*",
                "I apologize for the inconvenience.",
                "Let me see what I can do about this."
            ]
        }
        
        casual_expressions = {
            "happy": [
                "Great!",
                "*smiles*",
                "That's awesome!"
            ],
            "neutral": [
                "*nods*",
                "Okay.",
                "Got it."
            ],
            "concerned": [
                "*frowns slightly*",
                "Oh, that's not good.",
                "Hmm, that's a problem."
            ]
        }
        
        # Set expressions based on formality level
        formality = self.personality_traits.get("formality", 0.5)
        if formality > 0.6:
            self.emotion_expressions = formal_expressions
        else:
            self.emotion_expressions = casual_expressions


class NPCProfileRegistry:
    """
    Registry for managing NPC profiles.
    
    This class handles loading, storing, and retrieving NPC profiles,
    providing a centralized way to access profiles throughout the system.
    """
    
    def __init__(self, default_profile_id: str = "companion_dog", profiles_directory: str = None):
        """
        Initialize the registry.
        
        Args:
            default_profile_id: ID of the default profile to use when
                                a specific profile is not found
            profiles_directory: Optional path to directory containing profile JSON files.
                                If provided, profiles will be loaded automatically.
        """
        self.profiles = {}
        self.default_profile_id = default_profile_id
        self.profile_loader = None
        
        # If profiles directory is provided, load profiles
        if profiles_directory:
            self.load_profiles_from_directory(profiles_directory)
            
        logger.debug(f"Initialized NPCProfileRegistry with default profile: {default_profile_id}")
    
    def register_profile(self, profile: NPCProfile):
        """
        Register a profile in the registry.
        
        Args:
            profile: The NPCProfile to register
        """
        self.profiles[profile.profile_id] = profile
        logger.debug(f"Registered profile: {profile.profile_id}")
    
    def load_profiles_from_directory(self, directory_path: str):
        """
        Load all profile files from a directory using ProfileLoader.
        
        Args:
            directory_path: Path to directory containing profile JSON files
        """
        from src.ai.npc.core.npc.profile_loader import ProfileLoader
        
        if not os.path.exists(directory_path):
            logger.warning(f"Profile directory not found: {directory_path}")
            return
        
        # Create a ProfileLoader and load profiles
        self.profile_loader = ProfileLoader(directory_path)
        
        # Convert to NPCProfile objects and register them
        loaded_count = 0
        for profile_id in self.profile_loader.profiles:
            try:
                profile = self.profile_loader.get_profile(profile_id, as_object=True)
                self.register_profile(profile)
                loaded_count += 1
            except Exception as e:
                logger.error(f"Error converting profile {profile_id} to NPCProfile: {e}")
        
        logger.info(f"Loaded {loaded_count} profiles from {directory_path}")
    
    def get_profile(self, profile_id: str = None) -> Optional[NPCProfile]:
        """
        Get a profile by ID.
        
        Args:
            profile_id: Optional ID of the profile to get. If None or not found,
                        returns the default profile.
        
        Returns:
            The requested NPCProfile, or the default profile if not found,
            or None if neither are available
        """
        if not profile_id:
            return self.profiles.get(self.default_profile_id)
        
        profile = self.profiles.get(profile_id)
        if not profile:
            logger.warning(f"Profile not found: {profile_id}, using default")
            profile = self.profiles.get(self.default_profile_id)
            
        return profile
    
    def set_default_profile(self, profile_id: str):
        """
        Set the default profile.
        
        Args:
            profile_id: ID of the profile to set as default
        
        Raises:
            ValueError: If the profile doesn't exist
        """
        if profile_id not in self.profiles:
            raise ValueError(f"Cannot set default profile: {profile_id} not found")
        
        self.default_profile_id = profile_id
        logger.debug(f"Set default profile to: {profile_id}") 