"""
Initialize the hosted module.

This module contains the hosted processor and its dependencies.
"""

from src.ai.npc.hosted.bedrock_client import BedrockClient, BedrockError
from src.ai.npc.hosted.hosted_processor import HostedProcessor
from src.ai.npc.core.prompt_manager import PromptManager
from src.ai.npc.hosted.specialized_handlers import (
    SpecializedHandler,
    LocalHandler,
    HostedHandler,
    HandlerRegistry
)
from src.ai.npc.hosted.usage_tracker import UsageTracker

__all__ = [
    'BedrockClient',
    'BedrockError',
    'HostedProcessor',
    'PromptManager',
    'SpecializedHandler',
    'LocalHandler',
    'HostedHandler',
    'HandlerRegistry',
    'UsageTracker'
] 