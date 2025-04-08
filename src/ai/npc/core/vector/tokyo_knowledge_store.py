"""
Tokyo Knowledge Store

This module provides a vector database implementation for storing and retrieving
contextual information about the Tokyo train station adventure game.
"""

import os
import json
import uuid
import logging
from typing import List, Dict, Any, Optional, Union
from collections import Counter, defaultdict
from datetime import datetime

import chromadb
from chromadb.utils import embedding_functions

from src.ai.npc.core.models import ClassifiedRequest
from src.ai.npc.core.constants import (
    INTENT_VOCABULARY_HELP,
    INTENT_DIRECTION_GUIDANCE
)

logger = logging.getLogger(__name__)


class TokyoKnowledgeStore:
    """
    Vector database for storing and retrieving Tokyo train station knowledge.
    
    This class provides methods for loading knowledge from a JSON file,
    searching for relevant information, and retrieving contextual information
    based on the current game state.
    """
    
    def __init__(
        self,
        collection_name: str = "tokyo_knowledge_base",
        persist_directory: Optional[str] = None,
        embedding_model: str = "all-MiniLM-L6-v2",
        cache_size: int = 100
    ):
        """
        Initialize the knowledge store.
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Optional directory to persist the database
            embedding_model: Name of the sentence-transformers model to use
            cache_size: Maximum number of queries to cache
        """
        # Initialize the ChromaDB client
        if persist_directory:
            logger.debug(f"Initializing persistent ChromaDB client at {persist_directory}")
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            logger.debug("Initializing ephemeral ChromaDB client")
            self.client = chromadb.EphemeralClient()
            
        # Define the embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        
        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
        
        # Initialize caching and analytics
        self._cache = {}
        self._cache_size = cache_size
        self._analytics = {
            'query_counts': Counter(),
            'cache_hits': Counter(),
            'cache_misses': Counter(),
            'query_times': defaultdict(list),
            'document_retrievals': Counter()
        }
        
        logger.info(f"Initialized TokyoKnowledgeStore with collection: {collection_name}")
        
        # Check if the collection is empty and log its state
        count = self.collection.count()
        if count == 0:
            logger.warning(f"Collection {collection_name} is empty - needs to be populated")
        else:
            logger.info(f"Collection {collection_name} contains {count} documents")
    
    @classmethod
    def from_file(
        cls,
        knowledge_base_path: str,
        collection_name: str = "tokyo_knowledge_base",
        persist_directory: Optional[str] = None,
        embedding_model: str = "all-MiniLM-L6-v2"
    ) -> "TokyoKnowledgeStore":
        """
        Create a knowledge store from a file.
        
        Args:
            knowledge_base_path: Path to the knowledge base JSON file
            collection_name: Name of the ChromaDB collection
            persist_directory: Optional directory to persist the database
            embedding_model: Name of the sentence-transformers model to use
            
        Returns:
            Initialized TokyoKnowledgeStore with loaded data
        """
        store = cls(
            collection_name=collection_name,
            persist_directory=persist_directory,
            embedding_model=embedding_model
        )
        
        # Check if the collection is empty, and if so, load the knowledge base
        if store.collection.count() == 0:
            logger.info(f"Loading knowledge base from {knowledge_base_path}")
            store.load_knowledge_base(knowledge_base_path)
        else:
            logger.info(f"Collection already contains {store.collection.count()} documents, skipping load")
        
        return store
    
    def load_knowledge_base(self, file_path: str) -> int:
        """
        Load documents from the Tokyo knowledge base JSON file.
        
        Args:
            file_path: Path to the tokyo-train-knowledge-base.json file
            
        Returns:
            Number of documents loaded
            
        Raises:
            OSError: If the file cannot be found or accessed
            json.JSONDecodeError: If the file is not valid JSON
        """
        logger.debug(f"Attempting to load knowledge base from {file_path}")
        
        try:
            logger.debug(f"Opening file {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                logger.debug("File opened successfully, attempting to parse JSON")
                knowledge_base = json.load(f)
                
            # Check if the collection is already populated
            if self.collection.count() > 0:
                logger.info(f"Collection already contains {self.collection.count()} documents, skipping load")
                return 0
                
            # Transform knowledge base entries into documents
            documents = []
            metadatas = []
            ids = []
            
            for i, entry in enumerate(knowledge_base):
                # Create document text from content (title + content)
                document = f"{entry['title']}:\n{entry['content']}"
                
                # Create metadata
                metadata = {
                    "title": entry["title"],
                    "type": entry.get("type", "general"),
                    "importance": entry.get("importance", "medium")
                }
                
                # Add any other metadata fields that exist
                for key, value in entry.items():
                    if key not in ["title", "type", "importance", "content"]:
                        # Handle special case for lists in metadata (Chroma doesn't support them directly)
                        if isinstance(value, list):
                            metadata[key] = json.dumps(value)
                        else:
                            metadata[key] = value
                
                # Create ID (either use existing or create a new one)
                doc_id = entry.get("id", f"doc_{i}_{uuid.uuid4().hex[:8]}")
                
                documents.append(document)
                metadatas.append(metadata)
                ids.append(doc_id)
            
            # Add documents to the collection
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Loaded {len(documents)} documents from Tokyo knowledge base")
            return len(documents)
            
        except FileNotFoundError as e:
            logger.error(f"File not found: {file_path}")
            raise OSError(f"No such file or directory: {file_path}") from e
        except (OSError, IOError) as e:
            logger.error(f"Error accessing knowledge base file: {e}")
            raise OSError(f"Error accessing knowledge base file: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing knowledge base JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading knowledge base: {e}")
            raise
    
    def search(
        self,
        query: str,
        top_k: int = 3,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents.
        
        Args:
            query: The search query
            top_k: Maximum number of results to return
            filters: Optional filters to apply (e.g., {"type": "language_learning"})
            
        Returns:
            List of documents with metadata and scores
        """
        # Query the collection
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=filters,
            include=["documents", "metadatas", "distances"]
        )
        
        # Process the results
        processed_results = []
        
        # Chroma DB returns results in a nested structure, handle both formats for robustness
        if results["ids"] and len(results["ids"]) > 0:
            # Get the first set of results (for the first query)
            ids = results["ids"][0] if isinstance(results["ids"][0], list) else results["ids"]
            distances = results["distances"][0] if isinstance(results["distances"][0], list) else results["distances"]
            documents = results["documents"][0] if isinstance(results["documents"][0], list) else results["documents"]
            metadatas = results["metadatas"][0] if isinstance(results["metadatas"][0], list) else results["metadatas"]
            
            # Process each item in the results
            for i in range(len(ids)):
                processed_results.append({
                    "id": ids[i],
                    "document": documents[i],
                    "metadata": metadatas[i],
                    "score": 1.0 - distances[i]  # Convert distance to similarity score
                })
        
        logger.debug(f"Found {len(processed_results)} relevant documents for query: {query}")
        return processed_results
    
    def _get_cache_key(self, request: ClassifiedRequest, additional_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a cache key for a request.
        
        Args:
            request: The classified request
            additional_context: Optional additional context
            
        Returns:
            A string cache key
        """
        key_parts = [
            request.player_input,
            request.game_context.player_location if request.game_context else None,
            request.additional_params.get("intent") if request.additional_params else None,
            str(additional_context) if additional_context else None
        ]
        return "|".join(str(part) for part in key_parts if part is not None)
    
    def _update_analytics(self, cache_key: str, hit: bool, query_time: float):
        """
        Update analytics for a query.
        
        Args:
            cache_key: The cache key used
            hit: Whether it was a cache hit
            query_time: Time taken for the query
        """
        self._analytics['query_counts'][cache_key] += 1
        if hit:
            self._analytics['cache_hits'][cache_key] += 1
        else:
            self._analytics['cache_misses'][cache_key] += 1
        self._analytics['query_times'][cache_key].append(query_time)
    
    def get_analytics(self) -> Dict[str, Any]:
        """
        Get current analytics data.
        
        Returns:
            Dictionary containing analytics data
        """
        return {
            'total_queries': sum(self._analytics['query_counts'].values()),
            'cache_hit_rate': (
                sum(self._analytics['cache_hits'].values()) / 
                sum(self._analytics['query_counts'].values())
                if sum(self._analytics['query_counts'].values()) > 0 else 0
            ),
            'avg_query_time': {
                key: sum(times) / len(times)
                for key, times in self._analytics['query_times'].items()
                if times
            },
            'most_retrieved_docs': dict(
                self._analytics['document_retrievals'].most_common(10)
            )
        }
    
    def _prune_cache(self):
        """Prune the cache if it exceeds the size limit."""
        if len(self._cache) >= self._cache_size:
            # Get all entries sorted by usage count
            sorted_entries = sorted(
                self._analytics['query_counts'].items(),
                key=lambda x: x[1]
            )
            
            # Remove entries until we're under the size limit
            while len(self._cache) >= self._cache_size and sorted_entries:
                least_used = sorted_entries.pop(0)[0]
                del self._cache[least_used]
                del self._analytics['query_counts'][least_used]
                del self._analytics['cache_hits'][least_used]
                del self._analytics['cache_misses'][least_used]
                del self._analytics['query_times'][least_used]
                logger.debug(f"Pruned cache entry: {least_used}")
    
    async def contextual_search(
        self,
        request: ClassifiedRequest,
        additional_context: Optional[Dict[str, Any]] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents based on the current game context.
        
        Args:
            request: The classified request containing player input and game context
            additional_context: Optional additional context to include in the search
            top_k: Maximum number of results to return
            
        Returns:
            List of documents with metadata and scores
            
        Raises:
            AttributeError: If the request is None or invalid
        """
        if request is None:
            raise AttributeError("Request cannot be None")
            
        start_time = datetime.now()
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(request, additional_context)
            if cache_key in self._cache:
                self._update_analytics(cache_key, hit=True, query_time=0.0)
                return self._cache[cache_key]
            
            # Build filters based on intent and context
            filters = {}
            
            # Add intent-based filters
            intent = request.additional_params.get("intent")
            if intent == INTENT_VOCABULARY_HELP:
                filters["type"] = "language_learning"
            elif intent == INTENT_DIRECTION_GUIDANCE:
                filters["type"] = "location"
            
            # Build search query
            query_parts = [request.player_input]
            
            # Add objective if available
            if request.game_context and request.game_context.current_objective:
                query_parts.append(request.game_context.current_objective)
            
            # Add additional context if provided
            if additional_context:
                query_parts.extend(str(v) for v in additional_context.values())
            
            # Perform search
            query = " ".join(query_parts)
            results = self.search(query, top_k=top_k, filters=filters)
            
            # Update cache and analytics
            self._cache[cache_key] = results
            self._prune_cache()
            
            query_time = (datetime.now() - start_time).total_seconds()
            self._update_analytics(cache_key, hit=False, query_time=query_time)
            
            # Update document retrieval counts
            for result in results:
                self._analytics["document_retrievals"][result["id"]] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"Error in contextual search: {e}")
            raise
    
    def get_explanation(self, doc_id: str) -> Optional[str]:
        """
        Get a human-readable explanation for a document.
        
        Args:
            doc_id: The document ID
            
        Returns:
            A string explanation or None if document not found
        """
        try:
            # Get the document metadata
            results = self.collection.get(
                ids=[doc_id],
                include=["metadatas"]
            )
            
            if not results["metadatas"]:
                return None
                
            metadata = results["metadatas"][0]
            
            # Format the explanation
            parts = []
            
            if "type" in metadata:
                parts.append(f"Type: {metadata['type']}")
                
            if "importance" in metadata:
                parts.append(f"Importance: {metadata['importance']}")
                
            if "related_npcs" in metadata:
                npcs = json.loads(metadata["related_npcs"])
                parts.append(f"Related NPCs: {', '.join(npcs)}")
                
            if "related_locations" in metadata:
                locations = json.loads(metadata["related_locations"])
                parts.append(f"Related locations: {', '.join(locations)}")
                
            return " | ".join(parts)
            
        except Exception as e:
            logger.error(f"Error getting explanation for document {doc_id}: {e}")
            return None 