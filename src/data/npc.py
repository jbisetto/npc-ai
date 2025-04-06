"""
Data access layer for NPC operations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import logging

# Set up logging
logger = logging.getLogger(__name__)


# Custom exceptions
class NPCError(Exception):
    """Base exception for NPC errors."""
    pass


class NPCNotFoundError(NPCError):
    """Exception raised when an NPC is not found."""
    pass


class InvalidNPCIdError(NPCError):
    """Exception raised when an NPC ID is invalid."""
    pass


class PlayerNotFoundError(NPCError):
    """Exception raised when a player is not found."""
    pass


class InteractionStateNotFoundError(NPCError):
    """Exception raised when an interaction state is not found."""
    pass


# In-memory storage for NPC data (in a real implementation, this would be a database)
_npcs: Dict[str, Dict[str, Any]] = {}
_npc_configs: Dict[str, Dict[str, Any]] = {}
_interaction_states: Dict[str, Dict[str, Dict[str, Any]]] = {}  # player_id -> npc_id -> state


def validate_npc_id(npc_id: str) -> None:
    """
    Validate an NPC ID.
    
    Args:
        npc_id: The NPC ID to validate.
        
    Raises:
        InvalidNPCIdError: If the NPC ID is invalid.
    """
    if not npc_id or len(npc_id) < 3:
        raise InvalidNPCIdError(f"Invalid NPC ID format: {npc_id}")


def validate_player_id(player_id: str) -> None:
    """
    Validate a player ID.
    
    Args:
        player_id: The player ID to validate.
        
    Raises:
        InvalidNPCIdError: If the player ID is invalid.
    """
    if not player_id or len(player_id) < 3:
        raise InvalidNPCIdError(f"Invalid player ID format: {player_id}")


def get_npc_information(npc_id: str) -> Dict[str, Any]:
    """
    Get information about an NPC.
    
    Args:
        npc_id: The ID of the NPC.
        
    Returns:
        A dictionary containing information about the NPC.
        
    Raises:
        InvalidNPCIdError: If the NPC ID is invalid.
        NPCNotFoundError: If the NPC is not found.
    """
    validate_npc_id(npc_id)
    
    if npc_id not in _npcs:
        raise NPCNotFoundError(f"NPC with ID {npc_id} not found")
    
    return _npcs[npc_id]


def get_npc_configuration(npc_id: str) -> Dict[str, Any]:
    """
    Get the configuration for an NPC.
    
    Args:
        npc_id: The ID of the NPC.
        
    Returns:
        A dictionary containing the configuration for the NPC.
        
    Raises:
        InvalidNPCIdError: If the NPC ID is invalid.
        NPCNotFoundError: If the NPC is not found.
    """
    validate_npc_id(npc_id)
    
    if npc_id not in _npc_configs:
        raise NPCNotFoundError(f"NPC configuration with ID {npc_id} not found")
    
    return _npc_configs[npc_id]


def get_npc_interaction_state(player_id: str, npc_id: str) -> Dict[str, Any]:
    """
    Get the interaction state between a player and an NPC.
    
    Args:
        player_id: The ID of the player.
        npc_id: The ID of the NPC.
        
    Returns:
        A dictionary containing the interaction state.
        
    Raises:
        InvalidNPCIdError: If the NPC ID is invalid.
        InvalidNPCIdError: If the player ID is invalid.
        NPCNotFoundError: If the NPC is not found.
        PlayerNotFoundError: If the player is not found.
        InteractionStateNotFoundError: If the interaction state is not found.
    """
    validate_player_id(player_id)
    validate_npc_id(npc_id)
    
    if player_id not in _interaction_states:
        raise PlayerNotFoundError(f"Player with ID {player_id} not found")
    
    if npc_id not in _interaction_states[player_id]:
        raise InteractionStateNotFoundError(f"No interaction state found for player {player_id} and NPC {npc_id}")
    
    return _interaction_states[player_id][npc_id]


def update_npc_configuration(npc_id: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the configuration for an NPC.
    
    Args:
        npc_id: The ID of the NPC.
        config_data: The updated configuration data.
        
    Returns:
        A dictionary containing the updated configuration for the NPC.
        
    Raises:
        InvalidNPCIdError: If the NPC ID is invalid.
        NPCNotFoundError: If the NPC is not found.
    """
    validate_npc_id(npc_id)
    
    if npc_id not in _npc_configs:
        raise NPCNotFoundError(f"NPC configuration with ID {npc_id} not found")
    
    # Create a deep copy of the configuration to update
    updated_config = _npc_configs[npc_id].copy()
    
    logger.debug(f"Original config: {updated_config}")
    logger.debug(f"Update data: {config_data}")
    
    # Update each section of the configuration
    if "profile" in config_data:
        logger.debug(f"Updating profile: {config_data['profile']}")
        updated_config["profile"] = config_data["profile"]
    
    if "languageProfile" in config_data:
        logger.debug(f"Updating languageProfile: {config_data['languageProfile']}")
        updated_config["languageProfile"] = config_data["languageProfile"]
    
    if "promptTemplates" in config_data:
        logger.debug(f"Updating promptTemplates: {config_data['promptTemplates']}")
        updated_config["promptTemplates"] = config_data["promptTemplates"]
    
    if "conversationParameters" in config_data:
        logger.debug(f"Updating conversationParameters: {config_data['conversationParameters']}")
        updated_config["conversationParameters"] = config_data["conversationParameters"]
    
    # Update the configuration in the data store
    _npc_configs[npc_id] = updated_config
    
    logger.debug(f"Updated config: {_npc_configs[npc_id]}")
    
    return _npc_configs[npc_id]


