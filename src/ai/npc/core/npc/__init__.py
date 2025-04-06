"""
NPC module for the Tokyo Train Station Adventure.

This module provides classes for NPC profiles and interactions.
"""

from src.ai.npc.core.npc.profile import NPCProfile, NPCProfileRegistry
from src.ai.npc.core.npc.profile_loader import ProfileLoader

__all__ = ["NPCProfile", "NPCProfileRegistry", "ProfileLoader"] 