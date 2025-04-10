"""
NPC AI - Data Models

This module defines the data models used by the AI system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum, auto
import datetime
from pydantic import BaseModel
from src.ai.npc.core.constants import (
    METADATA_KEY_INTENT,
    INTENT_DEFAULT
)


class ProcessingTier(Enum):
    """Processing tier for the request."""
    LOCAL = "local"
    HOSTED = "hosted"


class GameContext(BaseModel):
    """Context information from the game."""
    player_id: str
    language_proficiency: Dict[str, float]
    conversation_history: Optional[List[Dict[str, Any]]] = None
    player_location: Optional[str] = None
    current_objective: Optional[str] = None
    nearby_npcs: Optional[List[str]] = None
    npc_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "player_id": self.player_id,
            "language_proficiency": self.language_proficiency,
            "conversation_history": self.conversation_history,
            "player_location": self.player_location,
            "current_objective": self.current_objective,
            "nearby_npcs": self.nearby_npcs,
            "npc_id": self.npc_id
        }


class NPCRequest(BaseModel):
    """
    A request to the NPC AI system.
    
    Contains:
    - request_id: Unique identifier for the request
    - player_input: The player's text input
    - game_context: Optional game context information
    - processing_tier: Whether to process locally or via hosted services
    - additional_params: Additional parameters for processing, including:
        - intent: The classified intent of the request (string)
        - language_level: Player's language proficiency
        - current_location: Player's current location in the station
        - conversation_history: Previous conversation context
    """
    request_id: str
    player_input: str
    game_context: Optional[GameContext] = None
    processing_tier: Optional[ProcessingTier] = None
    additional_params: Dict[str, Any] = field(default_factory=lambda: {
        METADATA_KEY_INTENT: INTENT_DEFAULT
    })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "request_id": self.request_id,
            "player_input": self.player_input,
            "game_context": self.game_context.to_dict() if self.game_context else None,
            "additional_params": self.additional_params
        }
        if self.processing_tier:
            result["processing_tier"] = self.processing_tier.value
        return result


# For backward compatibility, maintain aliases to the original names
CompanionRequest = NPCRequest
ClassifiedRequest = NPCRequest


@dataclass
class CompanionResponse:
    """A response from the companion AI."""
    request_id: str
    response_text: str
    processing_tier: ProcessingTier
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    suggested_actions: List[str] = field(default_factory=list)
    learning_cues: Dict[str, Any] = field(default_factory=dict)
    emotion: str = "neutral"
    confidence: float = 1.0
    debug_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    """Context for a conversation with the companion."""
    conversation_id: str
    request_history: List[NPCRequest] = field(default_factory=list)
    response_history: List[CompanionResponse] = field(default_factory=list)
    session_start: datetime.datetime = field(default_factory=datetime.datetime.now)
    last_updated: datetime.datetime = field(default_factory=datetime.datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_interaction(self, request: NPCRequest, response: CompanionResponse):
        """Add a request-response interaction to the history."""
        self.request_history.append(request)
        self.response_history.append(response)
        self.last_updated = datetime.datetime.now() 