# Create mock data for testing
def _create_mock_data():
    """Create mock data for testing."""
    # Ticket Operator NPC
    ticket_operator_id = "ticket_operator"
    _npcs[ticket_operator_id] = {
        "npc_id": ticket_operator_id,
        "name": "Tanaka",
        "role": "Ticket Machine Operator",
        "location": "ticket_gate_area",
        "available_dialogue_topics": [
            "ticket_purchase",
            "ticket_types",
            "fares",
            "destinations",
            "payment_methods"
        ],
        "visual_appearance": {
            "sprite_key": "ticket_operator_sprite",
            "animations": [
                "idle",
                "talking",
                "pointing",
                "operating_machine",
                "bowing"
            ]
        },
        "status": {
            "active": True,
            "current_emotion": "neutral",
            "current_activity": "standing_by_machine"
        }
    }
    
    _npc_configs[ticket_operator_id] = {
        "npc_id": ticket_operator_id,
        "profile": {
            "name": "Tanaka",
            "role": "Ticket Machine Operator",
            "location": "Ticket Gate Area",
            "personality": [
                "Helpful",
                "Technical",
                "Patient",
                "Efficient",
                "Detail-oriented"
            ],
            "expertise": [
                "Ticket types",
                "Fares",
                "Machine operation",
                "Payment methods",
                "Route information"
            ],
            "limitations": [
                "Only knows about Tokyo Station",
                "Limited knowledge of special events",
                "Cannot assist with non-transportation issues"
            ]
        },
        "language_profile": {
            "default_language": "japanese",
            "japanese_level": "N5",
            "speech_patterns": [
                "Polite but direct instruction giving",
                "Uses technical ticket terminology",
                "Clear step-by-step guidance",
                "Uses official station announcements style"
            ],
            "common_phrases": [
                "このボタンを押してください",
                "～円です",
                "片道ですか、往復ですか？",
                "切符はここから出てきます",
                "お手伝いできますか？"
            ],
            "vocabulary_focus": [
                "transportation",
                "directions",
                "money",
                "time"
            ]
        },
        "prompt_templates": {
            "initial_greeting": "いらっしゃいませ。切符の購入をお手伝いします。どちらまで行かれますか？ (Welcome. I can help you purchase a ticket. Where would you like to go?)",
            "response_format": "{japanese_text} ({english_translation})",
            "error_handling": "すみません、もう一度言っていただけますか？ (I'm sorry, could you please say that again?)",
            "conversation_close": "良い旅を！ (Have a good trip!)"
        },
        "conversation_parameters": {
            "max_turns": 15,
            "temperature_default": 0.7,
            "context_window_size": 2048
        }
    }
    
    # Information Desk Attendant NPC
    info_desk_id = "info_desk_attendant"
    _npcs[info_desk_id] = {
        "npc_id": info_desk_id,
        "name": "Yamada",
        "role": "Information Desk Attendant",
        "location": "central_hall",
        "available_dialogue_topics": [
            "station_layout",
            "train_schedules",
            "nearby_attractions",
            "lost_and_found",
            "station_services"
        ],
        "visual_appearance": {
            "sprite_key": "info_desk_attendant_sprite",
            "animations": [
                "idle",
                "talking",
                "bowing",
                "pointing_to_map",
                "checking_computer"
            ]
        },
        "status": {
            "active": True,
            "current_emotion": "friendly",
            "current_activity": "greeting_travelers"
        }
    }
    
    _npc_configs[info_desk_id] = {
        "npc_id": info_desk_id,
        "profile": {
            "name": "Yamada",
            "role": "Information Desk Attendant",
            "location": "Central Hall",
            "personality": [
                "Friendly",
                "Knowledgeable",
                "Patient",
                "Attentive",
                "Resourceful"
            ],
            "expertise": [
                "Station layout",
                "Train schedules",
                "Tourist information",
                "Station services",
                "Lost and found procedures"
            ],
            "limitations": [
                "Limited knowledge of areas outside Tokyo",
                "Cannot provide detailed technical assistance",
                "No access to passenger records"
            ]
        },
        "language_profile": {
            "default_language": "japanese",
            "japanese_level": "N5",
            "speech_patterns": [
                "Very polite and formal speech",
                "Uses simple, clear explanations",
                "Frequently offers additional helpful information",
                "Uses gestures to aid understanding"
            ],
            "common_phrases": [
                "いらっしゃいませ",
                "どのようにお手伝いできますか？",
                "～はこちらです",
                "少々お待ちください",
                "他にご質問はありますか？"
            ],
            "vocabulary_focus": [
                "directions",
                "locations",
                "time",
                "services"
            ]
        },
        "prompt_templates": {
            "initial_greeting": "いらっしゃいませ。東京駅案内所です。どのようにお手伝いできますか？ (Welcome. This is the Tokyo Station Information Desk. How may I help you?)",
            "response_format": "{japanese_text} ({english_translation})",
            "error_handling": "申し訳ありませんが、もう一度お願いできますか？ (I'm sorry, could you please repeat that?)",
            "conversation_close": "良い一日をお過ごしください。 (Have a nice day.)"
        },
        "conversation_parameters": {
            "max_turns": 20,
            "temperature_default": 0.6,
            "context_window_size": 2048
        }
    }
    
    # Create mock interaction states
    player1_id = "player123"
    _interaction_states[player1_id] = {}
    
    # Player 1 - Ticket Operator interaction
    _interaction_states[player1_id][ticket_operator_id] = {
        "player_id": player1_id,
        "npc_id": ticket_operator_id,
        "relationship_metrics": {
            "familiarity_level": 0.45,
            "interaction_count": 3,
            "last_interaction_time": datetime.now(timezone.utc) - timedelta(hours=2)
        },
        "conversation_state": {
            "active_conversation": True,
            "conversation_id": "conv_20250310143217_ticket_operator",
            "turn_count": 4,
            "pending_response": True
        },
        "game_progress_unlocks": {
            "unlocked_topics": [
                "ticket_purchase",
                "station_layout",
                "train_schedules"
            ],
            "completed_interactions": [
                "initial_greeting",
                "ticket_inquiry"
            ],
            "available_quests": [
                "find_platform_for_odawara"
            ]
        }
    }
    
    # Player 1 - Information Desk interaction
    _interaction_states[player1_id][info_desk_id] = {
        "player_id": player1_id,
        "npc_id": info_desk_id,
        "relationship_metrics": {
            "familiarity_level": 0.2,
            "interaction_count": 1,
            "last_interaction_time": datetime.now(timezone.utc) - timedelta(days=1)
        },
        "conversation_state": {
            "active_conversation": False,
            "conversation_id": None,
            "turn_count": 0,
            "pending_response": False
        },
        "game_progress_unlocks": {
            "unlocked_topics": [
                "station_layout",
                "nearby_attractions"
            ],
            "completed_interactions": [
                "initial_greeting"
            ],
            "available_quests": [
                "find_tourist_information"
            ]
        }
    }
    
    # Player 2
    player2_id = "player456"
    _interaction_states[player2_id] = {}
    
    # Player 2 - Information Desk interaction
    _interaction_states[player2_id][info_desk_id] = {
        "player_id": player2_id,
        "npc_id": info_desk_id,
        "relationship_metrics": {
            "familiarity_level": 0.6,
            "interaction_count": 5,
            "last_interaction_time": datetime.now(timezone.utc) - timedelta(hours=5)
        },
        "conversation_state": {
            "active_conversation": False,
            "conversation_id": None,
            "turn_count": 0,
            "pending_response": False
        },
        "game_progress_unlocks": {
            "unlocked_topics": [
                "station_layout",
                "train_schedules",
                "nearby_attractions",
                "lost_and_found"
            ],
            "completed_interactions": [
                "initial_greeting",
                "station_inquiry",
                "schedule_inquiry"
            ],
            "available_quests": [
                "find_lost_item",
                "explore_tokyo_tower"
            ]
        }
    }


# Create mock data when module is imported
_create_mock_data() 