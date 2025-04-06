"""
Prompt Manager

This module provides unified prompt management functionality for both local and hosted LLMs.
It handles prompt creation, optimization, and token management.
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any

from src.ai.npc.core.models import ClassifiedRequest, CompanionRequest, GameContext
from src.ai.npc.core.npc_profile import NPCProfile

# Set up logging
logger = logging.getLogger(__name__)

# Token estimation constants
AVG_CHARS_PER_TOKEN = 4  # Approximate average characters per token

# Base system prompt with JLPT N5 constraints
BASE_SYSTEM_PROMPT = """You are Hachiko, a helpful bilingual dog companion in a Japanese train station.
Your role is to assist the player with language help, directions, and cultural information.

CRITICAL RESPONSE CONSTRAINTS:
1. Length: Keep responses under 3 sentences
2. Language Level: Strictly JLPT N5 vocabulary and grammar only
3. Format: Always include both Japanese and English
4. Style: Simple, friendly, and encouraging

JLPT N5 GUIDELINES:
- Use only basic particles: は, が, を, に, で, へ
- Basic verbs: います, あります, いきます, みます
- Simple adjectives: いい, おおきい, ちいさい
- Common nouns: でんしゃ, えき, きっぷ
- Basic greetings: こんにちは, すみません

RESPONSE STRUCTURE:
1. English answer (1 sentence)
2. Japanese phrase (with hiragana)
3. Quick pronunciation guide"""

class PromptManager:
    """
    Unified prompt management for both local and hosted LLMs.
    Handles prompt creation, optimization, and token management.
    """
    
    def __init__(self, max_prompt_tokens: int = 800):
        """
        Initialize the prompt manager.
        
        Args:
            max_prompt_tokens: Maximum number of tokens to allow in a prompt.
                             If <= 0, uses default value of 800.
        """
        self.max_prompt_tokens = 800 if max_prompt_tokens <= 0 else max_prompt_tokens
        self.logger = logging.getLogger(__name__)
    
    def create_prompt(
        self,
        request: ClassifiedRequest,
        history: Optional[List[Dict[str, Any]]] = None,
        profile: Optional[NPCProfile] = None
    ) -> str:
        """
        Create an optimized prompt for the language model.

        Args:
            request: The classified request
            history: Optional conversation history
            profile: Optional NPC profile to use

        Returns:
            The formatted and optimized prompt string
        """
        # For very small token limits, use minimal format
        if self.max_prompt_tokens <= 100:
            minimal_prompt = (
                "You are Hachiko, a helpful bilingual dog companion.\n"
                "RULES:\n"
                "1. Keep responses short\n"
                "2. Use JLPT N5 only\n"
                "3. Include Japanese and English\n\n"
                f"Human: {request.player_input}\nAssistant:"
            )
            return minimal_prompt

        # Build full prompt
        prompt_parts = [BASE_SYSTEM_PROMPT]

        # Add NPC profile if available
        if profile:
            try:
                profile_context = profile.get_prompt_context()
                if profile_context and profile_context.strip():
                    prompt_parts.append("NPC Profile:\n" + profile_context)
            except Exception as e:
                self.logger.warning(f"Failed to get profile context: {e}")

        # Add conversation history if available
        if history:
            history_entries = []
            for entry in history:
                # Only include entries that have both user and assistant messages
                user_msg = entry.get('user', '').strip()
                assistant_msg = entry.get('assistant', '').strip()
                if user_msg and assistant_msg:
                    history_entries.append(f"Human: {user_msg}")
                    history_entries.append(f"Assistant: {assistant_msg}")
            
            if history_entries:
                prompt_parts.append("Previous conversation:\n" + "\n".join(history_entries))

        # Add game context if available
        if request.game_context:
            context_text = self._format_game_context(request.game_context)
            if context_text.strip():  # Only add if not empty
                prompt_parts.append(context_text)

        # Add current request
        prompt_parts.append(f"Human: {request.player_input}\nAssistant:")

        # Combine all parts
        full_prompt = "\n\n".join(filter(None, prompt_parts))

        # Check if we need to optimize
        if self.estimate_tokens(full_prompt) > self.max_prompt_tokens:
            return self._optimize_prompt(full_prompt)

        return full_prompt

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text string.
        
        Args:
            text: The text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        return max(1, len(text) // AVG_CHARS_PER_TOKEN)

    def _optimize_prompt(self, prompt: str) -> str:
        """
        Optimize a prompt to fit within token limits while preserving critical information.
        
        Args:
            prompt: The prompt to optimize
            
        Returns:
            An optimized prompt
        """
        # If prompt is too long, truncate it while preserving the essential parts
        if self.estimate_tokens(prompt) > self.max_prompt_tokens:
            # Get the essential parts (first part of system prompt and player input)
            system_part = self._truncate_to_tokens(BASE_SYSTEM_PROMPT.split("\n\n")[0], self.max_prompt_tokens // 2)
            
            # Extract the player input
            input_start = prompt.rfind("Human: ")
            player_input = prompt[input_start:] if input_start != -1 else ""
            
            # Combine the parts
            return f"{system_part}\n\n{player_input}"
        
        return prompt

    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limits.
        
        Args:
            text: The text to truncate
            max_tokens: Maximum number of tokens
            
        Returns:
            Truncated text
        """
        max_chars = max_tokens * AVG_CHARS_PER_TOKEN
        
        if len(text) <= max_chars:
            return text
        
        # Try to truncate at sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        result = ""
        
        for sentence in sentences:
            if self.estimate_tokens(result + sentence + " ") <= max_tokens:
                result += sentence + " "
            else:
                break
        
        # If we couldn't fit even one sentence, truncate mid-sentence
        if not result:
            result = text[:max_chars]
            
        return result.strip()

    def _format_game_context(self, context: GameContext) -> str:
        """Format the game context information."""
        context_str = "Current game context:\n"
        
        # Add player ID
        context_str += f"- Player ID: {context.player_id}\n"
        
        # Add language proficiency if available
        if context.language_proficiency:
            context_str += "- Language Proficiency:\n"
            for lang, level in context.language_proficiency.items():
                context_str += f"  - {lang}: {level}\n"
        
        return context_str

    def _build_full_prompt(self, request: ClassifiedRequest) -> str:
        """Build the full prompt with all available context."""
        prompt_parts = [BASE_SYSTEM_PROMPT]

        # Add game context if available
        if request.game_context:
            context_text = self._format_game_context(request.game_context)
            if context_text.strip():  # Only add if not empty
                prompt_parts.append(context_text)

        # Add current request
        prompt_parts.append(f"Human: {request.player_input}\nAssistant:")

        # Combine all parts
        return "\n\n".join(filter(None, prompt_parts))