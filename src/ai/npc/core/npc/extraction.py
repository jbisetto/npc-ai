"""
Utilities for extracting NPC profiles from existing components.

This module provides functions to extract NPC profiles from existing components
that have hardcoded personality information, allowing for a smoother transition
to the profile-based system.
"""

import logging
from typing import Dict, Any, List

from src.ai.npc.core.response_formatter import ResponseFormatter
from src.ai.npc.core.npc.profile import NPCProfile

logger = logging.getLogger(__name__)


def extract_companion_profile(formatter: ResponseFormatter) -> NPCProfile:
    """
    Extract a companion profile from a ResponseFormatter.
    
    This function creates an NPCProfile for Hachi the companion dog based on
    the personality traits and expressions defined in the ResponseFormatter.
    
    Args:
        formatter: The ResponseFormatter to extract from
        
    Returns:
        An NPCProfile for Hachi
    """
    # Extract personality traits
    personality_traits = formatter.DEFAULT_PERSONALITY.copy()
    
    # Extract emotion expressions
    emotion_expressions = {}
    for emotion, expressions in formatter.EMOTION_EXPRESSIONS.items():
        emotion_expressions[emotion] = expressions.copy()
    
    # Create speech patterns
    speech_patterns = {
        "formality_level": "casual",
        "speaking_style": "enthusiastic",
        "common_phrases": [
            "Woof! I'm here to help!",
            "Let me sniff out the answer for you!",
            "I'm pawsitively sure about this!",
            "You're doing great!",
            "I'm so happy to help you with your Japanese!",
            "Don't worry, I'll guide you through this!",
            "Remember, making mistakes is part of learning!"
        ]
    }
    
    # Define knowledge areas
    knowledge_areas = [
        "japanese_language",
        "tokyo_station",
        "train_system",
        "cultural_tips",
        "vocabulary",
        "grammar",
        "travel_advice"
    ]
    
    # Create backstory
    backstory = """
    Hachi is a magical talking Shiba Inu who serves as a companion and guide for travelers 
    at Tokyo Station. With an extensive knowledge of Japanese language and culture, 
    Hachi helps visitors navigate the station, learn useful phrases, and understand 
    cultural nuances. Friendly and enthusiastic, Hachi is especially patient with 
    language learners and always ready to offer a helpful bark of encouragement.
    """.strip()
    
    # Create visual traits
    visual_traits = {
        "breed": "Shiba Inu",
        "color": "Reddish brown with white chest",
        "size": "Medium",
        "accessories": "Red bandana with Tokyo Station logo",
        "appearance": "Fluffy with perky ears and a curled tail"
    }
    
    # Create the profile
    profile = NPCProfile(
        profile_id="companion_dog",
        name="Hachi",
        role="Companion Dog",
        personality_traits=personality_traits,
        speech_patterns=speech_patterns,
        knowledge_areas=knowledge_areas,
        backstory=backstory,
        visual_traits=visual_traits,
        emotion_expressions=emotion_expressions
    )
    
    logger.info(f"Created companion profile: {profile.name} ({profile.profile_id})")
    return profile 