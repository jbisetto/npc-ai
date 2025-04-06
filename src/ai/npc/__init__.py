"""
Companion AI Module

This module implements the companion dog AI that assists the player
with Japanese language learning and navigation through the train station.
"""

__version__ = "0.1.0"

import logging
from typing import Dict, Any, Optional
from .core.models import CompanionRequest, ClassifiedRequest, ProcessingTier
from .core.prompt_manager import PromptManager
from .core.npc_profile import NPCProfile
from .core.conversation_manager import ConversationManager
from .core.storage_manager import StorageManager
from .core.vector.tokyo_knowledge_store import TokyoKnowledgeStore
from .local.local_processor import LocalProcessor
from .hosted.hosted_processor import HostedProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
prompt_manager = PromptManager()
storage_manager = StorageManager()
knowledge_store = TokyoKnowledgeStore()
conversation_manager = ConversationManager(storage_manager)

# Initialize processors
local_processor = LocalProcessor()
hosted_processor = HostedProcessor()

def process_request(request: CompanionRequest, profile: Optional[NPCProfile] = None) -> Dict[str, Any]:
    """
    Process a request to the companion AI.
    
    Args:
        request: The request to process
        profile: Optional NPC profile to use
        
    Returns:
        The processed response
    """
    logger.info(f"Processing request: {request.request_id}")
    
    # Determine processing tier based on configuration
    processing_tier = ProcessingTier.LOCAL  # Default to local
    
    # Create classified request
    classified_request = ClassifiedRequest(
        **request.dict(),
        processing_tier=processing_tier,
        metadata={}
    )
    
    # Process based on tier
    if processing_tier == ProcessingTier.LOCAL:
        response = local_processor.process(classified_request, profile)
    else:
        response = hosted_processor.process(classified_request, profile)
        
    return response 