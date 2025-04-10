#!/usr/bin/env python
"""
Knowledge Base Initialization Script

This script loads the Tokyo Train Station knowledge base from a JSON file,
assigns appropriate intents to all documents, and populates the TokyoKnowledgeStore.
"""

import os
import sys
import json
import logging
import asyncio
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root directory to the Python path
project_root = str(Path(__file__).resolve().parent)
sys.path.append(project_root)

# Import the necessary modules
from src.ai.npc.core.vector.tokyo_knowledge_store import TokyoKnowledgeStore
from src.ai.npc.core.models import ClassifiedRequest, GameContext, ProcessingTier
from src.ai.npc.core.constants import (
    INTENT_VOCABULARY_HELP,
    INTENT_GRAMMAR_EXPLANATION,
    INTENT_TRANSLATION_CONFIRMATION,
    INTENT_DIRECTION_GUIDANCE,
    INTENT_GENERAL_HINT,
    INTENT_DEFAULT
)

# Path to the knowledge base JSON file
KNOWLEDGE_BASE_PATH = "src/data/knowledge/tokyo-train-knowledge-base.json"
# Make persistence directory an absolute path to ensure consistency
PERSIST_DIRECTORY = os.path.join(project_root, "data/vector_store")
logger.info(f"Using persistence directory: {PERSIST_DIRECTORY}")

# Map document types to appropriate intents
DOCUMENT_TYPE_TO_INTENT = {
    "language_learning": INTENT_VOCABULARY_HELP,
    "grammar": INTENT_GRAMMAR_EXPLANATION,
    "location": INTENT_DIRECTION_GUIDANCE,
    "gameplay_mechanic": INTENT_GENERAL_HINT,
    "character": INTENT_GENERAL_HINT,
    "quest": INTENT_DIRECTION_GUIDANCE
}

# Test queries for validating the knowledge store
TEST_QUERIES = [
    {
        "query": "Where can I buy a ticket to Odawara?",
        "expected_topics": ["ticket", "purchase", "booth"],
        "intent": INTENT_DIRECTION_GUIDANCE
    },
    {
        "query": "How do I say 'ticket' in Japanese?",
        "expected_topics": ["vocabulary", "Japanese", "ticket"],
        "intent": INTENT_VOCABULARY_HELP
    },
    {
        "query": "Where is the train platform?",
        "expected_topics": ["platform", "direction", "station"],
        "intent": INTENT_DIRECTION_GUIDANCE
    },
    {
        "query": "What are some useful Japanese phrases for the station?",
        "expected_topics": ["phrases", "Japanese", "station"],
        "intent": INTENT_GENERAL_HINT
    }
]

