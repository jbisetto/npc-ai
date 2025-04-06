"""
Data access layer for player operations.
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Custom exceptions
class PlayerError(Exception):
    """Base exception for player errors."""
    pass


class PlayerNotFoundError(PlayerError):
    """Exception raised when a player is not found."""
    pass


class InvalidPlayerIdError(PlayerError):
    """Exception raised when a player ID is invalid."""
    pass


# In-memory storage for player data (in a real implementation, this would be a database)
_players: Dict[str, Dict[str, Any]] = {}


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


def get_player_by_id(player_id: str) -> Dict[str, Any]:
    """
    Get a player by ID.
    
    Args:
        player_id: The ID of the player.
        
    Returns:
        A dictionary containing information about the player.
        
    Raises:
        InvalidPlayerIdError: If the player ID is invalid.
        PlayerNotFoundError: If the player is not found.
    """
    validate_player_id(player_id)
    
    if player_id not in _players:
        raise PlayerNotFoundError(f"Player with ID {player_id} not found")
    
    return _players[player_id]


# Create mock data for testing
def _create_mock_data():
    """Create mock data for testing."""
    # Player 1
    player1_id = "player123"
    _players[player1_id] = {
        "player_id": player1_id,
        "username": "JapanExplorer",
        "email": "explorer@example.com",
        "language_level": "N5",
        "created_at": "2023-01-15T08:30:00Z",
        "last_login": "2023-03-10T14:45:00Z",
        "learning_progress": {
            "vocabulary_mastered": 42,
            "grammar_points": 11,
            "conversation_success": 0.82
        },
        "game_progress": {
            "current_location": "tokyo_station",
            "completed_quests": ["tutorial", "meet_station_master"],
            "active_quests": ["buy_ticket_to_odawara"],
            "inventory": ["map", "phrase_book", "water_bottle"]
        }
    }
    
    # Player 2
    player2_id = "player456"
    _players[player2_id] = {
        "player_id": player2_id,
        "username": "TokyoTraveler",
        "email": "traveler@example.com",
        "language_level": "N4",
        "created_at": "2023-02-20T10:15:00Z",
        "last_login": "2023-03-12T09:30:00Z",
        "learning_progress": {
            "vocabulary_mastered": 78,
            "grammar_points": 23,
            "conversation_success": 0.91
        },
        "game_progress": {
            "current_location": "shinjuku_station",
            "completed_quests": ["tutorial", "meet_station_master", "buy_ticket_to_odawara"],
            "active_quests": ["find_lost_luggage"],
            "inventory": ["map", "phrase_book", "train_pass", "camera"]
        }
    }


# Initialize mock data
_create_mock_data() 