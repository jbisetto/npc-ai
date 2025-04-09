"""
Knowledge Context Adapter

This module provides implementations of the knowledge context adapter
for converting between different knowledge context formats.
"""

import logging
from typing import Dict, Any, List, Optional, Union
import uuid

from src.ai.npc.core.adapters import KnowledgeContextAdapter, KnowledgeDocument

logger = logging.getLogger(__name__)

class DefaultKnowledgeContextAdapter(KnowledgeContextAdapter):
    """
    Default implementation of the knowledge context adapter.
    
    This adapter converts between:
    - The format used by TokyoKnowledgeStore (with 'document'/'text' fields)
    - The standardized KnowledgeDocument format
    
    It also handles relevance scoring and metadata standardization.
    """
    
    def to_standard_format(self, documents: List[Dict[str, Any]]) -> List[KnowledgeDocument]:
        """
        Convert from TokyoKnowledgeStore format to standard format.
        
        Args:
            documents: Source format knowledge documents
            
        Returns:
            List of standardized knowledge documents
        """
        standardized_docs = []
        
        if not documents:
            return standardized_docs
        
        for doc in documents:
            try:
                # Extract text content, supporting both 'document' and 'text' fields
                text_content = doc.get('text', doc.get('document', ''))
                
                if not text_content:
                    logger.warning(f"Skipping document with missing content: {doc}")
                    continue
                
                # Extract or generate document ID
                doc_id = doc.get('id', str(uuid.uuid4()))
                
                # Extract metadata
                metadata = doc.get('metadata', {})
                
                # Extract relevance score if available
                relevance_score = None
                if 'relevance_score' in doc:
                    relevance_score = doc['relevance_score']
                elif 'score' in doc:
                    relevance_score = doc['score']
                
                # Create standardized document
                standard_doc = KnowledgeDocument(
                    text=text_content,
                    id=doc_id,
                    metadata=metadata,
                    relevance_score=relevance_score
                )
                
                standardized_docs.append(standard_doc)
            except Exception as e:
                logger.error(f"Error converting knowledge document to standard format: {e}")
                # Continue processing other documents
                continue
        
        # Sort by relevance score if available
        if standardized_docs:
            standardized_docs.sort(
                key=lambda d: d.relevance_score if d.relevance_score is not None else 0,
                reverse=True
            )
        
        return standardized_docs
    
    def from_standard_format(self, standardized_documents: List[KnowledgeDocument]) -> List[Dict[str, Any]]:
        """
        Convert from standard format to TokyoKnowledgeStore format.
        
        Args:
            standardized_documents: Standardized knowledge documents
            
        Returns:
            List of knowledge documents in TokyoKnowledgeStore format
        """
        tokyo_docs = []
        
        if not standardized_documents:
            return tokyo_docs
        
        for doc in standardized_documents:
            try:
                # Convert to Tokyo format
                tokyo_doc = {
                    'document': doc.text,
                    'text': doc.text,  # For backward compatibility
                    'id': doc.id,
                    'metadata': doc.metadata
                }
                
                # Add relevance score if available
                if doc.relevance_score is not None:
                    tokyo_doc['relevance_score'] = doc.relevance_score
                
                tokyo_docs.append(tokyo_doc)
            except Exception as e:
                logger.error(f"Error converting standard document to Tokyo format: {e}")
                # Continue processing other documents
                continue
        
        return tokyo_docs 