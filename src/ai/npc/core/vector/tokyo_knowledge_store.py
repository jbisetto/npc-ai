"""
Tokyo Knowledge Store

This module implements a knowledge store using ChromaDB for vector storage
and retrieval of contextual information.
"""

import os
import logging
import chromadb
import asyncio
import json
from typing import Dict, Any, List, Optional
from chromadb.config import Settings

from src.ai.npc.core.models import ClassifiedRequest
from src.ai.npc.core.vector.knowledge_store import KnowledgeStore
from src.ai.npc.core.constants import INTENT_VOCABULARY_HELP, INTENT_DIRECTION_GUIDANCE

logger = logging.getLogger(__name__)


class TokyoKnowledgeStore(KnowledgeStore):
    """
    Knowledge store implementation using ChromaDB.
    
    This store is specialized for the Tokyo setting, with optimizations
    for location-based and service-based knowledge retrieval.
    """
    
    def __init__(self, 
                 persist_directory: str = "knowledge_store",
                 collection_name: str = "tokyo_knowledge",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 cache_size: int = 1000,
                 client=None):
        """
        Initialize the knowledge store.
        
        Args:
            persist_directory: Directory to persist the vector store
            collection_name: Name of the collection to use
            embedding_model: Name of the embedding model to use
            cache_size: Size of the cache for query results
            client: Optional ChromaDB client to use (for testing)
        """
        self.logger = logging.getLogger(__name__)
        
        # Create or use provided ChromaDB client
        if client is not None:
            self.client = client
        else:
            self.client = chromadb.Client(Settings(
                persist_directory=persist_directory,
                anonymized_telemetry=False
            ))
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "hnsw:space": "cosine",
                "embedding_model": embedding_model
            }
        )
        
        # Initialize cache
        self._cache = {}
        self._cache_size = cache_size
        
        # Initialize analytics
        self._analytics = {
            "total_queries": 0,
            "cache_hits": {},
            "cache_misses": {},
            "query_times": [],
            "retrieved_docs": {}
        }
        
        self.logger.info(f"Initialized TokyoKnowledgeStore with {self.collection.count()} documents")
    
    async def contextual_search(self, request: ClassifiedRequest) -> List[Dict[str, Any]]:
        """
        Search for relevant knowledge context based on the request.
        
        Args:
            request: The classified request to find context for
            
        Returns:
            A list of dictionaries containing relevant knowledge context
        """
        # Check cache first
        cache_key = self._get_cache_key(request)
        if cache_key in self._cache:
            self._analytics["total_queries"] += 1
            if cache_key not in self._analytics["cache_hits"]:
                self._analytics["cache_hits"][cache_key] = 0
            self._analytics["cache_hits"][cache_key] += 1
            return self._cache[cache_key]
        
        # Get query text from request
        query = request.player_input
        
        # Get intent from metadata if available
        intent = request.additional_params.get('intent', None)
        
        start_time = asyncio.get_event_loop().time()
        
        # Prepare where clause for filtering
        where_clause = None
        if intent:
            # First try exact intent matching
            where_clause = {"intent": intent}
        
        # Search collection
        results = self.collection.query(
            query_texts=[query],
            n_results=5,
            where=where_clause
        )
        
        # Format results
        knowledge_context = []
        if results['documents'] and len(results['documents'][0]) > 0:
            for doc, metadata, id in zip(results['documents'][0], results['metadatas'][0], results['ids'][0]):
                # Track document retrieval for analytics
                if id not in self._analytics["retrieved_docs"]:
                    self._analytics["retrieved_docs"][id] = 0
                self._analytics["retrieved_docs"][id] += 1
                
                knowledge_context.append({
                    'document': doc,
                    'text': doc,  # For backward compatibility
                    'metadata': metadata,
                    'id': id
                })
        
        # Update analytics
        self._analytics["total_queries"] += 1
        query_time = asyncio.get_event_loop().time() - start_time
        self._analytics["query_times"].append(query_time)
        
        if cache_key not in self._analytics["cache_misses"]:
            self._analytics["cache_misses"][cache_key] = 0
        self._analytics["cache_misses"][cache_key] += 1
        
        # Cache results
        self._cache[cache_key] = knowledge_context
        
        # Prune cache if necessary
        if len(self._cache) > self._cache_size:
            # Remove oldest item
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        return knowledge_context

    def _get_cache_key(self, request: ClassifiedRequest) -> str:
        """Generate a cache key from a request."""
        # Use request ID and player input as the key
        return f"{request.request_id}:{request.player_input}"
    
    async def add_knowledge(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add new knowledge to the store.
        
        Args:
            text: The text content to add
            metadata: Optional metadata about the content
        """
        # Generate a unique ID for the document
        doc_id = f"doc_{self.collection.count() + 1}"
        
        # Add document to collection
        self.collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[doc_id]
        )
        
        self.logger.info(f"Added document {doc_id} to knowledge store")
    
    def load_knowledge_base(self, file_path: str) -> int:
        """
        Load knowledge base from a JSON file.
        
        Args:
            file_path: Path to the JSON file containing knowledge base
            
        Returns:
            Number of documents loaded
        
        Raises:
            OSError: If the file cannot be read
            ValueError: If the file is not a valid JSON file
        """
        self.logger.info(f"Loading knowledge base from {file_path}")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                knowledge_base = json.load(f)
        except OSError as e:
            self.logger.error(f"Error reading file: {e}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON: {e}")
            raise ValueError(f"Invalid JSON file: {e}")
        
        # Add documents to the collection
        documents = []
        metadatas = []
        ids = []
        
        for i, item in enumerate(knowledge_base):
            # Extract main content
            content = item.get("content", "")
            
            # Extract metadata
            metadata = {
                "type": item.get("type", "general"),
                "importance": item.get("importance", "medium"),
                "source": item.get("title", ""),
                "test": True  # For cleanup during tests
            }
            
            # For testing, set intent based on type
            if metadata["type"] == "location":
                metadata["intent"] = INTENT_DIRECTION_GUIDANCE
            elif metadata["type"] == "language_learning":
                metadata["intent"] = INTENT_VOCABULARY_HELP
            
            # Add optional fields to metadata, converting lists to strings
            for key in ["related_npcs", "related_locations", "intent"]:
                if key in item:
                    value = item[key]
                    # Convert lists to strings to comply with ChromaDB requirements
                    if isinstance(value, list):
                        metadata[key] = ", ".join(value)
                    else:
                        metadata[key] = value
            
            # Generate an ID
            doc_id = item.get("id", f"doc_{i+1}")
            
            documents.append(content)
            metadatas.append(metadata)
            ids.append(doc_id)
        
        # Batch add to collection
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        
        self.logger.info(f"Loaded {len(documents)} documents into knowledge store")
        return len(documents)

    def get_explanation(self, doc_id: str) -> Optional[str]:
        """
        Get an explanation for a document in the knowledge store.
        
        Args:
            doc_id: ID of the document to explain
            
        Returns:
            String explanation or None if not found
        """
        try:
            result = self.collection.get(ids=[doc_id])
            if not result["documents"]:
                return None
            
            doc = result["documents"][0]
            metadata = result["metadatas"][0]
            
            explanation = f"Document: {doc}\n"
            if "type" in metadata:
                explanation += f"Type: {metadata['type']}\n"
            if "importance" in metadata:
                explanation += f"Importance: {metadata['importance']}\n"
            if "source" in metadata:
                explanation += f"Source: {metadata['source']}\n"
            if "related_npcs" in metadata:
                explanation += f"Related NPCs: {metadata['related_npcs']}\n"
            if "related_locations" in metadata:
                explanation += f"Related Locations: {metadata['related_locations']}\n"
            
            return explanation
        except Exception as e:
            self.logger.error(f"Error getting explanation: {e}")
            return None

    def get_analytics(self) -> Dict[str, Any]:
        """
        Get analytics about the knowledge store usage.
        
        Returns:
            Dictionary with analytics data
        """
        total_queries = self._analytics["total_queries"]
        cache_hits = sum(self._analytics["cache_hits"].values())
        
        analytics = {
            "total_queries": total_queries,
            "cache_hit_rate": cache_hits / total_queries if total_queries > 0 else 0,
            "avg_query_time": sum(self._analytics["query_times"]) / len(self._analytics["query_times"]) if self._analytics["query_times"] else 0,
            "most_retrieved_docs": sorted(self._analytics["retrieved_docs"].items(), key=lambda x: x[1], reverse=True)[:5]
        }
        
        return analytics

    async def clear(self) -> None:
        """Clear all knowledge from the store."""
        self.collection.delete()
        self.collection = self.client.create_collection(
            name="tokyo_knowledge",
            metadata={"hnsw:space": "cosine"}
        )
        self.logger.info("Cleared knowledge store") 