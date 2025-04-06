"""
Storage Factory

This module provides a factory for creating storage instances.
"""

import logging
from typing import Dict, Any, Optional

from src.ai.npc.core.storage.base import ConversationStorage
from src.ai.npc.core.storage.memory import InMemoryConversationStorage
from src.ai.npc.core.storage.sqlite import SQLiteConversationStorage
from src.ai.npc.core.storage.config import StorageType, get_storage_config

logger = logging.getLogger(__name__)


class StorageFactory:
    """
    Factory for creating storage instances.
    
    This class is responsible for creating storage instances based on configuration.
    """
    
    _instance = None
    _storage_instances = {}
    
    def __new__(cls):
        """Create a singleton instance of the factory."""
        if cls._instance is None:
            cls._instance = super(StorageFactory, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the factory."""
        self._storage_instances = {}
    
    def get_storage(self, config: Optional[Dict[str, Any]] = None) -> ConversationStorage:
        """
        Get a storage instance based on configuration.
        
        Args:
            config: Optional configuration override
            
        Returns:
            A storage instance
        """
        storage_config = config or get_storage_config()
        storage_type = storage_config.get('type', StorageType.MEMORY)
        
        # Check if we already have an instance for this type
        if storage_type in self._storage_instances:
            return self._storage_instances[storage_type]
        
        # Create a new instance
        if storage_type == StorageType.MEMORY:
            storage = InMemoryConversationStorage()
        elif storage_type == StorageType.SQLITE:
            sqlite_config = storage_config.get('sqlite', {})
            database_path = sqlite_config.get('database_path')
            storage = SQLiteConversationStorage(database_path=database_path)
        else:
            logger.warning(f"Unknown storage type: {storage_type}, falling back to in-memory storage")
            storage = InMemoryConversationStorage()
        
        # Cache the instance
        self._storage_instances[storage_type] = storage
        
        return storage


# Default storage factory instance
default_storage_factory = StorageFactory() 