"""
NPC profiles endpoint
"""

import logging
from fastapi import APIRouter
from api.models.requests import NPCProfile, NPCListResponse
from typing import List

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1",
    tags=["npcs"],
    responses={404: {"description": "Not found"}},
)

# NPC profiles mapping - based on the demo app's profiles
# This could be loaded from a configuration file in a real implementation
NPC_PROFILES = {
    "hachiko": {
        "id": "hachiko",
        "name": "Hachiko (Dog Companion)",
        "role": "companion",
        "personality": "helpful_bilingual_dog",
    },
    "yamada": {
        "id": "yamada",
        "name": "Yamada (Station Staff)",
        "role": "staff",
        "personality": "professional_helpful",
    },
    "tanaka": {
        "id": "tanaka",
        "name": "Tanaka (Kyoto Station Staff)",
        "role": "staff",
        "personality": "formal_helpful",
    },
    "nakamura": {
        "id": "nakamura",
        "name": "Nakamura (Odawara Station Staff)",
        "role": "staff", 
        "personality": "local_helpful",
    },
    "suzuki": {
        "id": "suzuki",
        "name": "Suzuki (Information Booth)",
        "role": "information",
        "personality": "knowledgeable_patient",
    },
    "sato": {
        "id": "sato",
        "name": "Sato (Ticket Booth)",
        "role": "ticketing",
        "personality": "efficient_helpful",
    },
}


@router.get("/npcs", response_model=NPCListResponse)
async def get_npc_profiles() -> NPCListResponse:
    """
    Get a list of available NPC profiles
    """
    logger.info("Getting NPC profiles")
    
    # Convert dictionary profiles to NPCProfile objects
    profiles = [
        NPCProfile(**profile)
        for profile in NPC_PROFILES.values()
    ]
    
    return NPCListResponse(npcs=profiles)


@router.get("/npcs/{npc_id}", response_model=NPCProfile)
async def get_npc_profile(npc_id: str) -> NPCProfile:
    """
    Get details for a specific NPC profile
    """
    logger.info(f"Getting NPC profile: {npc_id}")
    
    if npc_id not in NPC_PROFILES:
        raise ValueError(f"NPC profile not found: {npc_id}")
    
    return NPCProfile(**NPC_PROFILES[npc_id])


@router.get("/valid-npc-ids", response_model=List[str])
async def get_valid_npc_ids() -> List[str]:
    """
    Get a list of all valid NPC IDs for use with the chat endpoint
    """
    logger.info("Getting valid NPC IDs")
    
    # Import the NPCProfileType to get the valid IDs
    from src.ai.npc.core.models import NPCProfileType
    
    # Extract all valid IDs from the enum
    valid_npc_ids = [member.value for member in NPCProfileType]
    
    return valid_npc_ids 