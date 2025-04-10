"""
NPC Profile System

This module provides the NPCProfile class for managing NPC personalities and behavior.
"""

from typing import Dict, List, Any, Optional
import json
import random
from pathlib import Path
from src.ai.npc.core.constants import (
    METADATA_KEY_INTENT,
    INTENT_DEFAULT,
    RESPONSE_FORMAT_DEFAULT,
    RESPONSE_FORMAT_GREETING
)
import logging

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
        response_formats: Optional[Dict[str, str]] = None,
        language_profile: Optional[Dict[str, Any]] = None
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
            response_formats: Optional dictionary of response format templates
            language_profile: Optional language settings including default_language
        """
        self.profile_id = profile_id
        self.name = name
        self.role = role
        self.personality_traits = personality_traits
        self.knowledge_areas = knowledge_areas
        self.backstory = backstory
        self.extends = extends or []
        self.response_formats = response_formats or {
            RESPONSE_FORMAT_DEFAULT: "{name}: {response}",
            RESPONSE_FORMAT_GREETING: "Hello! {name} here: {response}"
        }
        self.language_profile = language_profile or {
            "default_language": "english"
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
            response_formats=data.get("response_formats"),
            language_profile=data.get("language_profile")
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
            "response_formats": self.response_formats,
            "language_profile": self.language_profile
        }
    
    def get_system_prompt(self) -> str:
        """Generate the system prompt for this NPC.
        
        Returns:
            System prompt string
        """
        logger = logging.getLogger(__name__)
        
        prompt = f"""You are {self.name}, a {self.role}. {self.backstory}

Your personality traits are:
"""
        for trait, value in self.personality_traits.items():
            prompt += f"- {trait}: {value}\n"
            
        prompt += f"\nYou are knowledgeable about: {', '.join(self.knowledge_areas)}"
        
        # Add language instructions if available
        default_language = self.language_profile.get("default_language") if self.language_profile else None
        
        # Debug logging
        logger.info(f"[LANGUAGE DEBUG] Profile {self.name}, language_profile: {self.language_profile}")
        logger.info(f"[LANGUAGE DEBUG] Default language: {default_language}")
        
        if default_language:
            if default_language == "japanese":
                logger.info(f"[LANGUAGE DEBUG] Adding Japanese language instructions")
                prompt += f"\n\nIMPORTANT: You must ONLY respond in Japanese. If you understand the user's input, respond in Japanese only. If you cannot understand the input at all, you may briefly explain in English that you don't understand, and then suggest they try in Japanese."
            elif default_language == "english":
                logger.info(f"[LANGUAGE DEBUG] Adding English language instructions")
                prompt += f"\n\nIMPORTANT: You must ONLY respond in English. If the user speaks to you in another language and you understand it, always respond in English only."
            elif default_language == "bilingual":
                # Enhanced instructions for language instructors
                role_is_instructor = "instructor" in self.role.lower() or "teacher" in self.role.lower() or "learning" in self.role.lower()
                
                logger.info(f"[LANGUAGE DEBUG] Bilingual mode, role_is_instructor: {role_is_instructor}, role: {self.role}")
                
                if role_is_instructor:
                    logger.info(f"[LANGUAGE DEBUG] Adding enhanced bilingual language instructions for instructor")
                    prompt += f"""

IMPORTANT LANGUAGE INSTRUCTIONS:
You are a language instructor who should help users learn Japanese. Use a bilingual approach:
1. If the user speaks in English:
   - Respond primarily in Japanese with English translations in parentheses
   - Start with simple Japanese phrases then gradually introduce more complex ones
   - Include helpful explanations about grammar or vocabulary in English

2. If the user speaks in Japanese:
   - Respond primarily in Japanese with some English support as needed
   - Compliment their Japanese and gently correct any mistakes
   - Provide English translations for advanced words or grammar points

3. Always adjust to the user's perceived language level:
   - Use JLPT N5 level Japanese for beginners
   - If they seem more advanced, gradually increase complexity

4. Format your responses with Japanese first, followed by English translation when appropriate:
   「こんにちは！何かお手伝いできますか？」(Hello! How can I help you?)

IMPORTANT: You should respond in the same language the user addresses you in. If they speak Japanese, respond in Japanese. If they speak English, respond in English.
"""
                else:
                    # Standard bilingual instructions for non-instructors
                    logger.info(f"[LANGUAGE DEBUG] Adding standard bilingual language instructions")
                    prompt += f"\n\nIMPORTANT: You should respond in the same language the user addresses you in. If they speak Japanese, respond in Japanese. If they speak English, respond in English."
        
        return prompt
    
    def format_response(self, response: str, request: Optional[Dict[str, Any]] = None) -> str:
        """
        Format a response based on the request's intent.
        
        Args:
            response: The response to format
            request: Optional request data containing intent and other metadata
            
        Returns:
            The formatted response
        """
        if not response:
            return ""
            
        # Get the intent from request metadata
        intent = INTENT_DEFAULT
        if request and isinstance(request, dict):
            intent = request.get(METADATA_KEY_INTENT, INTENT_DEFAULT)
            
        # Get the appropriate format template
        format_key = f"response_format_{intent.lower()}"
        format_template = self.response_formats.get(format_key, self.response_formats[RESPONSE_FORMAT_DEFAULT])
        
        # Format the response using the template
        try:
            return format_template.format(name=self.name, response=response)
        except KeyError:
            # If template formatting fails, return the response as is
            return response
    
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