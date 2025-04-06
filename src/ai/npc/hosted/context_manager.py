"""
Context Manager for Tier 3 processing.

This module provides classes for managing conversation context across
multiple interactions with the player, enabling the companion AI to
maintain context and provide more coherent responses.
"""

import uuid
import logging
import copy
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.ai.npc.core.models import (
    ClassifiedRequest,
    IntentCategory
)

logger = logging.getLogger(__name__)


class ContextEntry:
    """
    A single entry in a conversation context, representing one exchange
    between the player and the companion AI.
    """
    
    def __init__(
        self,
        request: str,
        response: str,
        timestamp: Optional[datetime] = None,
        intent: Optional[IntentCategory] = None,
        entities: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a context entry.
        
        Args:
            request: The player's request
            response: The companion's response
            timestamp: When the exchange occurred (defaults to now)
            intent: The classified intent of the request
            entities: Any entities extracted from the request
        """
        self.request = request
        self.response = response
        self.timestamp = timestamp or datetime.now()
        self.intent = intent
        self.entities = entities or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the context entry to a dictionary.
        
        Returns:
            A dictionary representation of the context entry
        """
        return {
            "request": self.request,
            "response": self.response,
            "timestamp": self.timestamp.isoformat(),
            "intent": self.intent.value if self.intent else None,
            "entities": self.entities
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextEntry':
        """
        Create a context entry from a dictionary.
        
        Args:
            data: A dictionary representation of a context entry
            
        Returns:
            A new ContextEntry instance
        """
        intent = None
        if data.get("intent"):
            try:
                intent = IntentCategory(data["intent"])
            except ValueError:
                logger.warning(f"Unknown intent: {data['intent']}")
        
        return cls(
            request=data["request"],
            response=data["response"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            intent=intent,
            entities=data.get("entities", {})
        )


class ConversationContext:
    """
    A conversation context that maintains the history of exchanges between
    the player and the companion AI.
    """
    
    def __init__(
        self,
        conversation_id: Optional[str] = None,
        player_id: Optional[str] = None,
        player_language_level: str = "N5",
        current_location: str = "unknown",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        """
        Initialize a conversation context.
        
        Args:
            conversation_id: A unique identifier for the conversation (generated if not provided)
            player_id: A unique identifier for the player
            player_language_level: The player's Japanese language level (e.g., "N5", "N4")
            current_location: The player's current location in the game
            created_at: When the conversation was created (defaults to now)
            updated_at: When the conversation was last updated (defaults to now)
        """
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.player_id = player_id
        self.player_language_level = player_language_level
        self.current_location = current_location
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or self.created_at
        self.entries: List[ContextEntry] = []
    
    def add_entry(self, entry: ContextEntry) -> None:
        """
        Add an entry to the conversation context.
        
        Args:
            entry: The context entry to add
        """
        self.entries.append(entry)
        self.updated_at = datetime.now()
    
    def add_entry_from_request_response(
        self,
        request: ClassifiedRequest,
        response: str
    ) -> None:
        """
        Add an entry from a request and response.
        
        Args:
            request: The classified request
            response: The companion's response
        """
        entry = ContextEntry(
            request=request.player_input,
            response=response,
            timestamp=request.timestamp or datetime.now(),
            intent=request.intent,
            entities=request.extracted_entities
        )
        self.add_entry(entry)
    
    def get_recent_entries(self, count: int = 5) -> List[ContextEntry]:
        """
        Get the most recent entries in the conversation context.
        
        Args:
            count: The maximum number of entries to return
            
        Returns:
            A list of the most recent entries, sorted by timestamp (newest first)
        """
        # Sort entries by timestamp (newest first)
        sorted_entries = sorted(
            self.entries,
            key=lambda entry: entry.timestamp,
            reverse=True
        )
        
        # Return the specified number of entries
        return sorted_entries[:count]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the conversation context to a dictionary.
        
        Returns:
            A dictionary representation of the conversation context
        """
        return {
            "conversation_id": self.conversation_id,
            "player_id": self.player_id,
            "player_language_level": self.player_language_level,
            "current_location": self.current_location,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "entries": [entry.to_dict() for entry in self.entries]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        """
        Create a conversation context from a dictionary.
        
        Args:
            data: A dictionary representation of a conversation context
            
        Returns:
            A new ConversationContext instance
        """
        context = cls(
            conversation_id=data["conversation_id"],
            player_id=data["player_id"],
            player_language_level=data.get("player_language_level", "N5"),
            current_location=data.get("current_location", "unknown"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )
        
        # Directly set entries without calling add_entry to preserve timestamps
        context.entries = [ContextEntry.from_dict(entry_data) for entry_data in data.get("entries", [])]
        
        return context


class ContextManager:
    """
    Manager for conversation contexts.
    
    This class provides methods for creating, retrieving, updating, and
    deleting conversation contexts, as well as preparing context for
    requests to the companion AI.
    """
    
    def __init__(self):
        """Initialize the context manager."""
        self._contexts: Dict[str, ConversationContext] = {}
    
    def create_context(
        self,
        player_id: Optional[str] = None,
        player_language_level: str = "N5",
        current_location: str = "unknown"
    ) -> ConversationContext:
        """
        Create a new conversation context.
        
        Args:
            player_id: A unique identifier for the player
            player_language_level: The player's Japanese language level
            current_location: The player's current location in the game
            
        Returns:
            The newly created conversation context
        """
        context = ConversationContext(
            player_id=player_id,
            player_language_level=player_language_level,
            current_location=current_location
        )
        
        # Store the context
        self._contexts[context.conversation_id] = context
        
        logger.info(f"Created new conversation context: {context.conversation_id}")
        return context
    
    def get_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """
        Get a conversation context by ID.
        
        Args:
            conversation_id: The ID of the conversation context to retrieve
            
        Returns:
            The conversation context, or None if not found
        """
        return self._contexts.get(conversation_id)
    
    def update_context(
        self,
        conversation_id: str,
        request: ClassifiedRequest,
        response: str
    ) -> Optional[ConversationContext]:
        """
        Update a conversation context with a new request-response pair.
        
        Args:
            conversation_id: The ID of the conversation context to update
            request: The classified request
            response: The companion's response
            
        Returns:
            The updated conversation context, or None if not found
        """
        context = self.get_context(conversation_id)
        if not context:
            logger.warning(f"Context not found: {conversation_id}")
            return None
        
        # Add the request-response pair to the context
        context.add_entry_from_request_response(request, response)
        
        logger.debug(f"Updated context {conversation_id} with new entry")
        return context
    
    def delete_context(self, conversation_id: str) -> bool:
        """
        Delete a conversation context.
        
        Args:
            conversation_id: The ID of the conversation context to delete
            
        Returns:
            True if the context was deleted, False if not found
        """
        if conversation_id in self._contexts:
            del self._contexts[conversation_id]
            logger.info(f"Deleted conversation context: {conversation_id}")
            return True
        
        logger.warning(f"Context not found for deletion: {conversation_id}")
        return False
    
    def get_or_create_context(
        self,
        conversation_id: Optional[str] = None,
        player_id: Optional[str] = None,
        player_language_level: str = "N5",
        current_location: str = "unknown"
    ) -> ConversationContext:
        """
        Get a conversation context by ID, or create a new one if not found.
        
        Args:
            conversation_id: The ID of the conversation context to retrieve
            player_id: A unique identifier for the player (for new contexts)
            player_language_level: The player's Japanese language level (for new contexts)
            current_location: The player's current location in the game (for new contexts)
            
        Returns:
            The retrieved or newly created conversation context
        """
        if conversation_id and conversation_id in self._contexts:
            return self._contexts[conversation_id]
        
        # Create a new context
        if conversation_id:
            context = ConversationContext(
                conversation_id=conversation_id,
                player_id=player_id,
                player_language_level=player_language_level,
                current_location=current_location
            )
            self._contexts[conversation_id] = context
            logger.info(f"Created new conversation context with specified ID: {conversation_id}")
            return context
        
        # Create a new context with a generated ID
        return self.create_context(
            player_id=player_id,
            player_language_level=player_language_level,
            current_location=current_location
        )
    
    def add_request_response_to_context(
        self,
        conversation_id: str,
        request: ClassifiedRequest,
        response: str
    ) -> Optional[ConversationContext]:
        """
        Add a request-response pair to a conversation context.
        
        This is an alias for update_context.
        
        Args:
            conversation_id: The ID of the conversation context to update
            request: The classified request
            response: The companion's response
            
        Returns:
            The updated conversation context, or None if not found
        """
        return self.update_context(conversation_id, request, response)
    
    def get_context_for_request(
        self,
        request: ClassifiedRequest
    ) -> Optional[ConversationContext]:
        """
        Get the conversation context for a request.
        
        Args:
            request: The classified request
            
        Returns:
            The conversation context, or None if not found
        """
        # Check if the request has a conversation_id
        conversation_id = request.additional_params.get("conversation_id")
        if not conversation_id:
            logger.debug("Request does not have a conversation_id")
            return None
        
        # Get the context
        context = self.get_context(conversation_id)
        if not context:
            logger.warning(f"Context not found for request: {conversation_id}")
        
        return context
    
    def prepare_context_for_request(
        self,
        request: ClassifiedRequest
    ) -> ClassifiedRequest:
        """
        Prepare a request with conversation context.
        
        This method adds the conversation context to the request's additional_params
        so that it can be used by the specialized handlers.
        
        Args:
            request: The classified request
            
        Returns:
            The request with conversation context added
        """
        # Get the context for the request
        context = self.get_context_for_request(request)
        if not context:
            logger.debug("No context found for request")
            return request
        
        # Create a copy of the request to avoid modifying the original
        prepared_request = copy.deepcopy(request)
        
        # Add the context to the request's additional_params
        context_dict = {
            "conversation_id": context.conversation_id,
            "player_language_level": context.player_language_level,
            "current_location": context.current_location,
            "previous_exchanges": []
        }
        
        # Add recent exchanges
        recent_entries = context.get_recent_entries(5)  # Get the 5 most recent entries
        for entry in recent_entries:
            context_dict["previous_exchanges"].append({
                "request": entry.request,
                "response": entry.response
            })
        
        # Add the context to the request
        prepared_request.additional_params["conversation_context"] = context_dict
        
        logger.debug(f"Prepared request with conversation context: {context.conversation_id}")
        return prepared_request


# Create a singleton instance of the context manager
default_context_manager = ContextManager() 