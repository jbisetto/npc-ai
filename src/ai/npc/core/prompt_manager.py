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
from src.ai.npc.core.profile.profile import NPCProfile

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
    
    def __init__(self, max_prompt_tokens: int = 800, tier_specific_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the prompt manager.
        
        Args:
            max_prompt_tokens: Maximum number of tokens to allow in a prompt.
                             Must be greater than 0.
            tier_specific_config: Optional configuration specific to the processing tier.
                                For example, {"model_type": "bedrock"} for hosted tier.
                             
        Raises:
            ValueError: If max_prompt_tokens is less than or equal to 0.
        """
        if max_prompt_tokens <= 0:
            raise ValueError("max_prompt_tokens must be greater than 0")
        self.max_prompt_tokens = max_prompt_tokens
        self.tier_specific_config = tier_specific_config or {}
        self.logger = logging.getLogger(__name__)
    
    def create_prompt(
        self,
        request: ClassifiedRequest,
        history: Optional[List[Dict[str, Any]]] = None,
        profile: Optional[NPCProfile] = None,
        knowledge_context: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Create an optimized prompt for the language model.
        
        Args:
            request: The classified request
            history: Optional conversation history
            profile: Optional NPC profile to use
            knowledge_context: Optional knowledge context from vector store
            
        Returns:
            The formatted and optimized prompt string
            
        Raises:
            ValueError: If request is None, has empty player input, or missing game context
        """
        # Validate request
        if request is None:
            raise ValueError("Invalid request: request cannot be None")
        
        if not request.player_input or not request.player_input.strip():
            raise ValueError("Invalid request: empty player input")
            
        if not isinstance(request.game_context, GameContext):
            raise ValueError("Invalid request: game_context must be a GameContext instance")

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
        prompt_parts = []

        # Add NPC profile if available
        if profile:
            try:
                profile_prompt = profile.get_system_prompt()
                if profile_prompt and profile_prompt.strip():
                    prompt_parts.append(profile_prompt)
            except Exception as e:
                self.logger.warning(f"Failed to get profile prompt: {e}")

        # Add base system prompt if no profile or profile prompt is empty
        if not prompt_parts:
            prompt_parts.append(BASE_SYSTEM_PROMPT)

        # Add knowledge context if available
        if knowledge_context:
            knowledge_text = self._format_knowledge_context(knowledge_context)
            if knowledge_text.strip():  # Only add if not empty
                prompt_parts.append(knowledge_text)

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
        Estimate the number of tokens in a text.
        
        Args:
            text: The text to estimate tokens for
            
        Returns:
            Estimated number of tokens
            
        Raises:
            TypeError: If input is not a string
        """
        if not isinstance(text, str):
            raise TypeError("Input must be string")
            
        # Simple estimation: 1 token per 4 characters
        return max(1, len(text) // 4)

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
            # Split prompt into sections
            sections = prompt.split("\n\n")
            
            # Always keep system prompt and current request
            system_prompt = sections[0]  # First section is system prompt
            current_request = sections[-1]  # Last section is current request
            
            # Find history section if it exists
            history_section = None
            for section in sections:
                if section.startswith("Previous conversation:"):
                    history_section = section
                    break
            
            # If we have history, keep the most recent entries that fit
            if history_section:
                history_entries = history_section.split("\n")[1:]  # Skip "Previous conversation:" line
                optimized_history = []
                remaining_tokens = self.max_prompt_tokens - self.estimate_tokens(system_prompt + "\n\n" + current_request)
                
                # Add history entries from most recent to oldest until we run out of tokens
                for entry in reversed(history_entries):
                    entry_tokens = self.estimate_tokens(entry)
                    if entry_tokens <= remaining_tokens:
                        optimized_history.insert(0, entry)
                        remaining_tokens -= entry_tokens
                    else:
                        break
                
                if optimized_history:
                    history_section = "Previous conversation:\n" + "\n".join(optimized_history)
                else:
                    history_section = None
            
            # Combine sections
            sections = [system_prompt]
            if history_section:
                sections.append(history_section)
            sections.append(current_request)
            
            return "\n\n".join(filter(None, sections))
        
        return prompt

    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limit.
        
        Args:
            text: Text to truncate
            max_tokens: Maximum number of tokens
            
        Returns:
            Truncated text
        """
        if self.estimate_tokens(text) <= max_tokens:
            return text
            
        # Binary search for the right length
        left, right = 0, len(text)
        while left < right:
            mid = (left + right + 1) // 2
            if self.estimate_tokens(text[:mid]) <= max_tokens:
                left = mid
            else:
                right = mid - 1
                
        return text[:left]

    def _format_game_context(self, context: GameContext) -> str:
        """
        Format game context for inclusion in prompt.
        
        Args:
            context: Game context to format
            
        Returns:
            Formatted context string
        """
        parts = []
        
        # Add player info
        if context.player_id:
            parts.append(f"Player ID: {context.player_id}")
            
        # Add language proficiency
        if context.language_proficiency:
            parts.append("Language Proficiency:")
            for skill, level in context.language_proficiency.items():
                parts.append(f"- {skill}: {level}")
                
        return "\n".join(parts)

    def _format_knowledge_context(self, knowledge_docs: List[Dict[str, Any]]) -> str:
        """
        Format knowledge context for inclusion in prompt.
        
        Args:
            knowledge_docs: List of knowledge documents with metadata
            
        Returns:
            Formatted knowledge context string
        """
        if not knowledge_docs:
            return ""
            
        parts = ["Relevant information:"]
        
        for doc in knowledge_docs:
            # Get document content
            content = doc.get('document', '').strip()
            if not content:
                continue
                
            # Get metadata
            metadata = doc.get('metadata', {})
            doc_type = metadata.get('type', 'general')
            importance = metadata.get('importance', 'medium')
            
            # Format the entry
            entry = f"- [{doc_type.upper()}] {content}"
            if importance != 'medium':
                entry += f" (Importance: {importance})"
                
            parts.append(entry)
            
        return "\n".join(parts)