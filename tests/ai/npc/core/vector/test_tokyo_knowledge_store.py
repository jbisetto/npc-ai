"""
Tests for the Tokyo Knowledge Store.

This module contains tests for the TokyoKnowledgeStore class, which provides
vector database functionality for storing and retrieving contextual information
about the Tokyo train station adventure game.
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
from src.ai.npc.core.models import NPCProfileType

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
    client = chromadb.Client(
        Settings(allow_reset=True),  # Enable reset
        tenant="unit_test_tenant",
        database="unit_test_db"
    )
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
    yield store
    # Clean up all documents - simply delete the collection
    try:
        chromadb_client.delete_collection(collection_name)
    except:
        pass

@pytest.fixture
def sample_request():
    """Create a sample ClassifiedRequest for testing."""
    game_context = GameContext(
        player_id="test_player",
        language_proficiency={"JLPT": 5},
        conversation_history=None,
        player_location="Tokyo Station",
        current_objective="Find the main entrance",
        nearby_npcs=["Station Master"],
        npc_id=NPCProfileType.HACHIKO
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
async def test_initialization(knowledge_store):
    """Test knowledge store initialization."""
    assert knowledge_store.collection is not None
    assert knowledge_store._cache == {}
    assert knowledge_store._cache_size == 10
    # Check that the analytics structure exists with the right keys
    assert "total_queries" in knowledge_store._analytics
    assert "cache_hits" in knowledge_store._analytics
    assert "query_times" in knowledge_store._analytics
    assert "retrieved_docs" in knowledge_store._analytics

@pytest.mark.skip(reason="Skipped in full test suite due to ChromaDB singleton issues - run separately")
@pytest.mark.asyncio
async def test_load_knowledge_base(knowledge_store, tmp_path):
    """Test loading knowledge base from file."""
    # Create a temporary knowledge base file
    knowledge_file = tmp_path / "test_knowledge_base.json"
    with open(knowledge_file, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_KNOWLEDGE_BASE, f)
    
    # Load the knowledge base
    doc_count = knowledge_store.load_knowledge_base(str(knowledge_file))
    
    assert doc_count == 2
    assert knowledge_store.collection.count() == 2

@pytest.mark.skip(reason="Skipped in full test suite due to ChromaDB singleton issues - run separately")
@pytest.mark.asyncio
async def test_contextual_search(knowledge_store, sample_request, tmp_path):
    """Test contextual search functionality."""
    # Create and load test data
    knowledge_file = tmp_path / "test_knowledge_base.json"
    with open(knowledge_file, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_KNOWLEDGE_BASE, f)
    knowledge_store.load_knowledge_base(str(knowledge_file))
    
    # Perform search
    results = await knowledge_store.contextual_search(sample_request)
    
    assert len(results) > 0
    assert all("document" in result for result in results)
    assert all("metadata" in result for result in results)

@pytest.mark.skip(reason="Skipped in full test suite due to ChromaDB singleton issues - run separately")
@pytest.mark.asyncio
async def test_caching(knowledge_store, sample_request, tmp_path):
    """Test caching functionality."""
    # Create and load test data
    knowledge_file = tmp_path / "test_knowledge_base.json"
    with open(knowledge_file, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_KNOWLEDGE_BASE, f)
    knowledge_store.load_knowledge_base(str(knowledge_file))
    
    # First search (should miss cache)
    results1 = await knowledge_store.contextual_search(sample_request)
    assert knowledge_store._analytics["cache_misses"][knowledge_store._get_cache_key(sample_request)] == 1
    
    # Second search (should hit cache)
    results2 = await knowledge_store.contextual_search(sample_request)
    assert knowledge_store._analytics["cache_hits"][knowledge_store._get_cache_key(sample_request)] == 1
    assert results1 == results2

@pytest.mark.skip(reason="Skipped in full test suite due to ChromaDB singleton issues - run separately")
@pytest.mark.asyncio
async def test_cache_pruning(knowledge_store, tmp_path):
    """Test cache pruning when size limit is reached."""
    # Create and load test data
    knowledge_file = tmp_path / "test_knowledge_base.json"
    with open(knowledge_file, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_KNOWLEDGE_BASE, f)
    knowledge_store.load_knowledge_base(str(knowledge_file))
    
    # Create multiple requests to fill cache
    requests = []
    for i in range(15):  # More than cache_size
        game_context = GameContext(
            player_id=f"player_{i}",
            language_proficiency={"JLPT": 5},
            conversation_history=None,
            player_location=f"Location {i}",
            current_objective=f"Objective {i}",
            nearby_npcs=[f"NPC {i}"],
            npc_id=NPCProfileType.HACHIKO
        )
        request = ClassifiedRequest(
            request_id=f"request_{i}",
            player_input=f"Question {i}?",
            game_context=game_context,
            processing_tier=ProcessingTier.LOCAL,
            additional_params={"intent": INTENT_DIRECTION_GUIDANCE}
        )
        requests.append(request)
    
    # Perform searches
    for request in requests:
        await knowledge_store.contextual_search(request)
    
    # Verify cache size
    assert len(knowledge_store._cache) <= knowledge_store._cache_size

@pytest.mark.skip(reason="Skipped in full test suite due to ChromaDB singleton issues - run separately")
@pytest.mark.asyncio
async def test_analytics(knowledge_store, sample_request, tmp_path):
    """Test analytics tracking."""
    # Create and load test data
    knowledge_file = tmp_path / "test_knowledge_base.json"
    with open(knowledge_file, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_KNOWLEDGE_BASE, f)
    knowledge_store.load_knowledge_base(str(knowledge_file))
    
    # Perform multiple searches
    for _ in range(3):
        await knowledge_store.contextual_search(sample_request)
    
    # Get analytics
    analytics = knowledge_store.get_analytics()
    
    assert analytics["total_queries"] == 3
    assert analytics["cache_hit_rate"] > 0
    assert "avg_query_time" in analytics
    assert "most_retrieved_docs" in analytics

@pytest.mark.skip(reason="Skipped in full test suite due to ChromaDB singleton issues - run separately")
@pytest.mark.asyncio
async def test_get_explanation(knowledge_store, tmp_path):
    """Test getting explanations for documents."""
    # Create and load test data
    knowledge_file = tmp_path / "test_knowledge_base.json"
    with open(knowledge_file, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_KNOWLEDGE_BASE, f)
    knowledge_store.load_knowledge_base(str(knowledge_file))
    
    # Get explanation for a known document
    explanation = knowledge_store.get_explanation("doc1")
    assert explanation is not None
    assert "Type: location" in explanation
    assert "Importance: high" in explanation
    assert "Related NPCs: Station Master" in explanation

@pytest.mark.skip(reason="Skipped in full test suite due to ChromaDB singleton issues - run separately")
@pytest.mark.asyncio
async def test_intent_based_filtering(knowledge_store, tmp_path):
    """Test filtering based on intent."""
    # Create and load test data
    knowledge_file = tmp_path / "test_knowledge_base.json"
    with open(knowledge_file, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_KNOWLEDGE_BASE, f)
    knowledge_store.load_knowledge_base(str(knowledge_file))
    
    # Create requests with different intents
    game_context = GameContext(
        player_id="test_player",
        language_proficiency={"JLPT": 5},
        conversation_history=None,
        player_location="Tokyo Station",
        current_objective="Learn Japanese",
        nearby_npcs=["Tourist Guide"],
        npc_id=NPCProfileType.HACHIKO
    )
    
    # Language learning request
    lang_request = ClassifiedRequest(
        request_id="lang_request",
        player_input="How do I ask for directions?",
        game_context=game_context,
        processing_tier=ProcessingTier.LOCAL,
        additional_params={"intent": INTENT_VOCABULARY_HELP}
    )
    
    # Direction request
    dir_request = ClassifiedRequest(
        request_id="dir_request",
        player_input="Where is the main entrance?",
        game_context=game_context,
        processing_tier=ProcessingTier.LOCAL,
        additional_params={"intent": INTENT_DIRECTION_GUIDANCE}
    )
    
    # Get results for both requests
    lang_results = await knowledge_store.contextual_search(lang_request)
    dir_results = await knowledge_store.contextual_search(dir_request)
    
    # Verify language learning documents are prioritized for language requests
    lang_docs = [r for r in lang_results if r["metadata"]["type"] == "language_learning"]
    assert len(lang_docs) > 0  # Should get at least 1 language learning doc
    
    # Verify location documents are prioritized for direction requests
    dir_docs = [r for r in dir_results if r["metadata"]["type"] == "location"]
    assert len(dir_docs) > 0  # Should get at least 1 location doc

@pytest.mark.skip(reason="Skipped in full test suite due to ChromaDB singleton issues - run separately")
@pytest.mark.asyncio
async def test_error_handling(knowledge_store, tmp_path):
    """Test error handling in various operations."""
    # Test loading non-existent file
    nonexistent_file = tmp_path / "nonexistent.json"
    logging.debug(f"Attempting to load non-existent file: {nonexistent_file}")
    logging.debug(f"File exists: {nonexistent_file.exists()}")
    logging.debug(f"File is file: {nonexistent_file.is_file()}")
    
    with pytest.raises(OSError) as exc_info:
        knowledge_store.load_knowledge_base(str(nonexistent_file))
    assert "No such file or directory" in str(exc_info.value)
    
    # Test getting explanation for non-existent document
    explanation = knowledge_store.get_explanation("nonexistent_doc")
    assert explanation is None
    
    # Test search with invalid request
    with pytest.raises(AttributeError):
        await knowledge_store.contextual_search(None) 