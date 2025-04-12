"""
API request and response models
"""

from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for NPC chat interactions"""
    message: str = Field(..., description="User message to the NPC")
    npc_id: str = Field(..., description="ID of the NPC to interact with")
    player_id: str = Field(..., description="ID of the player")
    session_id: Optional[str] = Field(None, description="Optional session identifier")


class ChatResponse(BaseModel):
    """Response model for NPC chat interactions"""
    response_text: str = Field(..., description="NPC's response text")
    processing_tier: str = Field(..., description="Which tier processed the request")
    suggested_actions: Optional[List[str]] = Field(None, description="Suggested next actions for the player")
    learning_cues: Optional[Dict[str, Any]] = Field(None, description="Learning cues for language learning")
    emotion: Optional[str] = Field("neutral", description="Emotional state of the NPC")
    confidence: Optional[float] = Field(None, description="Confidence score of the response")


class NPCProfile(BaseModel):
    """Model for NPC profile information"""
    id: str = Field(..., description="NPC identifier")
    name: str = Field(..., description="NPC name")
    role: str = Field(..., description="NPC role in the game")
    personality: str = Field(..., description="NPC personality traits")


class NPCListResponse(BaseModel):
    """Response model for NPC profiles list"""
    npcs: List[NPCProfile] = Field(..., description="List of available NPCs")


class HealthResponse(BaseModel):
    """Response model for health check endpoint"""
    status: str = Field(..., description="Overall status of the API")
    local_model: Optional[bool] = Field(None, description="Local model availability")
    hosted_model: Optional[bool] = Field(None, description="Hosted model availability")
    knowledge_base: Optional[bool] = Field(None, description="Knowledge base status") 