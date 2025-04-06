"""
Storage Module

This module provides storage implementations for the companion AI system.
"""

from .base import ConversationStorage
from .memory import InMemoryConversationStorage
from .sqlite import SQLiteConversationStorage
from .config import StorageType, get_storage_config
from .factory import StorageFactory, default_storage_factory

__all__ = [
    'ConversationStorage',
    'InMemoryConversationStorage',
    'SQLiteConversationStorage',
    'StorageType',
    'get_storage_config',
    'StorageFactory',
    'default_storage_factory',
] 