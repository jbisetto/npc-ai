"""
Data access layer for DeepSeek engine parameters.
"""

from typing import Dict, Any, Optional
import logging

# Set up logging
logger = logging.getLogger(__name__)


# Custom exceptions
class DeepSeekParametersError(Exception):
    """Base exception for DeepSeek parameters errors."""
    pass


class InvalidParameterError(DeepSeekParametersError):
    """Exception raised when a parameter is invalid."""
    pass


# In-memory storage for DeepSeek parameters (in a real implementation, this would be a database)
_deepseek_parameters: Dict[str, Any] = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 50,
    "max_tokens": 1024,
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0,
    "context_window": 4096,
    "model_version": "deepseek-chat",
    "enable_japanese_corrections": True,
    "jlpt_level_cap": "N5"
}


def get_deepseek_parameters() -> Dict[str, Any]:
    """
    Get the current DeepSeek engine parameters.
    
    Returns:
        A dictionary containing the current DeepSeek engine parameters.
    """
    return _deepseek_parameters.copy()


def update_deepseek_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the DeepSeek engine parameters.
    
    Args:
        parameters: The parameters to update.
        
    Returns:
        A dictionary containing the updated DeepSeek engine parameters.
        
    Raises:
        InvalidParameterError: If a parameter is invalid.
    """
    # Validate parameters
    for key, value in parameters.items():
        if key not in _deepseek_parameters:
            raise InvalidParameterError(f"Invalid parameter: {key}")
        
        # Additional validation for specific parameters
        if key == "temperature" and (value < 0.0 or value > 1.0):
            raise InvalidParameterError(f"Temperature must be between 0.0 and 1.0, got {value}")
        elif key == "top_p" and (value < 0.0 or value > 1.0):
            raise InvalidParameterError(f"Top-p must be between 0.0 and 1.0, got {value}")
        elif key == "top_k" and value < 1:
            raise InvalidParameterError(f"Top-k must be at least 1, got {value}")
        elif key == "max_tokens" and value < 1:
            raise InvalidParameterError(f"Max tokens must be at least 1, got {value}")
        elif key == "presence_penalty" and (value < -2.0 or value > 2.0):
            raise InvalidParameterError(f"Presence penalty must be between -2.0 and 2.0, got {value}")
        elif key == "frequency_penalty" and (value < -2.0 or value > 2.0):
            raise InvalidParameterError(f"Frequency penalty must be between -2.0 and 2.0, got {value}")
        elif key == "context_window" and value < 512:
            raise InvalidParameterError(f"Context window must be at least 512, got {value}")
        elif key == "model_version" and value not in ["deepseek-chat", "deepseek-coder", "deepseek-llm"]:
            raise InvalidParameterError(f"Model version must be one of: deepseek-chat, deepseek-coder, deepseek-llm, got {value}")
        elif key == "jlpt_level_cap" and value not in ["N5", "N4", "N3", "N2", "N1"]:
            raise InvalidParameterError(f"JLPT level cap must be one of: N5, N4, N3, N2, N1, got {value}")
    
    # Update parameters
    for key, value in parameters.items():
        _deepseek_parameters[key] = value
        logger.info(f"Updated DeepSeek parameter {key} to {value}")
    
    return _deepseek_parameters.copy() 