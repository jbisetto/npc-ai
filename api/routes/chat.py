"""
Chat endpoints for NPC interactions
"""

import logging
import uuid
from fastapi import APIRouter, HTTPException
from ..models.requests import ChatRequest, ChatResponse

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

# Store conversation IDs for user sessions
# Key: player_id -> NPC -> conversation_id mappings
conversation_sessions = {}


@router.post("/chat", response_model=ChatResponse)
async def chat_with_npc(request: ChatRequest) -> ChatResponse:
    """
    Chat with an NPC
    """
    try:
        # Import here to avoid circular imports
        from src.ai.npc import process_request
        from src.ai.npc.core.models import NPCRequest, GameContext, NPCProfileType

        # Create or retrieve conversation ID for this player-NPC pair
        if request.player_id not in conversation_sessions:
            conversation_sessions[request.player_id] = {}
            
        if request.npc_id not in conversation_sessions[request.player_id]:
            # First conversation with this NPC, create a new conversation ID
            conversation_sessions[request.player_id][request.npc_id] = str(uuid.uuid4())
            
        # Get the conversation ID for this player-NPC pair
        conversation_id = conversation_sessions[request.player_id][request.npc_id]
        logger.debug(f"Using conversation_id: {conversation_id} for player {request.player_id}")
        
        # Create a unique request ID 
        request_id = str(uuid.uuid4())
        
        # Map NPC ID string to enum (customize based on your implementation)
        try:
            # This assumes that the NPC ID in the request corresponds to a value in NPCProfileType
            npc_profile_type = NPCProfileType(request.npc_id)
        except ValueError:
            # Fallback to a default if the mapping fails
            logger.warning(f"Invalid NPC ID: {request.npc_id}, using default")
            npc_profile_type = NPCProfileType.YAMADA  # Default profile
        
        # Create game context with NPC ID
        game_context = GameContext(
            player_id=request.player_id,
            language_proficiency={
                "en": 0.8,  # English proficiency
                "ja": 0.3   # Japanese proficiency
            },
            player_location="station",  # Generic location
            current_objective="Buy ticket to Odawara",
            npc_id=npc_profile_type
        )
        
        # Create a dictionary of additional parameters
        additional_params = {
            'conversation_id': conversation_id,
            'session_id': request.session_id or str(uuid.uuid4())
        }
        
        # Create request with all necessary fields
        npc_request = NPCRequest(
            request_id=request_id,
            player_input=request.message,
            game_context=game_context,
            additional_params=additional_params
        )
        
        logger.info(f"Processing chat request: player={request.player_id}, npc={request.npc_id}")
        
        # Process using the AI components
        response = await process_request(npc_request)
        
        # Extract response text and metadata
        response_text = response.get("response_text", "I apologize, but I couldn't process your request.")
        processing_tier = response.get("processing_tier", "unknown")
        suggested_actions = response.get("suggested_actions", [])
        learning_cues = response.get("learning_cues", {})
        emotion = response.get("emotion", "neutral")
        confidence = response.get("confidence", 0.0)
        
        # Return formatted response
        return ChatResponse(
            response_text=response_text,
            processing_tier=processing_tier,
            suggested_actions=suggested_actions,
            learning_cues=learning_cues,
            emotion=emotion,
            confidence=confidence
        )
    
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@router.delete("/conversations/{player_id}")
async def clear_conversation(player_id: str):
    """
    Clear all conversations for a player
    """
    if player_id in conversation_sessions:
        del conversation_sessions[player_id]
        return {"status": "success", "message": f"Conversations cleared for player {player_id}"}
    
    return {"status": "success", "message": f"No conversations found for player {player_id}"} 