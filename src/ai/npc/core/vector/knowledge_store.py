"""
Base knowledge store interface.

This module defines the base interface for knowledge stores that provide
contextual information for NPC responses.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from src.ai.npc.core.models import ClassifiedRequest


class KnowledgeStore(ABC):
    """Base class for knowledge stores."""
    
    @abstractmethod
    async def contextual_search(self, request: ClassifiedRequest) -> List[Dict[str, Any]]:
        """
        Search for relevant knowledge context based on the request.
        
        Args:
            request: The classified request to find context for
            
        Returns:
            A list of dictionaries containing relevant knowledge context.
            Each dictionary should have at least:
            - text: The actual knowledge text
            - metadata: A dictionary of metadata about the knowledge
        """
        pass
    
    @abstractmethod
    async def add_knowledge(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add new knowledge to the store.
        
        Args:
            text: The text content to add
            metadata: Optional metadata about the content
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all knowledge from the store."""
        pass 