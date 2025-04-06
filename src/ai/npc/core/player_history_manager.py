"""
Player History Manager for the Companion AI.

This module manages persistent conversation histories for players across multiple sessions.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class PlayerHistoryManager:
    """
    Manages player conversation histories across multiple sessions.
    """
    
    def __init__(self, storage_dir: str = "src/data/player_history"):
        """
        Initialize the player history manager.
        
        Args:
            storage_dir: Directory to store player histories
        """
        self.storage_dir = storage_dir
        self.histories = {}  # In-memory cache
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        
        logger.info(f"Initialized PlayerHistoryManager with storage directory: {storage_dir}")
    
    def get_player_history(self, player_id: str, max_entries: int = 10) -> List[Dict[str, Any]]:
        """
        Get the conversation history for a player.
        
        Args:
            player_id: The player ID
            max_entries: Maximum number of recent entries to return
            
        Returns:
            List of conversation entries, most recent first
        """
        # Load from cache or file
        if player_id not in self.histories:
            self._load_player_history(player_id)
        
        # Get the history (empty list if not found)
        history = self.histories.get(player_id, {"entries": []})
        
        # Return the most recent entries
        return history["entries"][-max_entries:]
    
    def add_interaction(
        self, 
        player_id: str, 
        user_query: str, 
        assistant_response: str, 
        session_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        Add an interaction to a player's history.
        
        Args:
            player_id: The player ID
            user_query: The user's query
            assistant_response: The assistant's response
            session_id: Optional session ID
            metadata: Optional additional metadata
        """
        # Load or initialize history
        if player_id not in self.histories:
            self._load_player_history(player_id)
            if player_id not in self.histories:
                self.histories[player_id] = {"entries": []}
        
        # Create the entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user_query": user_query,
            "assistant_response": assistant_response,
            "session_id": session_id
        }
        
        # Add metadata if provided
        if metadata:
            entry["metadata"] = metadata
        
        # Add to history
        self.histories[player_id]["entries"].append(entry)
        
        # Save to disk
        self._save_player_history(player_id)
        
        logger.debug(f"Added interaction to history for player {player_id}, now has {len(self.histories[player_id]['entries'])} entries")
    
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
                    self.histories[player_id] = json.load(f)
                logger.debug(f"Loaded history for player {player_id} from {file_path}")
            except Exception as e:
                logger.error(f"Error loading history for player {player_id}: {str(e)}")
                self.histories[player_id] = {"entries": []}
        else:
            logger.debug(f"No history file found for player {player_id}")
            self.histories[player_id] = {"entries": []}
    
    def _save_player_history(self, player_id: str) -> None:
        """
        Save a player's history to disk.
        
        Args:
            player_id: The player ID
        """
        file_path = os.path.join(self.storage_dir, f"{player_id}.json")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.histories[player_id], f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved history for player {player_id} to {file_path}")
        except Exception as e:
            logger.error(f"Error saving history for player {player_id}: {str(e)}") 