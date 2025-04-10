"""
Local processing module for NPC AI.

This module provides local processing capabilities using Ollama.
"""

from src.ai.npc.local.local_processor import LocalProcessor
from src.ai.npc.local.ollama_client import OllamaClient, OllamaError
from src.ai.npc.core.prompt_manager import PromptManager
from typing import Optional
import logging
import asyncio

__all__ = [
    'LocalProcessor',
    'OllamaClient',
    'OllamaError',
    'PromptManager'
]

logger = logging.getLogger(__name__)

# Global variable to store the local processor instance
_local_processor: Optional['LocalProcessor'] = None

def get_local_processor() -> 'LocalProcessor':
    """
    Returns a LocalProcessor instance, creating it if necessary.
    
    Returns:
        A LocalProcessor instance
    """
    global _local_processor
    
    if _local_processor is not None:
        logger.debug("Closing existing local processor before creating a new one")
        try:
            # Properly await the coroutine
            asyncio.run(_local_processor.close())
        except Exception as e:
            logger.error(f"Error closing local processor: {e}", exc_info=True)
        _local_processor = None
    
    from src.ai.npc.local.local_processor import LocalProcessor
    _local_processor = LocalProcessor()
    return _local_processor 