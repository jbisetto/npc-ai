"""
Test data factories for creating test objects.

This module provides factory functions for creating test data objects
like requests, contexts, and other commonly needed test fixtures.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from src.ai.npc.core.models import (
    ClassifiedRequest,
    GameContext,
    ProcessingTier,
    ConversationContext,
    CompanionResponse
)
from src.ai.npc.core.constants import METADATA_KEY_INTENT, INTENT_DEFAULT


def create_test_game_context(
    player_id: str = "test_player",
    language_level: Dict[str, float] = None,
    **kwargs
) -> GameContext:
    """
    Create a GameContext instance for testing.
    
    Args:
        player_id: Player identifier
        language_level: Dictionary of language proficiency scores
        **kwargs: Additional fields to override
        
    Returns:
        A GameContext instance
    """
    if language_level is None:
        language_level = {"JLPT": 5, "speaking": 0.3, "listening": 0.4}
        
    context_data = {
        "player_id": player_id,
        "language_proficiency": language_level,
        **kwargs
    }
    
    return GameContext(**context_data)


def create_test_request(
    request_id: str = "test_req_001",
    player_input: str = "Where is the ticket gate?",
    game_context: Optional[GameContext] = None,
    processing_tier: ProcessingTier = ProcessingTier.LOCAL,
    request_type: str = "navigation",
    confidence: float = 1.0,
    **kwargs
) -> ClassifiedRequest:
    """
    Create a ClassifiedRequest instance for testing.
    
    Args:
        request_id: Request identifier
        player_input: The player's input text
        game_context: Optional GameContext instance
        processing_tier: The processing tier to use
        request_type: Type of request
        confidence: Classification confidence
        **kwargs: Additional fields to override
        
    Returns:
        A ClassifiedRequest instance
    """
    if game_context is None:
        game_context = create_test_game_context()
        
    # Default additional parameters
    default_params = {
        "name": "Test NPC",
        METADATA_KEY_INTENT: INTENT_DEFAULT
    }
    
    # Merge with any provided additional parameters
    additional_params = kwargs.pop("additional_params", {})
    default_params.update(additional_params)
        
    request_data = {
        "request_id": request_id,
        "player_input": player_input,
        "game_context": game_context,
        "processing_tier": processing_tier,
        "request_type": request_type,
        "confidence": confidence,
        "timestamp": datetime.now(),
        "extracted_entities": {},
        "additional_params": default_params,
        **kwargs
    }
    
    return ClassifiedRequest(**request_data)


def create_test_conversation_context(
    player_id: str = "test_player",
    player_language_level: Dict[str, float] = None,
    conversation_history: Optional[list] = None,
    **kwargs
) -> ConversationContext:
    """
    Create a ConversationContext instance for testing.
    
    Args:
        player_id: Player identifier
        player_language_level: Dictionary of language proficiency scores
        conversation_history: Optional list of conversation entries
        **kwargs: Additional fields to override
        
    Returns:
        A ConversationContext instance
    """
    if player_language_level is None:
        player_language_level = {"JLPT": 5, "speaking": 0.3, "listening": 0.4}
        
    if conversation_history is None:
        conversation_history = []
        
    context_data = {
        "player_id": player_id,
        "player_language_level": player_language_level,
        "conversation_history": conversation_history,
        **kwargs
    }
    
    return ConversationContext(**context_data)


def create_test_response(
    request_id: str = "test_req_001",
    response_text: str = "The ticket gate is straight ahead.",
    processing_tier: ProcessingTier = ProcessingTier.LOCAL,
    suggested_actions: Optional[List[str]] = None,
    learning_cues: Optional[Dict[str, Any]] = None,
    emotion: str = "neutral",
    confidence: float = 1.0,
    debug_info: Optional[Dict[str, Any]] = None,
    **kwargs
) -> CompanionResponse:
    """
    Create a CompanionResponse instance for testing.
    
    Args:
        request_id: Request identifier
        response_text: The response text
        processing_tier: The processing tier used
        suggested_actions: Optional list of suggested actions
        learning_cues: Optional dictionary of learning cues
        emotion: Response emotion
        confidence: Response confidence
        debug_info: Optional debug information
        **kwargs: Additional fields to override
        
    Returns:
        A CompanionResponse instance
    """
    response_data = {
        "request_id": request_id,
        "response_text": response_text,
        "processing_tier": processing_tier,
        "suggested_actions": suggested_actions or [],
        "learning_cues": learning_cues or {},
        "emotion": emotion,
        "confidence": confidence,
        "debug_info": debug_info or {},
        "timestamp": datetime.now(),
        **kwargs
    }
    
    return CompanionResponse(**response_data) 