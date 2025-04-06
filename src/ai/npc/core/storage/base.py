"""
Storage Base Interface

This module defines the base interface for storage implementations.
"""

import abc
from typing import Dict, Any, List, Optional


class ConversationStorage(abc.ABC):
    """
    Abstract base class for conversation storage implementations.
    
    This class defines the interface that all conversation storage
    implementations must adhere to.
    """
    
    @abc.abstractmethod
    async def get_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a conversation context by ID.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            The conversation context, or None if not found
        """
        pass
    
    @abc.abstractmethod
    async def save_context(self, conversation_id: str, context: Dict[str, Any]) -> None:
        """
        Save a conversation context.
        
        Args:
            conversation_id: The ID of the conversation
            context: The conversation context to save
        """
        pass
    
    @abc.abstractmethod
    async def delete_context(self, conversation_id: str) -> None:
        """
        Delete a conversation context.
        
        Args:
            conversation_id: The ID of the conversation
        """
        pass
    
    @abc.abstractmethod
    async def list_contexts(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List conversation contexts.
        
        Args:
            limit: The maximum number of contexts to return
            offset: The number of contexts to skip
            
        Returns:
            A list of conversation contexts
        """
        pass
        
    @abc.abstractmethod
    async def cleanup_old_contexts(self, max_age_days: int = 30) -> int:
        """
        Delete conversation contexts older than the specified age.
        
        Args:
            max_age_days: The maximum age of contexts to keep, in days
            
        Returns:
            The number of contexts deleted
        """
        pass 