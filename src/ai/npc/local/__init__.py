"""
Local processing module for NPC AI.

This module provides local processing capabilities using Ollama.
"""

from src.ai.npc.local.local_processor import LocalProcessor
from src.ai.npc.local.ollama_client import OllamaClient, OllamaError
from src.ai.npc.core.prompt_manager import PromptManager

__all__ = [
    'LocalProcessor',
    'OllamaClient',
    'OllamaError',
    'PromptManager'
] 