"""
Specialized handlers for different types of requests.

This module provides handlers for processing different types of requests
based on their processing tier.
"""

import logging
from typing import Dict, Any, Optional, List

from src.ai.npc.core.models import (
    NPCRequest,
    ProcessingTier
)

logger = logging.getLogger(__name__)

class SpecializedHandler:
    """Base class for specialized request handlers."""
    
    def can_handle(self, request: NPCRequest) -> bool:
        """
        Check if this handler can process the request.
        
        Args:
            request: The request to check
            
        Returns:
            True if this handler can process the request
        """
        return False
        
    def handle(self, request: NPCRequest) -> Dict[str, Any]:
        """
        Process a request.
        
        Args:
            request: The request to process
            
        Returns:
            The processed response
        """
        raise NotImplementedError()


class LocalHandler(SpecializedHandler):
    """Handler for local processing requests."""
    
    def can_handle(self, request: NPCRequest) -> bool:
        """Check if this handler can process the request."""
        return request.processing_tier == ProcessingTier.LOCAL
        
    def handle(self, request: NPCRequest) -> Dict[str, Any]:
        """Process a local request."""
        # Basic local processing logic
        response = f"I understand you said: {request.player_input}"
        return {"response": response}


class HostedHandler(SpecializedHandler):
    """Handler for hosted processing requests."""
    
    def can_handle(self, request: NPCRequest) -> bool:
        """Check if this handler can process the request."""
        return request.processing_tier == ProcessingTier.HOSTED
        
    def handle(self, request: NPCRequest) -> Dict[str, Any]:
        """Process a hosted request."""
        # Basic hosted processing logic
        response = f"Processing your request: {request.player_input}"
        return {"response": response}


class HandlerRegistry:
    """Registry for managing specialized handlers."""
    
    def __init__(self):
        """Initialize the handler registry."""
        self._handlers: Dict[ProcessingTier, SpecializedHandler] = {}
        self._setup_default_handlers()
        
    def _setup_default_handlers(self):
        """Set up the default handlers."""
        self.register_handler(ProcessingTier.LOCAL, LocalHandler())
        self.register_handler(ProcessingTier.HOSTED, HostedHandler())
        
    def register_handler(self, tier: ProcessingTier, handler: SpecializedHandler) -> None:
        """
        Register a handler for a processing tier.
        
        Args:
            tier: The processing tier to register for
            handler: The handler to register
        """
        self._handlers[tier] = handler
        logger.debug(f"Registered handler for tier: {tier}")
        
    def get_handler(self, request: NPCRequest) -> Optional[SpecializedHandler]:
        """
        Get the appropriate handler for a request.
        
        Args:
            request: The request to get a handler for
            
        Returns:
            The appropriate handler, or None if no handler is found
        """
        handler = self._handlers.get(request.processing_tier)
        if not handler:
            logger.warning(f"No handler found for tier: {request.processing_tier}")
            return None
            
        return handler 