"""
Integration tests for the standardized adapters.
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List
import uuid

from src.ai.npc.core.adapters import ConversationHistoryEntry, KnowledgeDocument
from src.ai.npc.core.history_adapter import DefaultConversationHistoryAdapter
from src.ai.npc.core.knowledge_adapter import DefaultKnowledgeContextAdapter

# Test data for conversation history
LEGACY_HISTORY = [
    {
        "timestamp": "2023-04-08T10:00:00Z",
        "user_query": "Hello, who are you?",
        "response": "I'm Hachiko, your friendly guide at Tokyo Station!",
        "npc_id": "hachiko",
        "player_id": "player1",
        "conversation_id": "conv1"
    },
    {
        "timestamp": "2023-04-08T10:01:00Z",
        "user_query": "Where can I buy tickets?",
        "response": "You can buy tickets at the ticket counter near the central entrance.",
        "npc_id": "hachiko",
        "player_id": "player1",
        "conversation_id": "conv1",
        "metadata": {"language_level": "beginner"}
    }
]

# Test data for knowledge documents
LEGACY_KNOWLEDGE = [
    {
        "document": "The JR ticket office is located at the main entrance of Tokyo Station.",
        "metadata": {
            "type": "location",
            "importance": "high",
            "source": "Tokyo Station Guide"
        },
        "id": "doc_1"
    },
    {
        "text": "Tokyo Station connects JR East, JR Central, and Tokyo Metro lines.",
        "metadata": {
            "type": "transit",
            "importance": "medium",
            "source": "Train Network Guide"
        },
        "id": "doc_2",
        "relevance_score": 0.85
    }
]


class TestConversationHistoryAdapter:
    """Tests for the ConversationHistoryAdapter."""
    
    def test_to_standard_format(self):
        """Test conversion from legacy format to standard format."""
        adapter = DefaultConversationHistoryAdapter()
        standardized = adapter.to_standard_format(LEGACY_HISTORY)
        
        # Check if entries were converted correctly
        assert len(standardized) == 2
        assert isinstance(standardized[0], ConversationHistoryEntry)
        assert standardized[0].user == "Hello, who are you?"
        assert standardized[0].assistant == "I'm Hachiko, your friendly guide at Tokyo Station!"
        assert standardized[0].timestamp == "2023-04-08T10:00:00Z"
        assert standardized[0].conversation_id == "conv1"
        
        # Check if metadata was preserved
        assert standardized[1].metadata == {"language_level": "beginner"}
    
    def test_from_standard_format(self):
        """Test conversion from standard format to legacy format."""
        adapter = DefaultConversationHistoryAdapter()
        
        # Create standardized entries
        standardized = [
            ConversationHistoryEntry(
                user="What's the weather like?",
                assistant="It's sunny today in Tokyo!",
                timestamp="2023-04-08T11:00:00Z",
                conversation_id="conv2"
            ),
            ConversationHistoryEntry(
                user="How do I get to Shinjuku?",
                assistant="Take the JR Yamanote Line from Platform 3.",
                timestamp="2023-04-08T11:05:00Z",
                metadata={"intent": "direction"}
            )
        ]
        
        # Convert back to legacy format
        legacy = adapter.from_standard_format(standardized)
        
        # Check if entries were converted correctly
        assert len(legacy) == 2
        assert legacy[0]["user_query"] == "What's the weather like?"
        assert legacy[0]["response"] == "It's sunny today in Tokyo!"
        assert legacy[0]["timestamp"] == "2023-04-08T11:00:00Z"
        assert legacy[0]["conversation_id"] == "conv2"
        
        # Check if metadata was preserved
        assert legacy[1]["metadata"] == {"intent": "direction"}
    
    def test_round_trip_conversion(self):
        """Test round trip conversion (legacy -> standard -> legacy)."""
        adapter = DefaultConversationHistoryAdapter()
        
        # Perform round trip conversion
        standardized = adapter.to_standard_format(LEGACY_HISTORY)
        converted_back = adapter.from_standard_format(standardized)
        
        # Check that essential information is preserved
        assert len(converted_back) == len(LEGACY_HISTORY)
        
        for i, original in enumerate(LEGACY_HISTORY):
            assert converted_back[i]["user_query"] == original["user_query"]
            assert converted_back[i]["response"] == original["response"]
            assert converted_back[i]["timestamp"] == original["timestamp"]
            
            if "metadata" in original:
                assert converted_back[i]["metadata"] == original["metadata"]
    
    def test_empty_input(self):
        """Test handling of empty input."""
        adapter = DefaultConversationHistoryAdapter()
        
        # Test empty list input
        assert adapter.to_standard_format([]) == []
        assert adapter.from_standard_format([]) == []
    
    def test_invalid_input(self):
        """Test handling of invalid input."""
        adapter = DefaultConversationHistoryAdapter()
        
        # Missing required fields
        incomplete_history = [
            {"timestamp": "2023-04-08T10:00:00Z", "user_query": "Hello"},  # Missing response
            {"timestamp": "2023-04-08T10:01:00Z", "response": "Hi there"}  # Missing user_query
        ]
        
        standardized = adapter.to_standard_format(incomplete_history)
        assert len(standardized) == 0  # No valid entries should be created


class TestKnowledgeContextAdapter:
    """Tests for the KnowledgeContextAdapter."""
    
    def test_to_standard_format(self):
        """Test conversion from legacy format to standard format."""
        adapter = DefaultKnowledgeContextAdapter()
        standardized = adapter.to_standard_format(LEGACY_KNOWLEDGE)
        
        # Check if entries were converted correctly
        assert len(standardized) == 2
        assert isinstance(standardized[0], KnowledgeDocument)
        
        # Check if document with relevance score is first (sorting should happen)
        assert standardized[0].id == "doc_2"
        assert standardized[0].text == "Tokyo Station connects JR East, JR Central, and Tokyo Metro lines."
        assert standardized[0].relevance_score == 0.85
        
        # Check second document
        assert standardized[1].id == "doc_1"
        assert standardized[1].text == "The JR ticket office is located at the main entrance of Tokyo Station."
        assert standardized[1].metadata["type"] == "location"
    
    def test_from_standard_format(self):
        """Test conversion from standard format to legacy format."""
        adapter = DefaultKnowledgeContextAdapter()
        
        # Create standardized documents
        standardized = [
            KnowledgeDocument(
                text="The Shinkansen platforms are on the upper level.",
                id="doc_3",
                metadata={"type": "location", "source": "Station Map"},
                relevance_score=0.92
            ),
            KnowledgeDocument(
                text="Commuter trains operate from 5:00 AM to midnight.",
                id="doc_4",
                metadata={"type": "schedule", "importance": "high"}
            )
        ]
        
        # Convert to legacy format
        legacy = adapter.from_standard_format(standardized)
        
        # Check if documents were converted correctly
        assert len(legacy) == 2
        assert legacy[0]["document"] == "The Shinkansen platforms are on the upper level."
        assert legacy[0]["text"] == "The Shinkansen platforms are on the upper level."
        assert legacy[0]["id"] == "doc_3"
        assert legacy[0]["metadata"]["type"] == "location"
        assert legacy[0]["relevance_score"] == 0.92
        
        assert legacy[1]["document"] == "Commuter trains operate from 5:00 AM to midnight."
        assert legacy[1]["metadata"]["importance"] == "high"
    
    def test_round_trip_conversion(self):
        """Test round trip conversion (legacy -> standard -> legacy)."""
        adapter = DefaultKnowledgeContextAdapter()
        
        # Perform round trip conversion
        standardized = adapter.to_standard_format(LEGACY_KNOWLEDGE)
        converted_back = adapter.from_standard_format(standardized)
        
        # Check that essential information is preserved
        assert len(converted_back) == len(LEGACY_KNOWLEDGE)
        
        # Documents might be reordered due to relevance score sorting
        doc_ids = [doc["id"] for doc in converted_back]
        assert "doc_1" in doc_ids
        assert "doc_2" in doc_ids
        
        # Find each document in the converted back list
        for original in LEGACY_KNOWLEDGE:
            matched = False
            for converted in converted_back:
                if converted["id"] == original["id"]:
                    # Check content
                    if "document" in original:
                        assert converted["document"] == original["document"]
                    else:
                        assert converted["document"] == original["text"]
                    
                    # Check metadata
                    assert converted["metadata"] == original["metadata"]
                    matched = True
                    break
            
            assert matched, f"Document with ID {original['id']} not found in converted result"
    
    def test_empty_input(self):
        """Test handling of empty input."""
        adapter = DefaultKnowledgeContextAdapter()
        
        # Test empty list input
        assert adapter.to_standard_format([]) == []
        assert adapter.from_standard_format([]) == []
    
    def test_missing_text_field(self):
        """Test handling of documents with missing text field."""
        adapter = DefaultKnowledgeContextAdapter()
        
        # Missing text content
        invalid_docs = [
            {"id": "doc_x", "metadata": {"type": "unknown"}},  # Missing text/document
            {"document": "", "id": "doc_y"},  # Empty text
        ]
        
        standardized = adapter.to_standard_format(invalid_docs)
        assert len(standardized) == 0  # No valid docs should be created 