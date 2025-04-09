"""
Conversation History Adapter

This module provides implementations of the conversation history adapter
for converting between different conversation history formats.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.ai.npc.core.adapters import ConversationHistoryAdapter, ConversationHistoryEntry

logger = logging.getLogger(__name__)

class DefaultConversationHistoryAdapter(ConversationHistoryAdapter):
    """
    Default implementation of the conversation history adapter.
    
    This adapter converts between:
    - The legacy format used by ConversationManager (with 'user_query' and 'response')
    - The standardized format used by PromptManager (with 'user' and 'assistant')
    """
    
    def to_standard_format(self, history: List[Dict[str, Any]]) -> List[ConversationHistoryEntry]:
        """
        Convert from legacy format to standard format.
        
        Args:
            history: Source format conversation history from ConversationManager
            
        Returns:
            List of standardized conversation history entries
        """
        standardized_entries = []
        
        if not history:
            return standardized_entries
        
        for entry in history:
            try:
                # Map legacy fields to standard fields
                user_text = entry.get("user_query", "")
                # If user_query doesn't exist, check for alternate field names
                if not user_text:
                    user_text = entry.get("user", entry.get("query", entry.get("input", "")))
                
                assistant_text = entry.get("response", "")
                # If response doesn't exist, check for alternate field names
                if not assistant_text:
                    assistant_text = entry.get("assistant", entry.get("answer", entry.get("output", "")))
                
                timestamp = entry.get("timestamp", datetime.now().isoformat())
                
                # Extract or set defaults for optional fields
                metadata = entry.get("metadata", {})
                conversation_id = entry.get("conversation_id")
                
                # Create standardized entry if required fields are present
                if user_text and assistant_text:
                    standard_entry = ConversationHistoryEntry(
                        user=user_text,
                        assistant=assistant_text,
                        timestamp=timestamp,
                        metadata=metadata,
                        conversation_id=conversation_id
                    )
                    standardized_entries.append(standard_entry)
                else:
                    logger.warning(f"Skipping entry due to missing required fields: {entry}")
            except Exception as e:
                logger.error(f"Error converting history entry to standard format: {e}")
                # Continue processing other entries
                continue
        
        return standardized_entries
    
    def from_standard_format(self, standardized_history: List[ConversationHistoryEntry]) -> List[Dict[str, Any]]:
        """
        Convert from standard format to legacy format.
        
        Args:
            standardized_history: Standardized conversation history
            
        Returns:
            List of conversation history entries in legacy format
        """
        legacy_entries = []
        
        if not standardized_history:
            return legacy_entries
        
        for entry in standardized_history:
            try:
                # Convert to legacy format
                legacy_entry = {
                    "user_query": entry.user,
                    "response": entry.assistant,
                    "timestamp": entry.timestamp
                }
                
                # Add optional fields if present
                if entry.metadata:
                    legacy_entry["metadata"] = entry.metadata
                
                if entry.conversation_id:
                    legacy_entry["conversation_id"] = entry.conversation_id
                
                legacy_entries.append(legacy_entry)
            except Exception as e:
                logger.error(f"Error converting standard entry to legacy format: {e}")
                # Continue processing other entries
                continue
        
        return legacy_entries 