"""
Health check endpoint
"""

import logging
from fastapi import APIRouter
from ..models.requests import HealthResponse

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1",
    tags=["health"],
    responses={404: {"description": "Not found"}},
)


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Check the health of the API and its components
    """
    logger.info("Performing health check")
    
    # Default status is ok
    status = "ok"
    
    # Check local model (Ollama)
    local_model = None
    try:
        from src.ai.npc.local.ollama_client import OllamaClient
        
        # Try to initialize client (this won't make an actual API call)
        client = OllamaClient()
        local_model = True
    except Exception as e:
        logger.warning(f"Local model check failed: {e}")
        local_model = False
    
    # Check hosted model (AWS Bedrock)
    hosted_model = None
    try:
        # Simple check if AWS credentials are available
        import os
        if os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY"):
            hosted_model = True
        else:
            hosted_model = False
    except Exception as e:
        logger.warning(f"Hosted model check failed: {e}")
        hosted_model = False
    
    # Check knowledge base
    knowledge_base = None
    try:
        from src.ai.npc import get_knowledge_store
        
        # Try to get knowledge store
        store = get_knowledge_store()
        count = store.collection.count()
        knowledge_base = count > 0
    except Exception as e:
        logger.warning(f"Knowledge base check failed: {e}")
        knowledge_base = False
    
    # If any check failed, set status to degraded
    if local_model is False and hosted_model is False:
        status = "degraded_no_models"
    elif knowledge_base is False:
        status = "degraded_no_knowledge"
    
    return HealthResponse(
        status=status,
        local_model=local_model,
        hosted_model=hosted_model,
        knowledge_base=knowledge_base
    ) 