"""
Context manager for hosted request processing.

This module provides context management for hosted requests, including
conversation history and state tracking.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.ai.npc.core.models import (
    ClassifiedRequest,
    GameContext
)

logger = logging.getLogger(__name__)

class HostedContextManager:
    """Manages context for hosted request processing."""
    
    def __init__(self):
        """Initialize the hosted context manager."""
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self.logger = logging.getLogger(__name__)
        
    def add_request(
        self,
        conversation_id: str,
        request: ClassifiedRequest,
        response: str
    ) -> None:
        """
        Add a request-response pair to the conversation history.
        
        Args:
            conversation_id: The ID of the conversation
            request: The request that was processed
            response: The response that was generated
        """
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
            
        self.conversations[conversation_id].append({
            "request": request.to_dict(),
            "response": response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Trim history if too long
        if len(self.conversations[conversation_id]) > 10:
            self.conversations[conversation_id] = self.conversations[conversation_id][-10:]
            
    def get_history(
        self,
        conversation_id: str,
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get recent conversation history.
        
        Args:
            conversation_id: The ID of the conversation
            count: Number of recent exchanges to return
            
        Returns:
            List of recent exchanges
        """
        if conversation_id not in self.conversations:
            return []
            
        history = self.conversations[conversation_id]
        return history[-count:] if len(history) > count else history
        
    def clear_history(self, conversation_id: str) -> None:
        """
        Clear the conversation history.
        
        Args:
            conversation_id: The ID of the conversation to clear
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id] 