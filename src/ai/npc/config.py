"""
NPC AI - Configuration

This module contains configuration settings for the AI system.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Personality traits
PERSONALITY_TRAITS = {
    "FRIENDLY": 0.8,
    "HELPFUL": 0.9,
    "KNOWLEDGEABLE": 0.7,
    "PATIENT": 0.9,
    "ENTHUSIASTIC": 0.6,
}

# Local model configuration (Ollama)
LOCAL_MODEL_CONFIG = {
    "model_name": "deepseek-coder:7b",
    "max_tokens": 256,
    "temperature": 0.7,
    "top_p": 0.9,
    "cache_size": 100,  # Number of responses to cache
}

# Cloud API configuration (Bedrock)
CLOUD_API_CONFIG = {
    "region_name": "us-west-2",
    "model_id": "amazon.claude-3-sonnet-20240229-v1:0",
    "max_tokens": 1024,
    "temperature": 0.7,
    "top_p": 0.95,
    "daily_quota": 10000  # Maximum tokens per day
}

# Logging configuration
LOGGING_CONFIG = {
    "log_level": "INFO",
    "log_file": "npc_ai.log",
    "enable_request_logging": True,
    "enable_response_logging": True,
}

def get_config(section: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get configuration for a specific section.
    
    Args:
        section: The section name to get configuration for
        default: Optional default configuration if section is not found
        
    Returns:
        The configuration dictionary for the section
    """
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "npc-config.yaml")
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                if section in config:
                    return config[section]
    except Exception as e:
        logger.error(f"Error loading config: {e}")
    
    return default if default is not None else {} 