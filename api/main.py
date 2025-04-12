"""
FastAPI application for NPC AI
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables
load_dotenv(os.path.join(project_root, ".env"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(current_dir, "api.log"))
    ]
)

logger = logging.getLogger(__name__)

# Import routes - use absolute imports instead of relative imports
from api.routes import chat, npcs, health

# Create FastAPI application
app = FastAPI(
    title="NPC AI API",
    description="REST API for interacting with NPCs powered by AI",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(chat.router)
app.include_router(npcs.router)
app.include_router(health.router)


@app.on_event("startup")
async def startup_event():
    """
    Initialize components on startup
    """
    try:
        # Import here to avoid circular imports
        from src.ai.npc import get_knowledge_store
        
        # Get the knowledge base path
        knowledge_base_path = os.path.join(project_root, "data", "knowledge", "tokyo-train-knowledge-base.json")
        
        # Check if the knowledge base file exists
        if os.path.exists(knowledge_base_path):
            logger.info(f"Initializing knowledge base from: {knowledge_base_path}")
            
            # Initialize the knowledge store
            store = get_knowledge_store()
            await store.from_file(knowledge_base_path)
            
            # Log analytics
            logger.info(f"Knowledge store initialized with {store.collection.count()} documents")
        else:
            logger.warning(f"Knowledge base file not found: {knowledge_base_path}")
        
    except Exception as e:
        logger.error(f"Error initializing knowledge base: {e}")


@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "name": "NPC AI API",
        "version": "0.1.0",
        "description": "REST API for interacting with NPCs powered by AI",
        "endpoints": [
            {"path": "/api/v1/chat", "description": "Chat with an NPC"},
            {"path": "/api/v1/npcs", "description": "Get available NPC profiles"},
            {"path": "/api/v1/health", "description": "Check system health"}
        ]
    } 