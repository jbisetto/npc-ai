"""
Prompt Manager

This module provides unified prompt management functionality for both local and hosted LLMs.
It handles prompt creation, optimization, and token management.
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any

from src.ai.npc.core.models import ClassifiedRequest, CompanionRequest
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
            max_prompt_tokens: Maximum number of tokens to allow in a prompt
        """
        self.max_prompt_tokens = max_prompt_tokens
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
        # Start with base system prompt
        prompt_parts = [BASE_SYSTEM_PROMPT]

        # Add NPC profile if available
        if profile:
            profile_context = "NPC Profile:\n" + profile.get_prompt_context()
            prompt_parts.append(profile_context)

        # Add conversation history if available
        if history:
            history_text = "Previous conversation:\n"
            for entry in history:
                if 'user' in entry:
                    history_text += f"Human: {entry['user']}\n"
                if 'assistant' in entry:
                    history_text += f"Assistant: {entry['assistant']}\n"
            prompt_parts.append(history_text)

        # Add game context if available
        if request.game_context:
            context_text = self._format_game_context(request.game_context)
            prompt_parts.append(context_text)

        # Add current request
        prompt_parts.append(f"Human: {request.player_input}\nAssistant:")

        # Combine all parts
        full_prompt = "\n\n".join(prompt_parts)

        # Optimize the prompt if needed
        if self.estimate_tokens(full_prompt) > self.max_prompt_tokens:
            return self._optimize_prompt(full_prompt, request.player_input)

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

    def _optimize_prompt(self, full_prompt: str, player_input: str) -> str:
        """
        Optimize a prompt to fit within token limits while preserving critical information.
        
        Args:
            full_prompt: The full prompt to optimize
            player_input: The player's input to preserve
            
        Returns:
            An optimized prompt
        """
        # First try compressing the text
        compressed = self._compress_text(full_prompt)
        
        # If still too long, we need to truncate while preserving critical parts
        if self.estimate_tokens(compressed) > self.max_prompt_tokens:
            # Reserve tokens for the player input and essential instructions
            reserved_tokens = self.estimate_tokens(player_input) + 200  # 200 tokens for essential instructions
            available_tokens = max(100, self.max_prompt_tokens - reserved_tokens)
            
            # Get the essential parts (first part of system prompt and player input)
            essential_parts = [
                self._truncate_to_tokens(BASE_SYSTEM_PROMPT.split("\n\n")[0], available_tokens),
                f"Human: {player_input}\nAssistant:"
            ]
            
            return "\n\n".join(essential_parts)
            
        return compressed

    def _compress_text(self, text: str) -> str:
        """
        Compress text by removing unnecessary words and characters.
        
        Args:
            text: The text to compress
            
        Returns:
            Compressed text
        """
        # Remove redundant spaces
        compressed = re.sub(r'\s+', ' ', text).strip()
        
        # Remove filler words
        filler_words = [
            r'\bvery\b', r'\breally\b', r'\bquite\b', r'\bjust\b', 
            r'\bsimply\b', r'\bbasically\b', r'\bactually\b'
        ]
        for word in filler_words:
            compressed = re.sub(word, '', compressed)
        
        # Simplify common phrases
        replacements = {
            'in order to': 'to',
            'due to the fact that': 'because',
            'for the purpose of': 'for',
            'in the event that': 'if',
            'in the process of': 'while',
            'a large number of': 'many',
            'a majority of': 'most',
            'a significant number of': 'many'
        }
        
        for phrase, replacement in replacements.items():
            compressed = compressed.replace(phrase, replacement)
        
        return compressed

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

    def _format_game_context(self, context: Dict[str, Any]) -> str:
        """Format the game context information."""
        context_str = "Current game context:\n"
        
        if context.get('player_location'):
            context_str += f"- Player location: {context['player_location']}\n"
        
        if context.get('language_proficiency'):
            context_str += "- Language proficiency:\n"
            for lang, level in context['language_proficiency'].items():
                context_str += f"  - {lang}: {level}\n"
        
        return context_str 