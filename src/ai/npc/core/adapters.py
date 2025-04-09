"""
Adapters Module

This module provides standardized interfaces and data models for conversation
history and knowledge context integration in the NPC AI system.
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime
from pydantic import BaseModel, Field


class ConversationHistoryEntry(BaseModel):
    """
    Standardized conversation history entry.
    
    Required fields:
    - user: The user's message text
    - assistant: The assistant's response text
    - timestamp: ISO format datetime string when the exchange occurred
    
    Optional fields:
    - metadata: Dictionary containing additional context (language_level, location, etc.)
    - conversation_id: Unique identifier for the conversation
    """
    user: str
    assistant: str
    timestamp: str  # ISO format datetime
    metadata: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None


class KnowledgeDocument(BaseModel):
    """
    Standardized knowledge document.
    
    Required fields:
    - text: The document text content
    - id: Unique identifier for the document
    
    Optional fields:
    - metadata: Dictionary containing document metadata
      - type: Document type (e.g., "location", "language_learning")
      - importance: Importance level ("high", "medium", "low")
      - source: Source of the document
      - intent: Associated intent for this knowledge
    - relevance_score: Float indicating relevance to the query (0-1)
    """
    text: str
    id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    relevance_score: Optional[float] = None


class ConversationHistoryAdapter(ABC):
    """
    Adapter for converting between different conversation history formats.
    """
    
    @abstractmethod
    def to_standard_format(self, history: List[Dict[str, Any]]) -> List[ConversationHistoryEntry]:
        """
        Convert from source format to standard format.
        
        Args:
            history: Source format conversation history
            
        Returns:
            List of standardized conversation history entries
        """
        pass
    
    @abstractmethod
    def from_standard_format(self, standardized_history: List[ConversationHistoryEntry]) -> List[Dict[str, Any]]:
        """
        Convert from standard format to target format.
        
        Args:
            standardized_history: Standardized conversation history
            
        Returns:
            List of conversation history entries in target format
        """
        pass


class KnowledgeContextAdapter(ABC):
    """
    Adapter for converting between different knowledge context formats.
    """
    
    @abstractmethod
    def to_standard_format(self, documents: List[Dict[str, Any]]) -> List[KnowledgeDocument]:
        """
        Convert from source format to standard format.
        
        Args:
            documents: Source format knowledge documents
            
        Returns:
            List of standardized knowledge documents
        """
        pass
    
    @abstractmethod
    def from_standard_format(self, standardized_documents: List[KnowledgeDocument]) -> List[Dict[str, Any]]:
        """
        Convert from standard format to target format.
        
        Args:
            standardized_documents: Standardized knowledge documents
            
        Returns:
            List of knowledge documents in target format
        """
        pass 