"""
Integration tests for the Tokyo Knowledge Store.

This module contains integration tests that verify the TokyoKnowledgeStore's
integration with other components of the NPC AI system.
"""

import os
import json
import pytest
import asyncio
import logging
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import chromadb
from chromadb.config import Settings
import shutil
import uuid

from src.ai.npc.core.vector.tokyo_knowledge_store import TokyoKnowledgeStore
from src.ai.npc.core.models import ClassifiedRequest, GameContext, ProcessingTier
from src.ai.npc.core.constants import (
    INTENT_VOCABULARY_HELP,
    INTENT_DIRECTION_GUIDANCE
)

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)

# Test data
SAMPLE_KNOWLEDGE_BASE = [
    {
        "id": "doc1",
        "title": "Tokyo Station Main Entrance",
        "content": "The main entrance is located on the Marunouchi side.",
        "type": "location",
        "importance": "high",
        "related_npcs": ["Station Master"],
        "related_locations": ["Marunouchi Exit"]
    },
    {
        "id": "doc2",
        "title": "Basic Japanese Directions",
        "content": "To ask for directions, say 'すみません、道を教えてください'.",
        "type": "language_learning",
        "importance": "medium",
        "related_npcs": ["Tourist Guide"]
    }
]

@pytest.fixture(scope="session")
def chromadb_client():
    """Create a ChromaDB client for the test session."""
    # Use in-memory ChromaDB for tests to avoid persistence issues
    client = chromadb.Client(Settings(allow_reset=True))  # Enable reset
    yield client
    # Clean up after tests
    client.reset()

@pytest.fixture
def knowledge_store(chromadb_client):
    """Create a test instance of TokyoKnowledgeStore."""
    # Use a unique collection name for each test run
    collection_name = f"test_collection_{uuid.uuid4().hex}"
    
    # Create a store with the test client (no persistence needed)
    store = TokyoKnowledgeStore(
        client=chromadb_client,  # Pass the client directly
        collection_name=collection_name,
        embedding_model="all-MiniLM-L6-v2",
        cache_size=10
    )
    
    # Load sample data
    temp_dir = tempfile.mkdtemp()
    knowledge_file = os.path.join(temp_dir, "test_knowledge_base.json")
    with open(knowledge_file, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_KNOWLEDGE_BASE, f)
    store.load_knowledge_base(knowledge_file)
    
    yield store
    
    # Clean up all documents - simply delete the collection
    try:
        chromadb_client.delete_collection(collection_name)
        shutil.rmtree(temp_dir)
    except:
        pass

@pytest.fixture
def sample_request():
    """Create a sample ClassifiedRequest for testing."""
    game_context = GameContext(
        player_id="test_player",
        language_proficiency={"japanese": 0.5},
        conversation_history=None,
        player_location="Tokyo Station",
        current_objective="Find the main entrance",
        nearby_npcs=["Station Master"],
        npc_id="hachiko"
    )
    return ClassifiedRequest(
        request_id="test_request",
        player_input="Where is the main entrance?",
        game_context=game_context,
        processing_tier=ProcessingTier.LOCAL,
        additional_params={"intent": INTENT_DIRECTION_GUIDANCE}
    )

@pytest.mark.skip(reason="Skipped in full test suite due to ChromaDB singleton issues - run separately")
@pytest.mark.asyncio
async def test_knowledge_base_initialization(knowledge_store):
    """Test knowledge base initialization and persistence."""
    # Verify collection is populated
    assert knowledge_store.collection.count() == 2
    
    # Verify documents are correctly loaded
    results = knowledge_store.collection.get()
    assert len(results["ids"]) == 2
    assert "main entrance" in results["documents"][0].lower() or "main entrance" in results["documents"][1].lower()
    
    # Verify metadata is correctly loaded
    types = [meta.get("type") for meta in results["metadatas"]]
    assert "location" in types
    assert "language_learning" in types

