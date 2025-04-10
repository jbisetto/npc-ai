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
from typing import Dict, Any, List, Optional, Union
import numpy as np

from chromadb.config import Settings
from chromadb.utils import embedding_functions

from src.ai.npc.core.models import ClassifiedRequest
from src.ai.npc.core.vector.knowledge_store import KnowledgeStore
from src.ai.npc.core.constants import INTENT_VOCABULARY_HELP, INTENT_DIRECTION_GUIDANCE, INTENT_GENERAL_HINT, METADATA_KEY_INTENT
from src.ai.npc.core.adapters import KnowledgeDocument
from src.ai.npc.core.knowledge_adapter import DefaultKnowledgeContextAdapter

logger = logging.getLogger(__name__)


class TokyoKnowledgeStore(KnowledgeStore):
    """
    Knowledge store implementation using ChromaDB.
    
    This store is specialized for the Tokyo setting, with optimizations
    for location-based and service-based knowledge retrieval.
    """
    
    def __init__(self, 
                 persist_directory: str = "data/vector_store",
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
        
        # Create embedding function
        try:
            self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
            self.logger.info(f"Using DefaultEmbeddingFunction for embeddings")
        except Exception as e:
            self.logger.warning(f"Could not create embedding function: {e}")
            # Fallback to dummy embedding function
            self.embedding_function = DummyEmbeddingFunction()
            self.logger.warning("Using DummyEmbeddingFunction instead - this will only work for exact matches")
        
        # Create or use provided ChromaDB client
        if client is not None:
            self.client = client
        else:
            # Ensure the persistence directory exists with proper permissions
            if persist_directory:
                os.makedirs(persist_directory, exist_ok=True)
                self.logger.info(f"Ensuring persistence directory exists: {persist_directory}")
            
            # Use PersistentClient instead of Client to ensure data is persisted
            try:
                from chromadb.config import Settings
                from chromadb.api.client import PersistentClient
                self.client = PersistentClient(
                    path=persist_directory,
                    settings=Settings(
                        anonymized_telemetry=False
                    )
                )
                self.logger.info(f"Created PersistentClient with path: {persist_directory}")
            except (ImportError, AttributeError) as e:
                self.logger.warning(f"Failed to create PersistentClient: {e}, falling back to Client")
                self.client = chromadb.Client(Settings(
                    persist_directory=persist_directory,
                    anonymized_telemetry=False
                ))
        
        # Save the collection name for later use
        self.collection_name = collection_name
        
        # Create or get collection with explicit embedding function
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
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
        
        # Initialize adapter
        self.knowledge_adapter = DefaultKnowledgeContextAdapter()
        
        self.logger.info(f"Initialized TokyoKnowledgeStore with {self.collection.count()} documents")
    
    async def contextual_search(
        self, 
        request: ClassifiedRequest,
        standardized_format: bool = False,
        max_results: int = 2  # Reduce default number of results
    ) -> Union[List[Dict[str, Any]], List[KnowledgeDocument]]:
        """
        Search for relevant knowledge context based on the request.
        
        Args:
            request: The classified request to find context for
            standardized_format: If True, returns entries in standardized KnowledgeDocument format
            max_results: Maximum number of results to return (default: 2)
            
        Returns:
            A list of knowledge context documents in either standard or legacy format
        """
        # Get intent from request's additional_params
        intent = request.additional_params.get(METADATA_KEY_INTENT, None)
        
        self.logger.debug(f"Performing contextual search for request: '{request.player_input}' with intent: {intent}")
        
        # Get all documents first to verify they exist (but only in debug mode)
        all_docs = None
        try:
            all_docs = self.collection.get()
            doc_count = len(all_docs['documents'] if 'documents' in all_docs else [])
            self.logger.debug(f"Collection contains {doc_count} documents in total")
        except Exception as e:
            self.logger.error(f"Error getting all documents: {str(e)}")
            all_docs = None
        
        # Check cache first
        cache_key = self._get_cache_key(request)
        if cache_key in self._cache:
            self.logger.debug(f"Cache hit for key: {cache_key}")
            self._analytics["total_queries"] += 1
            if cache_key not in self._analytics["cache_hits"]:
                self._analytics["cache_hits"][cache_key] = 0
            self._analytics["cache_hits"][cache_key] += 1
            
            # Return cached results in requested format (limited to max_results)
            cached_results = self._cache[cache_key][:max_results]
            
            if standardized_format:
                std_results = self.knowledge_adapter.to_standard_format(cached_results)
                return std_results
            return cached_results
        
        # Get query text from request
        query = request.player_input
        self.logger.debug(f"No cache hit, performing vector search for: '{query}'")
        
        start_time = asyncio.get_event_loop().time()
        
        # Initialize results variable
        results = None
        
        # First try: exact intent matching if intent is specified
        if intent and intent != "DEFAULT":
            self.logger.debug(f"Trying search with exact intent: {intent}")
            where_clause = {"intent": intent}
            
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=max_results,  # Use max_results
                    where=where_clause
                )
            except Exception as e:
                self.logger.error(f"Error during intent search: {str(e)}")
                results = None
                
            # Check if we got results
            if results and results['documents'] and results['documents'][0] and len(results['documents'][0]) > 0:
                self.logger.debug(f"Intent search returned {len(results['documents'][0])} documents")
            else:
                self.logger.debug("Intent search returned no documents, trying fallback...")
                results = None
        
        # Second try: search without intent filter (always do this if first try fails or no intent specified)
        if results is None:
            self.logger.debug("Performing search without intent filter")
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=max_results,  # Use max_results
                    where=None  # No filtering
                )
            except Exception as e:
                self.logger.error(f"Error during unfiltered search: {str(e)}")
                results = None
                
            # Check if we got results
            if results and results['documents'] and results['documents'][0] and len(results['documents'][0]) > 0:
                self.logger.debug(f"Unfiltered search returned {len(results['documents'][0])} documents")
            else:
                self.logger.debug("Unfiltered search also returned no documents")
                results = None
        
        # Final fallback: if all searches failed, just return some documents
        if results is None and all_docs and 'documents' in all_docs and all_docs['documents']:
            self.logger.debug("Using fallback - returning documents without vector search")
            
            # Just use the first few documents as results
            max_docs = min(max_results, len(all_docs['documents']))
            
            results = {
                'documents': [all_docs['documents'][:max_docs]],
                'metadatas': [all_docs['metadatas'][:max_docs]],
                'ids': [all_docs['ids'][:max_docs]],
                'distances': [[0.0] * max_docs]  # Dummy distances
            }
        
        # Format results
        knowledge_context = []
        if results and results['documents'] and results['documents'][0] and len(results['documents'][0]) > 0:
            # Documents are already sorted by relevance in ChromaDB results
            docs_count = len(results['documents'][0])
            self.logger.debug(f"Processing {docs_count} documents from search results")
            
            for i, (doc, metadata, doc_id) in enumerate(zip(
                results['documents'][0], 
                results['metadatas'][0], 
                results['ids'][0]
            )):
                # Track document retrieval for analytics
                if doc_id not in self._analytics["retrieved_docs"]:
                    self._analytics["retrieved_docs"][doc_id] = 0
                self._analytics["retrieved_docs"][doc_id] += 1
                
                # Calculate relevance score - linearly decreasing from 1.0 to 0.6
                relevance_score = 1.0 - (i * 0.4 / max(1, docs_count - 1))
                relevance_score = round(max(0.6, min(1.0, relevance_score)), 3)
                
                # Ensure metadata is a dictionary
                if metadata is None:
                    metadata = {}
                
                # Create document with consistent field names and relevance score
                knowledge_context.append({
                    'document': doc,  # Original field name
                    'text': doc,  # Standardized field name
                    'metadata': metadata,
                    'id': doc_id,
                    'relevance_score': relevance_score
                })
            
            # Sort by relevance score (highest first) 
            knowledge_context.sort(key=lambda x: x['relevance_score'], reverse=True)
        else:
            self.logger.warning(f"No knowledge documents found for query: '{query}'")
        
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
            # Remove oldest key
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        # Limit results to max_results
        knowledge_context = knowledge_context[:max_results]
        
        # Convert to standardized format if requested
        if standardized_format:
            std_results = self.knowledge_adapter.to_standard_format(knowledge_context)
            return std_results
        
        return knowledge_context

    def _get_cache_key(self, request: ClassifiedRequest) -> str:
        """Generate a cache key from a request."""
        # Use request ID and player input as the key
        return f"{request.request_id}:{request.player_input}"
    
    async def add_knowledge(
        self, 
        text: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add new knowledge to the store.
        
        Args:
            text: The text content to add
            metadata: Optional metadata about the content
        """
        # Generate a unique ID for the document
        doc_id = f"doc_{self.collection.count() + 1}"
        
        # Ensure metadata is a dictionary
        if metadata is None:
            metadata = {}
        
        # Validate metadata
        if not isinstance(metadata, dict):
            self.logger.warning(f"Invalid metadata type: {type(metadata)}. Using empty dict instead.")
            metadata = {}
            
        # Add document to collection
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
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
            
            # Add intent field to metadata
            if "intent" in item:
                metadata["intent"] = item["intent"]
                self.logger.debug(f"Using intent from item: {item['intent']}")
            else:
                # For testing, set intent based on type
                if metadata["type"] == "location":
                    metadata["intent"] = INTENT_DIRECTION_GUIDANCE
                elif metadata["type"] == "language_learning":
                    metadata["intent"] = INTENT_VOCABULARY_HELP
                else:
                    metadata["intent"] = INTENT_GENERAL_HINT
                self.logger.debug(f"Assigned default intent based on type: {metadata['intent']}")
            
            # Add optional fields to metadata, converting lists to strings
            for key in ["related_npcs", "related_locations"]:
                if key in item:
                    value = item[key]
                    # Convert lists to strings to comply with ChromaDB requirements
                    if isinstance(value, list):
                        metadata[key] = ", ".join(value)
                    else:
                        metadata[key] = value
            
            # Generate an ID
            doc_id = item.get("id", f"doc_{i+1}")
            
            self.logger.debug(f"Adding document {i+1}: {doc_id} with intent {metadata.get('intent', 'None')}")
            
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
            
            # Explicitly persist the data
            try:
                if hasattr(self.client, 'persist'):
                    self.client.persist()
                    self.logger.info("Explicitly persisted data to disk")
            except Exception as e:
                self.logger.warning(f"Failed to explicitly persist data: {e}")
            
            # Log detailed status after adding
            self.logger.info(f"Added {len(documents)} documents to knowledge store")
            self.logger.info(f"Collection now contains {self.collection.count()} documents")
            
            # Check what we actually stored by retrieving some data
            try:
                all_data = self.collection.get()
                if all_data and "documents" in all_data and all_data["documents"]:
                    self.logger.info(f"Verification: Retrieved {len(all_data['documents'])} documents from the collection")
                    self.logger.info(f"Sample document: {all_data['documents'][0][:100]}...")
                    
                    first_metadata = all_data["metadatas"][0] if all_data["metadatas"] else None
                    if first_metadata:
                        self.logger.info(f"Sample metadata: {first_metadata}")
                    else:
                        self.logger.warning("No metadata found for verification")
                else:
                    self.logger.warning("Verification failed: No documents retrieved after adding")
            except Exception as e:
                self.logger.error(f"Error verifying added documents: {e}")
            
            return len(documents)
        
        return 0
    
    def get_explanation(self, doc_id: str) -> Optional[str]:
        """
        Get an explanation for a specific document.
        
        Args:
            doc_id: The document ID
            
        Returns:
            An explanation string or None if the document doesn't exist
        """
        try:
            result = self.collection.get(ids=[doc_id])
            
            if result['ids'] and result['metadatas']:
                doc = result['documents'][0]
                metadata = result['metadatas'][0]
                
                doc_type = metadata.get('type', 'general')
                importance = metadata.get('importance', 'medium')
                
                explanation = f"This is a {importance} importance {doc_type} document about {metadata.get('source', 'unknown topic')}."
                
                if 'intent' in metadata:
                    explanation += f" It's relevant for {metadata['intent']} queries."
                
                return explanation
            
            return None
        except Exception as e:
            self.logger.error(f"Error getting explanation for document {doc_id}: {e}")
            return None
    
    def get_analytics(self) -> Dict[str, Any]:
        """
        Get analytics data for the knowledge store.
        
        Returns:
            A dictionary containing analytics data
        """
        total_queries = self._analytics["total_queries"]
        if total_queries > 0:
            # Calculate cache hit ratio
            total_hits = sum(self._analytics["cache_hits"].values())
            hit_ratio = total_hits / total_queries
            
            # Calculate average query time
            avg_query_time = sum(self._analytics["query_times"]) / len(self._analytics["query_times"]) if self._analytics["query_times"] else 0
            
            return {
                **self._analytics,
                "hit_ratio": hit_ratio,
                "avg_query_time": avg_query_time
            }
        
        return self._analytics
    
    async def clear(self) -> None:
        """
        Clear the knowledge store.
        """
        try:
            self.collection.delete(where={"test": True})
            self._cache = {}
            self.logger.info("Cleared knowledge store")
        except Exception as e:
            self.logger.error(f"Error clearing knowledge store: {e}")
            raise
            
    async def close(self) -> None:
        """
        Close the knowledge store and release resources.
        
        This method should be called when the store is no longer needed
        to ensure proper cleanup of resources.
        """
        try:
            # First clear the cache
            self._cache = {}
            
            # If using a persistent client, we might need to explicitly close it
            if hasattr(self, 'client') and self.client is not None:
                if hasattr(self.client, 'close') and callable(self.client.close):
                    self.client.close()
                    
            self.logger.info("Closed knowledge store")
        except Exception as e:
            self.logger.error(f"Error closing knowledge store: {e}")
            raise

class DummyEmbeddingFunction:
    """A dummy embedding function that returns random vectors. Only for testing."""
    
    def __call__(self, texts):
        """Generate random embeddings for the given texts."""
        return [np.random.random(384).tolist() for _ in texts] 