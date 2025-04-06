"""
Common Context Manager

This module provides a unified context management system that can be used by
both tier2 and tier3 processors, allowing for consistent context handling
with tier-specific optimizations.
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
            conversation_id: Unique identifier for the conversation
            player_id: Identifier for the player
            player_language_level: The player's Japanese language level
            current_location: The player's current location in the game
            created_at: When the context was created
            updated_at: When the context was last updated
        """
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.player_id = player_id
        self.player_language_level = player_language_level
        self.current_location = current_location
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.entries = []
    
    def add_entry(self, entry: ContextEntry) -> None:
        """
        Add an entry to the conversation context.
        
        Args:
            entry: The entry to add
        """
        self.entries.append(entry)
        self.updated_at = datetime.now()
    
    def add_entry_from_request_response(
        self,
        request: ClassifiedRequest,
        response: str
    ) -> None:
        """
        Add an entry to the conversation context from a request and response.
        
        Args:
            request: The classified request
            response: The response to the request
        """
        entry = ContextEntry(
            request=request.player_input,
            response=response,
            timestamp=request.timestamp if hasattr(request, 'timestamp') else None,
            intent=request.intent if hasattr(request, 'intent') else None,
            entities=request.extracted_entities if hasattr(request, 'extracted_entities') else {}
        )
        self.add_entry(entry)
    
    def get_recent_entries(self, count: int = 5) -> List[ContextEntry]:
        """
        Get the most recent entries in the conversation context.
        
        Args:
            count: The number of entries to get
            
        Returns:
            A list of the most recent entries
        """
        return self.entries[-count:] if self.entries else []
    
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
            player_id=data.get("player_id"),
            player_language_level=data.get("player_language_level", "N5"),
            current_location=data.get("current_location", "unknown"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )
        
        for entry_data in data.get("entries", []):
            entry = ContextEntry.from_dict(entry_data)
            context.entries.append(entry)
        
        return context


class ContextManager:
    """
    Manager for conversation contexts.
    
    This class provides methods for creating, retrieving, updating, and
    deleting conversation contexts.
    """
    
    def __init__(self, tier_specific_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the context manager.
        
        Args:
            tier_specific_config: Optional configuration specific to the tier
        """
        self.tier_specific_config = tier_specific_config or {}
        self.contexts = {}
        logger.debug("Initialized ContextManager with config: %s", self.tier_specific_config)
    
    def create_context(
        self,
        player_id: Optional[str] = None,
        player_language_level: str = "N5",
        current_location: str = "unknown"
    ) -> ConversationContext:
        """
        Create a new conversation context.
        
        Args:
            player_id: Identifier for the player
            player_language_level: The player's Japanese language level
            current_location: The player's current location in the game
            
        Returns:
            A new ConversationContext instance
        """
        context = ConversationContext(
            player_id=player_id,
            player_language_level=player_language_level,
            current_location=current_location
        )
        
        self.contexts[context.conversation_id] = context
        logger.debug(f"Created context {context.conversation_id}")
        
        return context
    
    def get_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """
        Get a conversation context by ID.
        
        Args:
            conversation_id: The ID of the conversation context to get
            
        Returns:
            The conversation context, or None if not found
        """
        return self.contexts.get(conversation_id)
    
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
            response: The response to the request
            
        Returns:
            The updated conversation context, or None if not found
        """
        context = self.get_context(conversation_id)
        
        if context:
            context.add_entry_from_request_response(request, response)
            logger.debug(f"Updated context {conversation_id}")
            return context
        
        logger.warning(f"Context {conversation_id} not found")
        return None
    
    def delete_context(self, conversation_id: str) -> bool:
        """
        Delete a conversation context.
        
        Args:
            conversation_id: The ID of the conversation context to delete
            
        Returns:
            True if the context was deleted, False otherwise
        """
        if conversation_id in self.contexts:
            del self.contexts[conversation_id]
            logger.debug(f"Deleted context {conversation_id}")
            return True
        
        logger.warning(f"Context {conversation_id} not found")
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
            conversation_id: The ID of the conversation context to get
            player_id: Identifier for the player
            player_language_level: The player's Japanese language level
            current_location: The player's current location in the game
            
        Returns:
            The conversation context
        """
        if conversation_id and conversation_id in self.contexts:
            return self.contexts[conversation_id]
        
        return self.create_context(
            player_id=player_id,
            player_language_level=player_language_level,
            current_location=current_location
        )
    
    def prepare_context_for_request(
        self,
        request: ClassifiedRequest
    ) -> ClassifiedRequest:
        """
        Prepare a request with context information.
        
        Args:
            request: The classified request
            
        Returns:
            The request with context information added
        """
        # Check if the request already has a conversation_id
        conversation_id = request.additional_params.get("conversation_id")
        
        if not conversation_id:
            # Create a new context if there's no conversation_id
            context = self.create_context()
            request.additional_params["conversation_id"] = context.conversation_id
        else:
            # Get the existing context
            context = self.get_context(conversation_id)
            
            if not context:
                # Create a new context if the conversation_id is not found
                context = self.create_context()
                request.additional_params["conversation_id"] = context.conversation_id
        
        # Add context information to the request
        request.additional_params["player_language_level"] = context.player_language_level
        request.additional_params["current_location"] = context.current_location
        
        return request


# Create a default context manager for convenience
default_context_manager = ContextManager() 