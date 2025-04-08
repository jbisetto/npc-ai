#!/usr/bin/env python
"""
NPC AI - Application Entry Point
"""

import os
import sys
import logging
import logging.config
import asyncio
from pathlib import Path

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Define log file path in src directory
log_file_path = os.path.join(current_dir, "npc_ai.log")

# Configure logging
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "detailed",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": log_file_path,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    },
    "loggers": {
        "src": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}

# Apply the logging configuration
logging.config.dictConfig(logging_config)

from src.ai.npc import get_knowledge_store
from src.ai.npc.config import load_config

async def initialize_knowledge_base():
    """Initialize the knowledge base at startup."""
    try:
        # Get the knowledge base path
        current_dir = Path(__file__).parent
        knowledge_base_path = current_dir / "data" / "knowledge" / "tokyo-train-knowledge-base.json"
        
        if not knowledge_base_path.exists():
            logger.warning(f"Knowledge base file not found: {knowledge_base_path}")
            return
            
        # Initialize the knowledge store
        store = get_knowledge_store()
        await store.from_file(str(knowledge_base_path))
        
        # Log analytics
        analytics = store.get_analytics()
        logger.info(f"Knowledge store initialized with {store.collection.count()} documents")
        logger.info(f"Cache hit rate: {analytics['cache_hit_rate']:.2%}")
        
    except Exception as e:
        logger.error(f"Error initializing knowledge base: {e}")
        raise

async def main():
    """Main entry point."""
    try:
        # Load configuration
        config = load_config()
        logger.info("Configuration loaded successfully")
        
        # Initialize knowledge base
        await initialize_knowledge_base()
        
        # Start the server or other components
        # TODO: Add server initialization
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
