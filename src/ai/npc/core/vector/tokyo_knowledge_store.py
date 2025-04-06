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

import chromadb
from chromadb.utils import embedding_functions

from src.ai.npc.core.models import ClassifiedRequest

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
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize the knowledge store.
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Optional directory to persist the database
            embedding_model: Name of the sentence-transformers model to use
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
        """
        # Check if the collection is already populated
        if self.collection.count() > 0:
            logger.info(f"Collection already contains {self.collection.count()} documents, skipping load")
            return 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                knowledge_base = json.load(f)
                
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
            
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
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
    
    def contextual_search(
        self,
        request: ClassifiedRequest,
        top_k: int = 3,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search with awareness of game context.
        
        Args:
            request: The classified request
            top_k: Maximum number of results to return
            additional_context: Additional context to include in the query
            
        Returns:
            List of documents with metadata and scores
        """
        # Create an enhanced query
        query_parts = [request.player_input]
        
        # Add game context to the query
        if request.game_context:
            if request.game_context.player_location:
                query_parts.append(f"at {request.game_context.player_location}")
            if request.game_context.current_objective:
                query_parts.append(f"for objective: {request.game_context.current_objective}")
            if request.game_context.nearby_npcs:
                query_parts.append(f"with NPCs: {', '.join(request.game_context.nearby_npcs)}")
        
        # Add intent to the query
        if request.intent:
            query_parts.append(f"intent: {request.intent.value}")
        
        # Add additional context
        if additional_context:
            for key, value in additional_context.items():
                query_parts.append(f"{key}: {value}")
        
        # Create the enhanced query
        enhanced_query = " ".join(query_parts)
        logger.debug(f"Enhanced query: {enhanced_query}")
        
        # Determine appropriate filters
        filters = None
        
        # If the intent is vocabulary or grammar related, prioritize language_learning
        if request.intent and request.intent.value in ["vocabulary_help", "grammar_explanation"]:
            # Get 2 language learning documents
            language_results = self.search(enhanced_query, top_k=2, filters={"type": "language_learning"})
            
            # Get 1 location document related to the player's location
            location_filters = {"type": "location"}
            location_results = []
            if request.game_context and request.game_context.player_location:
                location_query = f"{request.game_context.player_location} in Tokyo Station"
                location_results = self.search(location_query, top_k=1, filters=location_filters)
            
            # Combine the results
            results = language_results + location_results
        
        # For direction guidance, prioritize location information
        elif request.intent and request.intent.value == "direction_guidance":
            # Get 2 location documents
            location_results = self.search(enhanced_query, top_k=2, filters={"type": "location"})
            
            # Get 1 language learning document for direction vocabulary
            language_query = "direction vocabulary in Japanese"
            language_results = self.search(language_query, top_k=1, filters={"type": "language_learning"})
            
            # Combine the results
            results = location_results + language_results
        
        # For general search, don't use filters
        else:
            results = self.search(enhanced_query, top_k=top_k)
        
        # Sort results by importance and score
        importance_ranking = {"high": 3, "medium": 2, "low": 1}
        sorted_results = sorted(
            results,
            key=lambda x: (
                importance_ranking.get(x.get("metadata", {}).get("importance", "medium"), 0),
                x.get("score", 0)
            ),
            reverse=True
        )
        
        # Limit to top_k
        return sorted_results[:top_k] 