async def main():
    """Main function to initialize the knowledge base."""
    logger.info("Starting knowledge base initialization...")
    
    # Check if the knowledge base file exists
    if not os.path.exists(KNOWLEDGE_BASE_PATH):
        logger.error(f"Knowledge base file not found: {KNOWLEDGE_BASE_PATH}")
        sys.exit(1)
    
    try:
        # Load and process the knowledge base items
        logger.info(f"Loading knowledge base from {KNOWLEDGE_BASE_PATH}")
        with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
            knowledge_items = json.load(f)
        
        # Add or fix intents in the knowledge items
        intent_updates = 0
        for item in knowledge_items:
            item_type = item.get("type", "")
            
            # If the item doesn't have an intent field, assign one based on type
            if "intent" not in item:
                default_intent = DOCUMENT_TYPE_TO_INTENT.get(item_type, INTENT_GENERAL_HINT)
                item["intent"] = default_intent
                intent_updates += 1
                logger.debug(f"Assigned intent {default_intent} to document '{item.get('title', '')}'")
        
        logger.info(f"Updated intents for {intent_updates} documents")
        
        # Create a temporary file with the fixed knowledge base
        temp_knowledge_path = "temp_knowledge_base.json"
        with open(temp_knowledge_path, "w", encoding="utf-8") as f:
            json.dump(knowledge_items, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Prepared knowledge base with {len(knowledge_items)} documents")
        
        # Create knowledge store instance and load the fixed knowledge base
        knowledge_store = TokyoKnowledgeStore(persist_directory=PERSIST_DIRECTORY)
        documents_count = knowledge_store.load_knowledge_base(temp_knowledge_path)
        
        # Verify documents were loaded
        if documents_count > 0:
            logger.info(f"Successfully loaded {documents_count} documents into the knowledge store")
            
            # Check the collection contents
            collection_contents = knowledge_store.collection.get()
            logger.info(f"Collection contains {len(collection_contents['ids'])} documents")
            
            # Analyze document intent metadata
            intents_found = {}
            for metadata in collection_contents['metadatas']:
                intent = metadata.get('intent', None)
                if intent:
                    if intent not in intents_found:
                        intents_found[intent] = 0
                    intents_found[intent] += 1
            
            logger.info(f"Intent distribution in documents: {intents_found}")
            
            # Test each query to verify embedding quality and retrieval
            await test_embedding_quality(knowledge_store)
            
            # Clean up temporary file
            if os.path.exists(temp_knowledge_path):
                os.remove(temp_knowledge_path)
                logger.debug("Cleaned up temporary knowledge base file")
            
            # Save the knowledge items to a permanent file
            permanent_kb_path = os.path.join(project_root, "data", "processed_knowledge_base.json")
            with open(permanent_kb_path, "w", encoding="utf-8") as f:
                json.dump(knowledge_items, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved processed knowledge base to {permanent_kb_path}")
            
            # Verify that ChromaDB files were created
            chroma_files = os.listdir(PERSIST_DIRECTORY)
            logger.info(f"ChromaDB persistence directory contents: {chroma_files}")
            if not chroma_files:
                logger.warning("No files found in ChromaDB persistence directory. Data may not be persisted.")
            
            # Output collection stats
            logger.info(f"Knowledge base initialization complete. Knowledge store contains {documents_count} documents.")
            return True
        else:
            logger.warning("No documents were loaded into the knowledge store")
            return False
            
    except Exception as e:
        logger.error(f"Error initializing knowledge base: {str(e)}", exc_info=True)
        return False

async def test_embedding_quality(knowledge_store):
    """
    Test the quality of embeddings by running various test queries.
    
    Args:
        knowledge_store: The initialized TokyoKnowledgeStore instance
    """
    logger.info("=" * 50)
    logger.info("TESTING EMBEDDING QUALITY WITH SAMPLE QUERIES")
    logger.info("=" * 50)
    
    total_tests = len(TEST_QUERIES)
    passed_tests = 0
    
    for i, test_case in enumerate(TEST_QUERIES):
        query = test_case["query"]
        expected_topics = test_case["expected_topics"]
        intent = test_case.get("intent", INTENT_DEFAULT)
        
        logger.info(f"\nTest {i+1}/{total_tests}: Query: '{query}'")
        logger.info(f"Expected topics: {', '.join(expected_topics)}")
        logger.info(f"Intent: {intent}")
        
        # Test with the ClassifiedRequest
        try:
            logger.info("Testing with ClassifiedRequest (application flow)...")
            test_request = ClassifiedRequest(
                request_id=f"test-{i}",
                player_input=query,
                game_context=GameContext(
                    player_id="test-player",
                    player_location="station_entrance",
                    language_proficiency={"en": 0.8, "ja": 0.3},
                    current_objective="Buy ticket to Odawara",
                    npc_id="test_npc"
                ),
                intent=intent,
                additional_params={"intent": intent},
                processing_tier=ProcessingTier.LOCAL
            )
            
            results = await knowledge_store.contextual_search(test_request)
            
            if results and len(results) > 0:
                logger.info(f"✅ ClassifiedRequest query returned {len(results)} results")
                
                # Check first result for expected topics
                first_result = results[0]['document']
                topics_found = sum(1 for topic in expected_topics if topic.lower() in first_result.lower())
                
                if topics_found > 0:
                    logger.info(f"✅ Found {topics_found}/{len(expected_topics)} expected topics in top result")
                    logger.info(f"  Result snippet: {first_result[:150]}...")
                    passed_tests += 1
                else:
                    logger.warning(f"⚠️ None of the expected topics found in top result")
                    logger.info(f"  Result snippet: {first_result[:150]}...")
            else:
                logger.warning("❌ ClassifiedRequest query returned no results")
                
                # Try a fallback search without intent filtering
                fallback_request = ClassifiedRequest(
                    request_id=f"fallback-{i}",
                    player_input=query,
                    game_context=GameContext(
                        player_id="test-player",
                        player_location="station_entrance",
                        language_proficiency={"en": 0.8, "ja": 0.3},
                        current_objective="Buy ticket to Odawara",
                        npc_id="test_npc"
                    ),
                    intent=intent,
                    processing_tier=ProcessingTier.LOCAL
                )
                
                fallback_results = await knowledge_store.contextual_search(fallback_request)
                
                if fallback_results and len(fallback_results) > 0:
                    logger.info(f"✅ Fallback query without intent returned {len(fallback_results)} results")
                    logger.info(f"  Result snippet: {fallback_results[0]['document'][:150]}...")
                else:
                    logger.warning("❌ Both standard and fallback queries returned no results")
        except Exception as e:
            logger.error(f"Error in ClassifiedRequest test: {str(e)}")
    
    # Summarize test results
    logger.info("\n" + "=" * 50)
    logger.info(f"EMBEDDING QUALITY TEST SUMMARY: {passed_tests}/{total_tests} tests passed")
    logger.info("=" * 50)

if __name__ == "__main__":
    # Run the async main function
    success = asyncio.run(main())
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1) 