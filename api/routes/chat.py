"""
Chat endpoints for NPC interactions
"""

import logging
import uuid
import os
from fastapi import APIRouter, HTTPException
from api.models.requests import ChatRequest, ChatResponse

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
        # Check if we're running in Docker and set Ollama URL if needed
        if os.path.exists('/.dockerenv'):
            logger.info("Running in Docker, setting host.docker.internal for Ollama")
            os.environ["OLLAMA_BASE_URL"] = "http://host.docker.internal:11434"
        
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
        
        # Define valid NPC IDs as per NPCProfileType enum
        valid_npc_ids = [member.value for member in NPCProfileType]
        
        # Check if the requested NPC ID is valid
        if request.npc_id not in valid_npc_ids:
            # Return a response indicating invalid NPC ID
            logger.warning(f"Invalid NPC ID: {request.npc_id}")
            return ChatResponse(
                response_text=f"No NPC profile found for ID: {request.npc_id}. Valid IDs are: {', '.join(valid_npc_ids)}",
                processing_tier="error",
                emotion="neutral",
                confidence=0.0
            )
        
        # Map NPC ID string to enum (now we know it's valid)
        npc_profile_type = NPCProfileType(request.npc_id)
        
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
        
        # Return a graceful error response
        return ChatResponse(
            response_text=f"I'm sorry, I'm having technical difficulties right now. The error was: {str(e)}",
            processing_tier="error",
            suggested_actions=["Try again later", "Check if Ollama is running on your host machine"],
            emotion="concerned",
            confidence=0.0
        )


@router.delete("/conversations/{player_id}")
async def clear_conversation(player_id: str):
    """
    Clear all conversations for a player
    """
    if player_id in conversation_sessions:
        del conversation_sessions[player_id]
        return {"status": "success", "message": f"Conversations cleared for player {player_id}"}
    
    return {"status": "success", "message": f"No conversations found for player {player_id}"} 