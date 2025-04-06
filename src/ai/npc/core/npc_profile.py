"""
NPC Profile

This module provides a placeholder for the NPCProfile class.
Future implementation will include full NPC personality and behavior configuration.
"""

from typing import Dict, Any, Optional


class NPCProfile:
    """
    Placeholder for NPC Profile functionality.
    Currently provides minimal interface required by other components.
    """
    
    def __init__(self, profile_id: str, name: str = "Station Assistant"):
        self.profile_id = profile_id
        self.name = name
        self.personality_traits: Dict[str, float] = {
            "formality": 0.5,
            "friendliness": 0.8,
            "helpfulness": 0.9
        }
        self.response_format: Dict[str, str] = {}
    
    def get_response_format(self, intent: Any) -> str:
        """Placeholder for response format retrieval."""
        return self.response_format.get(str(intent), "")
    
    def format_response(self, response: str, request: Any, emotion: str = "neutral") -> str:
        """Placeholder for response formatting."""
        return f"{self.name}: {response}"
    
    def get_personality_trait(self, trait: str) -> float:
        """Get a personality trait value."""
        return self.personality_traits.get(trait, 0.5) 