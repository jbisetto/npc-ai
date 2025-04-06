"""
NPC AI - Data Models

This module defines the data models used by the AI system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum, auto
import datetime
from pydantic import BaseModel


class ProcessingTier(Enum):
    """Processing tier for the request."""
    LOCAL = "local"
    HOSTED = "hosted"


class GameContext(BaseModel):
    """Context information from the game."""
    player_id: str
    player_location: str
    language_proficiency: Dict[str, float]
    current_quest: Optional[str] = None
    npc_id: Optional[str] = None
    conversation_history: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "player_id": self.player_id,
            "player_location": self.player_location,
            "language_proficiency": self.language_proficiency,
            "current_quest": self.current_quest,
            "npc_id": self.npc_id,
            "conversation_history": self.conversation_history
        }


class CompanionRequest(BaseModel):
    """A request to the companion AI."""
    request_id: str
    player_input: str
    game_context: Optional[GameContext] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "player_input": self.player_input,
            "game_context": self.game_context.to_dict() if self.game_context else None
        }


class ClassifiedRequest(CompanionRequest):
    """A request that has been classified."""
    processing_tier: ProcessingTier
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            "processing_tier": self.processing_tier.value,
            "metadata": self.metadata
        })
        return base_dict


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
    request_history: List[CompanionRequest] = field(default_factory=list)
    response_history: List[CompanionResponse] = field(default_factory=list)
    session_start: datetime.datetime = field(default_factory=datetime.datetime.now)
    last_updated: datetime.datetime = field(default_factory=datetime.datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_interaction(self, request: CompanionRequest, response: CompanionResponse):
        """Add a request-response interaction to the history."""
        self.request_history.append(request)
        self.response_history.append(response)
        self.last_updated = datetime.datetime.now() 