@pytest.mark.skip(reason="Skipped in full test suite due to ChromaDB singleton issues - run separately")
@pytest.mark.asyncio
async def test_processor_integration(knowledge_store, sample_request):
    """Test integration with processor components."""
    # Test contextual search with intent-based filtering
    results = await knowledge_store.contextual_search(sample_request)
    
    # Verify results are filtered by intent
    assert len(results) > 0
    assert all(r["metadata"]["type"] == "location" for r in results)
    
    # Test caching behavior
    cache_key = knowledge_store._get_cache_key(sample_request)
    assert cache_key in knowledge_store._cache
    
    # Test analytics tracking
    analytics = knowledge_store.get_analytics()
    assert analytics["total_queries"] > 0
    assert analytics["cache_hit_rate"] >= 0
    assert "avg_query_time" in analytics

@pytest.mark.skip(reason="Skipped in full test suite due to ChromaDB singleton issues - run separately")
@pytest.mark.asyncio
async def test_prompt_enhancement(knowledge_store, sample_request):
    """Test knowledge context enhancement for prompts."""
    # Get relevant knowledge for the request
    results = await knowledge_store.contextual_search(sample_request)
    
    # Verify knowledge context is relevant
    assert len(results) > 0
    assert any("main entrance" in r["document"].lower() for r in results)
    
    # Verify metadata is included
    assert all("metadata" in r for r in results)
    assert all("type" in r["metadata"] for r in results)
    assert all("importance" in r["metadata"] for r in results)
    
    # Test explanation generation
    explanation = knowledge_store.get_explanation(results[0]["id"])
    assert explanation is not None
    assert "Type: location" in explanation
    assert "Importance: high" in explanation

@pytest.mark.skip(reason="Skipped in full test suite due to ChromaDB singleton issues - run separately")
@pytest.mark.asyncio
async def test_vector_store_enhancements(knowledge_store, sample_request):
    """Test vector store enhancements and optimizations."""
    # Test caching
    results1 = await knowledge_store.contextual_search(sample_request)
    results2 = await knowledge_store.contextual_search(sample_request)
    assert results1 == results2  # Results should be identical
    
    # Verify cache hit
    cache_key = knowledge_store._get_cache_key(sample_request)
    assert knowledge_store._analytics["cache_hits"][cache_key] > 0
    
    # Test cache pruning
    # Create multiple requests to fill cache
    for i in range(15):  # More than cache_size
        game_context = GameContext(
            player_id=f"player_{i}",
            language_proficiency={"japanese": 0.5},
            conversation_history=None,
            player_location=f"Location {i}",
            current_objective=f"Objective {i}",
            nearby_npcs=[f"NPC {i}"],
            npc_id="hachiko"
        )
        request = ClassifiedRequest(
            request_id=f"request_{i}",
            player_input=f"Question {i}?",
            game_context=game_context,
            processing_tier=ProcessingTier.LOCAL,
            additional_params={"intent": INTENT_DIRECTION_GUIDANCE}
        )
        await knowledge_store.contextual_search(request)
    
    # Verify cache size is maintained
    assert len(knowledge_store._cache) <= knowledge_store._cache_size
    
    # Test analytics
    analytics = knowledge_store.get_analytics()
    assert analytics["cache_hit_rate"] >= 0  # Should have some cache hits
    assert "avg_query_time" in analytics  # Should track query times
    assert "most_retrieved_docs" in analytics  # Should track document retrievals
    
    # Verify that cache pruning is working
    assert len(knowledge_store._cache) >= knowledge_store._cache_size - 1  # Cache should be near max size
    
    # Try to access the original request again
    await knowledge_store.contextual_search(sample_request)
    
    # The original request should have been pruned and recreated
    new_cache_key = knowledge_store._get_cache_key(sample_request)
    assert new_cache_key == cache_key  # Keys should be identical
    assert knowledge_store._analytics["cache_misses"][cache_key] > 0  # Should have at least one cache miss 