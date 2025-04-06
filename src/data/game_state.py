"""
Data access layer for game state operations.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional

# In-memory storage for game states (in a real implementation, this would be a database)
_game_states: Dict[str, Dict[str, Any]] = {}


class GameStateError(Exception):
    """Base exception for game state errors."""
    pass


class PlayerNotFoundError(GameStateError):
    """Exception raised when a player is not found."""
    pass


class SaveNotFoundError(GameStateError):
    """Exception raised when a save is not found."""
    pass


class InvalidPlayerIdError(GameStateError):
    """Exception raised when a player ID is invalid."""
    pass


def validate_player_id(player_id: str) -> None:
    """
    Validate a player ID.
    
    Args:
        player_id: The player ID to validate.
        
    Raises:
        InvalidPlayerIdError: If the player ID is invalid.
    """
    if not player_id or len(player_id) < 3:
        raise InvalidPlayerIdError(f"Invalid player ID format: {player_id}")


def save_game_state(game_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save a game state.
    
    Args:
        game_state: The game state to save.
        
    Returns:
        A dictionary containing the save ID and timestamp.
        
    Raises:
        InvalidPlayerIdError: If the player ID is invalid.
    """
    player_id = game_state.get("player_id")
    validate_player_id(player_id)
    
    # Generate a unique save ID
    save_id = str(uuid.uuid4())
    timestamp = game_state.get("timestamp", datetime.now(timezone.utc))
    
    # Create a new save entry
    save_entry = {
        "save_id": save_id,
        "timestamp": timestamp,
        "last_played": timestamp,
        "player_id": player_id,
        "session_id": game_state.get("session_id"),
        "location": game_state.get("location", {}),
        "quest_state": game_state.get("quest_state", {}),
        "inventory": game_state.get("inventory", []),
        "game_flags": game_state.get("game_flags", {}),
        "companions": game_state.get("companions", {})
    }
    
    # Initialize player's saves if not exists
    if player_id not in _game_states:
        _game_states[player_id] = {}
    
    # Store the save
    _game_states[player_id][save_id] = save_entry
    
    return {
        "success": True,
        "save_id": save_id,
        "timestamp": timestamp
    }


def load_game_state(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load a game state.
    
    Args:
        request_data: A dictionary containing the player_id and optionally save_id.
        
    Returns:
        The loaded game state.
        
    Raises:
        InvalidPlayerIdError: If the player ID is invalid.
        PlayerNotFoundError: If the player is not found.
        SaveNotFoundError: If the save is not found.
    """
    player_id = request_data.get("player_id")
    save_id = request_data.get("save_id")
    
    validate_player_id(player_id)
    
    # Check if player exists
    if player_id not in _game_states:
        raise PlayerNotFoundError(f"Player with ID {player_id} not found")
    
    player_saves = _game_states[player_id]
    
    # If no save ID is provided, get the most recent save
    if save_id is None:
        if not player_saves:
            raise SaveNotFoundError(f"No saves found for player {player_id}")
        
        # Find the most recent save
        most_recent_save = max(
            player_saves.values(),
            key=lambda save: save["timestamp"]
        )
        return most_recent_save
    
    # Check if save exists
    if save_id not in player_saves:
        raise SaveNotFoundError(f"Save with ID {save_id} not found for player {player_id}")
    
    return player_saves[save_id]


def list_saved_games(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    List all saved games for a player.
    
    Args:
        request_data: A dictionary containing the player_id.
        
    Returns:
        A dictionary containing the player ID and a list of save metadata.
        
    Raises:
        InvalidPlayerIdError: If the player ID is invalid.
        PlayerNotFoundError: If the player is not found.
    """
    player_id = request_data.get("player_id")
    validate_player_id(player_id)
    
    # Check if player exists
    if player_id not in _game_states:
        raise PlayerNotFoundError(f"Player with ID {player_id} not found")
    
    player_saves = _game_states[player_id]
    
    # Create a list of save metadata
    saves = [
        {
            "save_id": save_id,
            "timestamp": save["timestamp"],
            "location_name": save["location"].get("area", "Unknown"),
            "quest_name": save["quest_state"].get("active_quest", "None"),
            "level": None  # Level is not implemented yet
        }
        for save_id, save in player_saves.items()
    ]
    
    # Sort saves by timestamp (newest first)
    saves.sort(key=lambda save: save["timestamp"], reverse=True)
    
    return {
        "player_id": player_id,
        "saves": saves
    }


# Create mock data for testing
def _create_mock_data():
    """Create mock data for testing."""
    # Create a player
    player_id = "test_player"
    
    # Create some saves
    save1 = {
        "player_id": player_id,
        "session_id": "test_session_1",
        "timestamp": datetime.now(timezone.utc) - timedelta(days=2),
        "location": {
            "area": "tokyo_station",
            "position": {
                "x": 100,
                "y": 200
            }
        },
        "quest_state": {
            "active_quest": "find_ticket_machine",
            "quest_step": "locate_machine",
            "objectives": [
                {
                    "id": "obj1",
                    "completed": True,
                    "description": "Enter Tokyo Station"
                },
                {
                    "id": "obj2",
                    "completed": False,
                    "description": "Find the ticket machine"
                }
            ]
        },
        "inventory": ["map", "phrase_book"],
        "game_flags": {
            "tutorial_completed": True,
            "met_station_attendant": False
        },
        "companions": {
            "ai_assistant": {
                "relationship": 0.5,
                "assistance_used": 2
            }
        }
    }
    
    save2 = {
        "player_id": player_id,
        "session_id": "test_session_2",
        "timestamp": datetime.now(timezone.utc) - timedelta(hours=5),
        "location": {
            "area": "shinjuku_station",
            "position": {
                "x": 150,
                "y": 300
            }
        },
        "quest_state": {
            "active_quest": "buy_ticket",
            "quest_step": "select_destination",
            "objectives": [
                {
                    "id": "obj1",
                    "completed": True,
                    "description": "Find the ticket machine"
                },
                {
                    "id": "obj2",
                    "completed": False,
                    "description": "Select destination"
                }
            ]
        },
        "inventory": ["map", "phrase_book", "station_guide"],
        "game_flags": {
            "tutorial_completed": True,
            "met_station_attendant": True
        },
        "companions": {
            "ai_assistant": {
                "relationship": 0.7,
                "assistance_used": 5
            }
        }
    }
    
    save3 = {
        "player_id": player_id,
        "session_id": "test_session_3",
        "timestamp": datetime.now(timezone.utc) - timedelta(days=1),
        "location": {
            "area": "akihabara_station",
            "position": {
                "x": 200,
                "y": 400
            }
        },
        "quest_state": {
            "active_quest": "find_platform",
            "quest_step": "check_schedule",
            "objectives": [
                {
                    "id": "obj1",
                    "completed": True,
                    "description": "Buy ticket"
                },
                {
                    "id": "obj2",
                    "completed": False,
                    "description": "Find the correct platform"
                }
            ]
        },
        "inventory": ["map", "phrase_book", "station_guide", "ticket"],
        "game_flags": {
            "tutorial_completed": True,
            "met_station_attendant": True,
            "bought_ticket": True
        },
        "companions": {
            "ai_assistant": {
                "relationship": 0.8,
                "assistance_used": 7
            }
        }
    }
    
    # Save the mock data
    save_game_state(save1)
    save_game_state(save2)
    save_game_state(save3)


# Create mock data when module is imported
_create_mock_data() 