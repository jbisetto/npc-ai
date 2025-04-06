"""
Initialize the local module.

This module contains the local processor and its dependencies.
"""

from src.ai.npc.local.ollama_client import OllamaClient, OllamaError
from src.ai.npc.local.local_processor import LocalProcessor
from src.ai.npc.local.prompt_engineering import create_prompt
from src.ai.npc.local.response_parser import ResponseParser

__all__ = [
    'OllamaClient',
    'OllamaError',
    'LocalProcessor',
    'create_prompt',
    'ResponseParser'
] 