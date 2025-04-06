"""
Storage Configuration

This module provides configuration options for the storage implementations.
"""

import os
from typing import Dict, Any, Optional

# Default database path
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)
    ))))),
    'data', 'conversations.db'
)

# Storage type options
class StorageType:
    MEMORY = "memory"
    SQLITE = "sqlite"

# Default storage config
DEFAULT_STORAGE_CONFIG = {
    "type": StorageType.SQLITE,  # Default to SQLite storage
    "sqlite": {
        "database_path": DEFAULT_DB_PATH,
        "cleanup_days": 30,      # Default to cleaning up conversations older than 30 days
    }
}

def get_storage_config() -> Dict[str, Any]:
    """
    Get the storage configuration from environment variables.
    
    Returns:
        The storage configuration
    """
    config = DEFAULT_STORAGE_CONFIG.copy()
    
    # Override with environment variables if present
    storage_type = os.environ.get('CONVERSATION_STORAGE_TYPE')
    if storage_type:
        config['type'] = storage_type
    
    database_path = os.environ.get('CONVERSATION_STORAGE_DB_PATH')
    if database_path:
        config['sqlite']['database_path'] = database_path
    
    cleanup_days = os.environ.get('CONVERSATION_STORAGE_CLEANUP_DAYS')
    if cleanup_days and cleanup_days.isdigit():
        config['sqlite']['cleanup_days'] = int(cleanup_days)
    
    return config 