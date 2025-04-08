"""
Companion AI Module

This module implements the companion dog AI that assists the player
with Japanese language learning and navigation through the train station.
"""

__version__ = "0.1.0"

import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Export core models directly as they are fundamental
from .core.models import CompanionRequest, ClassifiedRequest, ProcessingTier

# Initialize components lazily
_prompt_manager = None
_storage_manager = None
_knowledge_store = None
_local_processor = None
_hosted_processor = None
_context_manager = None

def get_prompt_manager():
    """Get the global prompt manager instance."""
    global _prompt_manager
    if _prompt_manager is None:
        from .core.prompt_manager import PromptManager
        _prompt_manager = PromptManager()
    return _prompt_manager

def get_storage_manager():
    """Get or initialize the storage manager."""
    global _storage_manager
    if _storage_manager is None:
        from .core.storage_manager import StorageManager
        _storage_manager = StorageManager()
    return _storage_manager

def get_knowledge_store():
    """Get or initialize the knowledge store."""
    global _knowledge_store
    if _knowledge_store is None:
        from .core.vector.tokyo_knowledge_store import TokyoKnowledgeStore
        _knowledge_store = TokyoKnowledgeStore()
    return _knowledge_store

def get_local_processor():
    """Get or create the local processor instance."""
    global _local_processor
    if _local_processor is None:
        from .local.local_processor import LocalProcessor
        from .local.ollama_client import OllamaClient
        _local_processor = LocalProcessor(ollama_client=OllamaClient())
    return _local_processor

def get_hosted_processor():
    """Get or create the hosted processor instance."""
    global _hosted_processor
    if _hosted_processor is None:
        from .hosted.hosted_processor import HostedProcessor
        _hosted_processor = HostedProcessor()
    return _hosted_processor

async def process_request(request: CompanionRequest, profile: Optional['NPCProfile'] = None) -> Dict[str, Any]:
    """
    Process a request to the companion AI.
    
    Args:
        request: The request to process
        profile: Optional NPC profile to use (currently unused)
        
    Returns:
        The processed response
    """
    logger.info(f"Processing request: {request.request_id}")
    
    # Load config
    from src.ai.npc.config import get_full_config
    config = get_full_config()
    
    # Determine processing tier based on configuration
    if config.get('hosted', {}).get('enabled', False):
        processing_tier = ProcessingTier.HOSTED
    elif config.get('local', {}).get('enabled', False):
        processing_tier = ProcessingTier.LOCAL
    else:
        raise ValueError("No processing tier enabled in config")
    
    # Create classified request
    classified_request = ClassifiedRequest(
        **request.model_dump(),
        processing_tier=processing_tier,
        metadata={}
    )
    
    # Process based on tier
    if processing_tier == ProcessingTier.LOCAL:
        response = await get_local_processor().process(classified_request)
    else:
        response = await get_hosted_processor().process(classified_request)
        
    return response 