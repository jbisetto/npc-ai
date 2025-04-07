"""
Core processor framework.

This module provides the base framework for request processing.
"""

import logging
from typing import Dict, Any, Optional, Type

from src.ai.npc.core.models import (
    ClassifiedRequest,
    ProcessingTier
)
from src.ai.npc.core.constants import (
    METADATA_KEY_INTENT,
    INTENT_DEFAULT
)

logger = logging.getLogger(__name__)

class Processor:
    """Base framework for processing requests."""
    
    def __init__(self):
        """Initialize the processor framework."""
        self.logger = logging.getLogger(__name__)
    
    def process_request(self, request: ClassifiedRequest) -> Dict[str, Any]:
        """
        Process a request using the appropriate processor.
        
        Args:
            request: The classified request to process
            
        Returns:
            The processed response
        """
        # Get the intent from metadata, defaulting to DEFAULT if not present
        intent = request.additional_params.get(METADATA_KEY_INTENT, INTENT_DEFAULT)
        
        # Select processor based on tier
        if request.processing_tier == ProcessingTier.LOCAL:
            return self._process_local(request, intent)
        else:
            return self._process_hosted(request, intent)
    
    def _process_local(self, request: ClassifiedRequest, intent: str) -> Dict[str, Any]:
        """
        Process a request using the local processor.
        
        Args:
            request: The request to process
            intent: The classified intent of the request
            
        Returns:
            The processed response
        """
        # Local processing logic
        pass
    
    def _process_hosted(self, request: ClassifiedRequest, intent: str) -> Dict[str, Any]:
        """
        Process a request using the hosted processor.
        
        Args:
            request: The request to process
            intent: The classified intent of the request
            
        Returns:
            The processed response
        """
        # Hosted processing logic
        pass