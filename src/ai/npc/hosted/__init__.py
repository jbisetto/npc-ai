"""
Initialize the hosted module.

This module contains the hosted processor and its dependencies.
"""

from src.ai.npc.hosted.bedrock_client import BedrockClient, BedrockError
from src.ai.npc.hosted.hosted_processor import HostedProcessor
from src.ai.npc.hosted.prompt_optimizer import create_optimized_prompt
from src.ai.npc.hosted.scenario_detection import ScenarioDetector, ScenarioType
from src.ai.npc.hosted.specialized_handlers import (
    VocabularyHelpHandler,
    TicketPurchaseHandler,
    NavigationHandler,
    GrammarExplanationHandler,
    CulturalInformationHandler,
    DefaultHandler
)
from src.ai.npc.hosted.usage_tracker import UsageTracker

__all__ = [
    'BedrockClient',
    'BedrockError',
    'HostedProcessor',
    'create_optimized_prompt',
    'ScenarioDetector',
    'ScenarioType',
    'VocabularyHelpHandler',
    'TicketPurchaseHandler',
    'NavigationHandler',
    'GrammarExplanationHandler',
    'CulturalInformationHandler',
    'DefaultHandler',
    'UsageTracker'
] 