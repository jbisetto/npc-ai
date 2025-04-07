"""
Conversation Manager for the Companion AI.

This module manages persistent conversation histories across multiple sessions.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ConversationManager:
    """
    Manages conversation histories across multiple sessions.
    """
    
    def __init__(self, storage_dir: str = "src/data/conversations"):
        """
        Initialize the conversation manager.
        
        Args:
            storage_dir: Directory to store conversation histories
        """
        self.storage_dir = storage_dir
        self.player_histories = {}  # In-memory cache of player histories
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        
        logger.info(f"Initialized ConversationManager with storage directory: {storage_dir}")
    
    def get_player_history(self, player_id: str, max_entries: int = 10) -> List[Dict[str, Any]]:
        """
        Get the conversation history for a specific player.
        
        Args:
            player_id: The player ID to get history for
            max_entries: Maximum number of recent entries to return
            
        Returns:
            List of conversation entries, most recent first
        """
        # Load player history if not in cache
        if player_id not in self.player_histories:
            self._load_player_history(player_id)
        
        # Get all entries from all conversations
        all_entries = []
        player_data = self.player_histories.get(player_id, {"conversations": {}})
        for conv_id, conversation in player_data["conversations"].items():
            # Add conversation_id to each entry for reference
            entries = [{**entry, "conversation_id": conv_id} for entry in conversation["entries"]]
            all_entries.extend(entries)
        
        # Sort by timestamp and return most recent
        all_entries.sort(key=lambda x: x["timestamp"], reverse=True)
        return all_entries[:max_entries]
    
    def add_to_history(
        self, 
        conversation_id: str, 
        user_query: str, 
        response: str,
        npc_id: str,
        player_id: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a conversation entry to the history.
        
        Args:
            conversation_id: The conversation ID
            user_query: The user's query
            response: The NPC's response
            npc_id: Identifier for the NPC that provided the response
            player_id: The ID of the player in this conversation
            session_id: Optional session ID
            metadata: Optional additional metadata (e.g., language_level)
        """
        # Load or initialize player history
        if player_id not in self.player_histories:
            self._load_player_history(player_id)
            if player_id not in self.player_histories:
                self.player_histories[player_id] = {
                    "player_id": player_id,
                    "conversations": {}
                }
        
        # Initialize conversation if it doesn't exist
        player_data = self.player_histories[player_id]
        if conversation_id not in player_data["conversations"]:
            player_data["conversations"][conversation_id] = {
                "entries": []
            }
        
        # Create the entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user_query": user_query,
            "response": response,
            "npc_id": npc_id,
            "player_id": player_id
        }
        
        # Add optional fields
        if session_id:
            entry["session_id"] = session_id
        if metadata:
            entry["metadata"] = metadata
        
        # Add to history
        player_data["conversations"][conversation_id]["entries"].append(entry)
        
        # Save to disk
        self._save_player_history(player_id)
        
        logger.debug(f"Saved entry for player {player_id} in conversation {conversation_id}, now has {len(player_data['conversations'][conversation_id]['entries'])} entries")
    
    def _load_player_history(self, player_id: str) -> None:
        """
        Load a player's history from disk.
        
        Args:
            player_id: The player ID
        """
        file_path = os.path.join(self.storage_dir, f"{player_id}.json")
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.player_histories[player_id] = json.load(f)
                logger.debug(f"Loaded history for player {player_id} from {file_path}")
            except Exception as e:
                logger.error(f"Error loading history for player {player_id}: {str(e)}")
                self.player_histories[player_id] = {"player_id": player_id, "conversations": {}}
        else:
            logger.debug(f"No history file found for player {player_id}")
            self.player_histories[player_id] = {"player_id": player_id, "conversations": {}}
    
    def _save_player_history(self, player_id: str) -> None:
        """
        Save a player's history to disk.
        
        Args:
            player_id: The player ID
        """
        file_path = os.path.join(self.storage_dir, f"{player_id}.json")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.player_histories[player_id], f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved history for player {player_id} to {file_path}")
        except Exception as e:
            logger.error(f"Error saving history for player {player_id}: {str(e)}") 