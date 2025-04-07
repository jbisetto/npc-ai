"""
Standalone formatter module.

This module provides a simple formatter for responses that doesn't require
any external dependencies or complex formatting rules.
"""

from typing import Optional
from src.ai.npc.core.models import ClassifiedRequest
from src.ai.npc.core.constants import (
    METADATA_KEY_INTENT,
    INTENT_DEFAULT,
    RESPONSE_FORMAT_DEFAULT
)

def format_response(response: Optional[str], request: ClassifiedRequest) -> str:
    """
    Format a response in a simple way.

    Args:
        response: The response to format.
        request: The request that generated the response.

    Returns:
        The formatted response.
    """
    if response is None:
        return ""

    # Strip whitespace
    formatted = response.strip()

    # Return empty string if response is empty
    if not formatted:
        return ""

    return formatted 