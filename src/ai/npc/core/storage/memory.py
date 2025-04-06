"""
In-Memory Storage

This module provides an in-memory implementation of the conversation storage.
"""

import logging
import copy
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from src.ai.npc.core.storage.base import ConversationStorage

logger = logging.getLogger(__name__)


class InMemoryConversationStorage(ConversationStorage):
    """
    In-memory implementation of the conversation storage.
    
    This class stores conversation contexts in memory, which means they are lost
    when the application restarts.
    """
    
    # Class-level storage to simulate persistence across instances
    _storage = {}
    
    def __init__(self):
        """Initialize the in-memory storage."""
        # Create a unique instance ID to isolate test instances
        self.instance_id = str(uuid.uuid4())[:8]
        logger.debug(f"Initialized InMemoryConversationStorage with instance ID: {self.instance_id}")
    
    def _get_prefixed_id(self, conversation_id: str) -> str:
        """Get the prefixed conversation ID to ensure isolation between test instances."""
        return f"{self.instance_id}:{conversation_id}"
    
    async def get_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a conversation context by ID.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            The conversation context, or None if not found
        """
        prefixed_id = self._get_prefixed_id(conversation_id)
        context = InMemoryConversationStorage._storage.get(prefixed_id)
        if context:
            logger.debug(f"Getting context for {conversation_id} with {len(context.get('entries', []))} entries")
            # Make a deep copy to avoid mutations affecting our storage
            return copy.deepcopy(context)
        logger.debug(f"No context found for {conversation_id}")
        return None
    
    async def save_context(self, conversation_id: str, context: Dict[str, Any]) -> None:
        """
        Save a conversation context.
        
        Args:
            conversation_id: The ID of the conversation
            context: The conversation context to save
        """
        prefixed_id = self._get_prefixed_id(conversation_id)
        
        # Ensure the context has a timestamp
        if 'timestamp' not in context:
            context['timestamp'] = datetime.now().isoformat()
        
        # Ensure entries exists
        if 'entries' not in context:
            context['entries'] = []
            
        # Make a deep copy to avoid reference sharing
        InMemoryConversationStorage._storage[prefixed_id] = copy.deepcopy(context)
        
        logger.debug(f"Saved context for {conversation_id} with {len(context.get('entries', []))} entries")
        
        # Verify the entries were saved correctly
        saved_context = InMemoryConversationStorage._storage[prefixed_id]
        logger.debug(f"Verified saved context has {len(saved_context.get('entries', []))} entries")
    
    async def delete_context(self, conversation_id: str) -> None:
        """
        Delete a conversation context.
        
        Args:
            conversation_id: The ID of the conversation
        """
        prefixed_id = self._get_prefixed_id(conversation_id)
        if prefixed_id in InMemoryConversationStorage._storage:
            logger.debug(f"Deleting context for {conversation_id}")
            del InMemoryConversationStorage._storage[prefixed_id]
    
    async def list_contexts(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List conversation contexts.
        
        Args:
            limit: The maximum number of contexts to return
            offset: The number of contexts to skip
            
        Returns:
            A list of conversation contexts
        """
        # Filter contexts that belong to this instance
        prefix = f"{self.instance_id}:"
        instance_contexts = {
            k.replace(prefix, ''): v 
            for k, v in InMemoryConversationStorage._storage.items() 
            if k.startswith(prefix)
        }
        
        # Convert to list, copy, sort by timestamp (newest first), and slice
        contexts = [copy.deepcopy(ctx) for ctx in instance_contexts.values()]
        contexts.sort(key=lambda ctx: ctx.get('timestamp', ''), reverse=True)
        logger.debug(f"Listing contexts: found {len(contexts)} total, returning {min(limit, max(0, len(contexts) - offset))} contexts")
        return contexts[offset:offset + limit] if offset < len(contexts) else []
    
    async def cleanup_old_contexts(self, max_age_days: int = 30) -> int:
        """
        Delete conversation contexts older than the specified age.
        
        Args:
            max_age_days: The maximum age of contexts to keep, in days
            
        Returns:
            The number of contexts deleted
        """
        now = datetime.now()
        max_age = timedelta(days=max_age_days)
        count = 0
        
        # Filter contexts that belong to this instance
        prefix = f"{self.instance_id}:"
        for key, context in list(InMemoryConversationStorage._storage.items()):
            if not key.startswith(prefix):
                continue
                
            timestamp = context.get('timestamp')
            if timestamp:
                try:
                    context_date = datetime.fromisoformat(timestamp)
                    if now - context_date > max_age:
                        del InMemoryConversationStorage._storage[key]
                        count += 1
                except ValueError:
                    # Invalid timestamp format, ignore this entry
                    pass
        
        logger.debug(f"Cleaned up {count} old contexts")
        return count
        
    async def clear_entries(self, conversation_id: str) -> None:
        """
        Clear all entries for a specific conversation ID.
        
        Args:
            conversation_id: The ID of the conversation to clear entries for
        """
        logger.debug(f"Clearing entries for {conversation_id}")
        prefixed_id = self._get_prefixed_id(conversation_id)
        
        if prefixed_id in InMemoryConversationStorage._storage:
            # Get a copy of the existing context
            context = copy.deepcopy(InMemoryConversationStorage._storage[prefixed_id])
            # Clear entries
            context["entries"] = []
            # Save it back
            InMemoryConversationStorage._storage[prefixed_id] = context
            logger.debug(f"Cleared all entries for {conversation_id}")
        else:
            # Create a new empty context
            context = {
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "entries": []
            }
            InMemoryConversationStorage._storage[prefixed_id] = context
            logger.debug(f"Created new empty context for {conversation_id}") 