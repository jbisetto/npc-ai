"""
Profile Loader

This module provides functionality for loading and managing NPC profiles,
supporting profile inheritance and conversion to NPCProfile objects.
"""

import os
import json
import logging
import copy
from typing import Dict, Any, Optional, List, Set
from pathlib import Path

# Import the NPCProfile class
from src.ai.npc.core.profile.profile import NPCProfile

logger = logging.getLogger(__name__)


class ProfileLoader:
    """
    Loads and manages NPC profiles from JSON files.
    
    This class handles loading individual NPC profiles and base profiles,
    managing profile inheritance, and converting profile data to
    NPCProfile objects as needed.
    """
    
    def __init__(self, profiles_directory: str):
        """
        Initialize the profile loader.
        
        Args:
            profiles_directory: Path to directory containing profile JSON files
        """
        self.profiles_directory = profiles_directory
        self.base_profiles = {}  # Stores base profiles that can be extended
        self.profiles = {}  # Stores concrete NPC profiles
        
        # Load all profiles
        self._load_all_profiles()
        
        logger.debug(f"Loaded {len(self.base_profiles)} base profiles and {len(self.profiles)} NPC profiles")
    
    def _load_all_profiles(self):
        """
        Load all profile files from the profiles directory.
        
        First loads all base profiles (files starting with "base_"),
        then loads all concrete profiles, applying inheritance as needed.
        """
        if not os.path.exists(self.profiles_directory):
            logger.warning(f"Profiles directory not found: {self.profiles_directory}")
            return
        
        # First, load all base profiles
        for filename in os.listdir(self.profiles_directory):
            if filename.startswith("base_") and filename.endswith(".json"):
                filepath = os.path.join(self.profiles_directory, filename)
                self._load_base_profile(filepath)
        
        # Then, load all concrete profiles
        for filename in os.listdir(self.profiles_directory):
            if not filename.startswith("base_") and filename.endswith(".json"):
                filepath = os.path.join(self.profiles_directory, filename)
                self._load_profile(filepath)
    
    def _load_base_profile(self, file_path: str):
        """
        Load a base profile from a JSON file.
        
        Args:
            file_path: Path to the base profile JSON file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
                profile_id = profile_data.get("profile_id")
                
                if not profile_id:
                    logger.warning(f"Base profile missing profile_id: {file_path}")
                    return
                
                self.base_profiles[profile_id] = profile_data
                logger.debug(f"Loaded base profile: {profile_id}")
                
        except Exception as e:
            logger.error(f"Error loading base profile from {file_path}: {e}")
    
    def _load_profile(self, file_path: str):
        """
        Load a concrete profile from a JSON file and apply inheritance.
        
        Args:
            file_path: Path to the profile JSON file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
                profile_id = profile_data.get("profile_id")
                
                if not profile_id:
                    logger.warning(f"Profile missing profile_id: {file_path}")
                    return
                
                # Apply inheritance if this profile extends base profiles
                profile_data = self._apply_inheritance(profile_data)
                
                self.profiles[profile_id] = profile_data
                logger.debug(f"Loaded and processed profile: {profile_id}")
                
        except Exception as e:
            logger.error(f"Error loading profile from {file_path}: {e}")
    
    def _apply_inheritance(self, profile: Dict[str, Any], visited: Optional[Set[str]] = None) -> Dict[str, Any]:
        """
        Apply inheritance by merging in fields from base profiles.
        
        Args:
            profile: The profile to apply inheritance to
            visited: Set of already visited profile IDs (for circular inheritance detection)
            
        Returns:
            The profile with inherited fields applied
        """
        # Initialize visited set if not provided
        if visited is None:
            visited = set()
        
        # Check for extends field
        extends = profile.get("extends", [])
        if not extends:
            return profile
        
        # Create a deep copy of the profile to work with
        result = copy.deepcopy(profile)
        
        # Process each base profile in order
        for base_id in extends:
            # Check for circular inheritance
            if base_id in visited:
                raise RecursionError(f"Circular inheritance detected for profile: {profile.get('profile_id')}")
            
            # Skip if base profile doesn't exist
            if base_id not in self.base_profiles:
                logger.warning(f"Base profile not found: {base_id}")
                continue
            
            # Get the base profile, applying its own inheritance first
            base_profile = copy.deepcopy(self.base_profiles[base_id])
            if base_profile.get("extends"):
                new_visited = visited.copy()
                new_visited.add(profile.get("profile_id", ""))
                base_profile = self._apply_inheritance(base_profile, new_visited)
            
            # Merge fields from base profile into result
            result = self._merge_profiles(base_profile, result)
        
        return result
    
    def _merge_profiles(self, base: Dict[str, Any], child: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge fields from a base profile into a child profile.
        
        Child fields override base fields when both exist, except for
        certain fields like knowledge_areas which are combined.
        
        Args:
            base: The base profile to inherit from
            child: The child profile to inherit into
            
        Returns:
            The merged profile
        """
        result = copy.deepcopy(child)
        
        # Don't override these fields
        non_inheritable = {"profile_id", "name", "role", "extends"}
        
        # Special handling for different field types
        for key, value in base.items():
            # Skip non-inheritable fields
            if key in non_inheritable:
                continue
            
            # If child doesn't have this field, copy from base
            if key not in result:
                result[key] = copy.deepcopy(value)
                continue
            
            # Special handling for dictionaries (deep merge)
            if isinstance(value, dict) and isinstance(result[key], dict):
                for k, v in value.items():
                    if k not in result[key]:
                        result[key][k] = copy.deepcopy(v)
            
            # Special handling for lists (append items)
            elif isinstance(value, list) and isinstance(result[key], list):
                # For knowledge_areas and similar fields, combine without duplicates
                if key in {"knowledge_areas"}:
                    existing = set(result[key])
                    for item in value:
                        if item not in existing:
                            result[key].append(item)
                            existing.add(item)
        
        return result
    
    def get_profile(self, profile_id: str, as_object: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get a profile by its ID.
        
        Args:
            profile_id: The ID of the profile to get
            as_object: If True, return an NPCProfile object instead of a dict
            
        Returns:
            The profile dict, NPCProfile object, or None if not found
        """
        profile = self.profiles.get(profile_id)
        if not profile:
            logger.warning(f"Profile not found: {profile_id}")
            return None
        
        if as_object:
            return NPCProfile.from_dict(profile)
        
        return profile
        
    def get_knowledge_areas_with_sources(self, profile_id: str) -> List[Dict[str, str]]:
        """
        Get knowledge areas with their source profiles for a given profile.
        
        Args:
            profile_id: The ID of the profile to get knowledge areas for
            
        Returns:
            List of dictionaries with 'area' and 'source' keys
        """
        profile = self.profiles.get(profile_id)
        if not profile:
            logger.warning(f"Profile not found: {profile_id}")
            return []
            
        # Get base knowledge areas
        base_knowledge = {}
        extends = profile.get("extends", [])
        
        # Process immediate base profiles
        for base_id in extends:
            base_profile = self.base_profiles.get(base_id)
            if not base_profile:
                continue
                
            # Get knowledge areas from this base profile
            for area in base_profile.get("knowledge_areas", []):
                if area not in base_knowledge:
                    base_knowledge[area] = base_id
            
            # Also check if this base profile extends other base profiles
            self._add_inherited_knowledge_areas(base_profile, base_knowledge, base_id)
        
        # Combine with profile's own knowledge areas
        result = []
        for area in profile.get("knowledge_areas", []):
            if area in base_knowledge:
                result.append({
                    "area": area,
                    "source": base_knowledge[area]
                })
            else:
                result.append({
                    "area": area,
                    "source": "original"
                })
                
        return result
        
    def _add_inherited_knowledge_areas(self, profile, knowledge_dict, direct_source):
        """
        Helper method to recursively add knowledge areas from base profiles.
        
        Args:
            profile: The profile to get inherited knowledge areas from
            knowledge_dict: Dictionary to add knowledge areas to
            direct_source: The direct source profile that inherits from others
        """
        # Check if this profile extends other profiles
        extends = profile.get("extends", [])
        if not extends:
            return
            
        for base_id in extends:
            base_profile = self.base_profiles.get(base_id)
            if not base_profile:
                continue
                
            # Add knowledge areas, marking as inherited through direct_source
            for area in base_profile.get("knowledge_areas", []):
                if area not in knowledge_dict:
                    knowledge_dict[area] = f"{direct_source} (from {base_id})"
            
            # Recursively add from deeper base profiles
            self._add_inherited_knowledge_areas(base_profile, knowledge_dict, direct_source) 