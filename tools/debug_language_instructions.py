#!/usr/bin/env python3
"""
Debug script to print the language instructions in NPC prompts.
"""

import os
import sys
import re

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ai.npc.core.models import NPCRequest, GameContext
from src.ai.npc.core.prompt_manager import PromptManager
from src.ai.npc.core.profile.profile_loader import ProfileLoader

# Initialize components
# Use absolute path to profiles directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILES_DIR = os.path.join(PROJECT_ROOT, "src/data/profiles")
profile_loader = ProfileLoader(PROFILES_DIR)
prompt_manager = PromptManager(max_prompt_tokens=800)

def create_and_analyze_prompt(npc_id, player_input="Where is the ticket counter?"):
    """Create a prompt for the specified NPC and analyze its language instructions."""
    print(f"\n====== Testing NPC ID: {npc_id} ======")
    
    # Create game context with default values
    game_context = GameContext(
        player_id="test_player",
        language_proficiency={"japanese": 0.3, "english": 0.9},
        player_location="Tokyo Station",
        npc_id=npc_id
    )
    
    # Create request
    request = NPCRequest(
        request_id="test_request",
        player_input=player_input,
        game_context=game_context
    )
    
    # Load profile
    profile = profile_loader.get_profile(npc_id, as_object=True)
    if not profile:
        print(f"Profile not found: {npc_id}")
        return
    
    print(f"Profile name: {profile.name}")
    print(f"Profile role: {profile.role}")
    
    # Print language profile info
    if hasattr(profile, 'language_profile') and profile.language_profile:
        print(f"Language profile: {profile.language_profile}")
    else:
        print("No language profile found")
    
    # Generate prompt
    prompt = prompt_manager.create_prompt(
        request=request,
        profile=profile
    )
    
    # Look for language instructions with more flexible matching
    print("\nLooking for language instructions...")
    
    # List of patterns to look for
    patterns = [
        "IMPORTANT: You must ONLY respond in Japanese",
        "IMPORTANT: You must ONLY respond in English",
        "IMPORTANT: You should respond in the same language",
        "IMPORTANT LANGUAGE INSTRUCTIONS",
        "language instructor who should help",
        "bilingual approach"
    ]
    
    language_section_found = False
    for pattern in patterns:
        if pattern in prompt:
            language_section_found = True
            print(f"✓ Found language pattern: '{pattern}'")
            
            # Extract context around the pattern
            start_idx = prompt.find(pattern)
            context_start = max(0, start_idx - 20)
            context_end = min(len(prompt), start_idx + 400)  # Show more context for better analysis
            context = prompt[context_start:context_end]
            print(f"Context around this pattern:\n{context}\n")
    
    if not language_section_found:
        print("✗ No language instructions found in prompt")
        
    # Always print the full prompt for debugging
    print("\n=== FULL PROMPT ===")
    print(prompt)
    print("=== END PROMPT ===\n")
    
    return profile, prompt

def main():
    """Main entry point."""
    # Test specific Japanese NPCs
    create_and_analyze_prompt("base_japanese_npc")
    
    # Test with other NPCs
    create_and_analyze_prompt("companion_dog")  # Hachiko should be bilingual
    
    # Test a real NPC for which we're seeing issues
    if len(sys.argv) > 1:
        npc_id = sys.argv[1]
        create_and_analyze_prompt(npc_id)

if __name__ == "__main__":
    main() 