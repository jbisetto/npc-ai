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
    "region_name": os.environ.get("AWS_REGION", "us-east-1"),
    "model_id": os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0"),
    "max_tokens": int(os.environ.get("BEDROCK_MAX_TOKENS", "1024")),
    "temperature": float(os.environ.get("BEDROCK_TEMPERATURE", "0.7")),
    "top_p": float(os.environ.get("BEDROCK_TOP_P", "0.95")),
    "daily_quota": int(os.environ.get("BEDROCK_DAILY_QUOTA", "10000"))  # Maximum tokens per day
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
    config = get_full_config()
    if section in config:
        return config[section]
    return default if default is not None else {}

def get_full_config() -> Dict[str, Any]:
    """Get the full configuration.
    
    Returns:
        The complete configuration dictionary
    """
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "npc-config.yaml")
    
    # Default configuration
    default_config = {
        'local': {
            'enabled': True,
            'model_name': LOCAL_MODEL_CONFIG.get('model_name'),
            'max_tokens': LOCAL_MODEL_CONFIG.get('max_tokens'),
            'temperature': LOCAL_MODEL_CONFIG.get('temperature')
        },
        'hosted': {
            'enabled': True,
            'bedrock': {
                'default_model': CLOUD_API_CONFIG.get('model_id'),
                'max_tokens': CLOUD_API_CONFIG.get('max_tokens'),
                'temperature': CLOUD_API_CONFIG.get('temperature'),
                'top_p': CLOUD_API_CONFIG.get('top_p'),
                'region_name': CLOUD_API_CONFIG.get('region_name')
            }
        }
    }
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                loaded_config = yaml.safe_load(f) or {}
                # Merge loaded config with defaults
                return {**default_config, **loaded_config}
    except Exception as e:
        logger.error(f"Error loading config: {e}")
    
    return default_config 