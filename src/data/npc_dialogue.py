"""
Data access layer for NPC dialogue functionality.
"""

import logging
import uuid
import time
import random
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from src.data.npc import get_npc_information, get_npc_configuration
from src.data.player import get_player_by_id

logger = logging.getLogger(__name__)

# In-memory storage for conversations
# In a production environment, this would be stored in a database
_conversations: Dict[str, Dict[str, Any]] = {}


def npc_exists(npc_id: str) -> bool:
    """
    Check if an NPC with the given ID exists.
    
    Args:
        npc_id: The ID of the NPC to check.
        
    Returns:
        True if the NPC exists, False otherwise.
    """
    try:
        return get_npc_information(npc_id) is not None
    except Exception as e:
        logger.error(f"Error checking if NPC exists: {e}")
        return False


def player_exists(player_id: str) -> bool:
    """
    Check if a player with the given ID exists.
    
    Args:
        player_id: The ID of the player to check.
        
    Returns:
        True if the player exists, False otherwise.
    """
    try:
        return get_player_by_id(player_id) is not None
    except Exception as e:
        logger.error(f"Error checking if player exists: {e}")
        return False


def create_conversation(player_id: str, npc_id: str) -> str:
    """
    Create a new conversation between a player and an NPC.
    
    Args:
        player_id: The ID of the player.
        npc_id: The ID of the NPC.
        
    Returns:
        The ID of the new conversation.
    """
    conversation_id = str(uuid.uuid4())
    _conversations[conversation_id] = {
        "player_id": player_id,
        "npc_id": npc_id,
        "exchanges": [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    return conversation_id


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a conversation by its ID.
    
    Args:
        conversation_id: The ID of the conversation.
        
    Returns:
        The conversation data, or None if not found.
    """
    return _conversations.get(conversation_id)


def add_exchange_to_conversation(
    conversation_id: str, 
    player_text: str, 
    npc_text: str
) -> bool:
    """
    Add an exchange to a conversation.
    
    Args:
        conversation_id: The ID of the conversation.
        player_text: The text from the player.
        npc_text: The text from the NPC.
        
    Returns:
        True if the exchange was added, False otherwise.
    """
    conversation = get_conversation(conversation_id)
    if not conversation:
        return False
    
    now = datetime.now().isoformat()
    
    conversation["exchanges"].append({
        "player": {
            "text": player_text,
            "timestamp": now
        },
        "npc": {
            "text": npc_text,
            "timestamp": now
        }
    })
    
    conversation["updated_at"] = now
    return True


def is_supported_language(language: str) -> bool:
    """
    Check if a language is supported.
    
    Args:
        language: The language to check.
        
    Returns:
        True if the language is supported, False otherwise.
    """
    return language.lower() in ["japanese", "english"]


def process_dialogue(
    player_context: Dict[str, Any],
    game_context: Dict[str, Any],
    npc_id: str,
    player_input: Dict[str, Any],
    conversation_context: Dict[str, Any]
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Process dialogue with an NPC.
    
    Args:
        player_context: Context information about the player.
        game_context: Context information about the current game state.
        npc_id: The ID of the NPC to interact with.
        player_input: Input provided by the player.
        conversation_context: Context of the current conversation.
        
    Returns:
        A tuple containing the NPC's response and any game state changes.
    """
    start_time = time.time()
    
    # Get NPC data
    npc_data = get_npc_information(npc_id)
    npc_config = get_npc_configuration(npc_id)
    
    # Get or create conversation
    conversation_id = conversation_context.get("conversationId")
    if not conversation_id:
        conversation_id = create_conversation(player_context["playerId"], npc_id)
    
    # Determine AI tier to use (rule-based, local, or cloud)
    # In a real implementation, this would be more sophisticated
    ai_tier_roll = random.random()
    if ai_tier_roll < 0.7:  # 70% rule-based
        ai_tier = "rule"
    elif ai_tier_roll < 0.9:  # 20% local
        ai_tier = "local"
    else:  # 10% cloud
        ai_tier = "cloud"
    
    # Generate NPC response based on AI tier
    # In a real implementation, this would call different AI systems
    if ai_tier == "rule":
        npc_response = generate_rule_based_response(npc_data, npc_config, player_input, game_context)
    elif ai_tier == "local":
        npc_response = generate_local_ai_response(npc_data, npc_config, player_input, game_context)
    else:  # cloud
        npc_response = generate_cloud_ai_response(npc_data, npc_config, player_input, game_context)
    
    # Generate expected input
    expected_input = generate_expected_input(npc_data, npc_config, game_context)
    
    # Determine game state changes
    game_state_changes = determine_game_state_changes(npc_data, npc_config, player_input, game_context)
    
    # Add exchange to conversation
    add_exchange_to_conversation(
        conversation_id,
        player_input["text"],
        npc_response["japanese"]
    )
    
    # Calculate processing time
    processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    # Create response
    response = {
        "conversationId": conversation_id,
        "npcResponse": npc_response,
        "expectedInput": expected_input,
        "gameStateChanges": game_state_changes,
        "meta": {
            "processingTime": processing_time,
            "aiTier": ai_tier,
            "confidenceScore": 0.85  # In a real implementation, this would be calculated
        }
    }
    
    return response, game_state_changes


def generate_rule_based_response(
    npc_data: Dict[str, Any],
    npc_config: Dict[str, Any],
    player_input: Dict[str, Any],
    game_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a rule-based response from an NPC.
    
    Args:
        npc_data: Data about the NPC.
        npc_config: Configuration for the NPC.
        player_input: Input provided by the player.
        game_context: Context information about the current game state.
        
    Returns:
        The NPC's response.
    """
    # In a real implementation, this would use a rule-based system
    # For now, we'll return a simple response based on the NPC's role
    
    npc_role = npc_data.get("role", "station_staff")
    
    responses = {
        "ticket_operator": {
            "text": "How can I help you with your ticket purchase?",
            "japanese": "切符の購入についてどのようにお手伝いできますか？",
            "animation": "talking",
            "emotion": "neutral"
        },
        "information_desk": {
            "text": "Welcome to Tokyo Station. How can I assist you today?",
            "japanese": "東京駅へようこそ。今日はどのようにお手伝いできますか？",
            "animation": "greeting",
            "emotion": "happy"
        },
        "shop_keeper": {
            "text": "Welcome! Please take a look at our products.",
            "japanese": "いらっしゃいませ！商品をご覧ください。",
            "animation": "bowing",
            "emotion": "happy"
        },
        "station_staff": {
            "text": "How may I assist you?",
            "japanese": "どのようにお手伝いできますか？",
            "animation": "idle",
            "emotion": "neutral"
        }
    }
    
    response = responses.get(npc_role, responses["station_staff"])
    
    # Add language learning feedback
    response["feedback"] = {
        "grammar": [
            {
                "pattern": "〜ください",
                "explanation": "Polite request form",
                "level": "N5"
            }
        ],
        "vocabulary": [
            {
                "word": "切符",
                "reading": "きっぷ",
                "meaning": "ticket",
                "level": "N5"
            }
        ]
    }
    
    return response


def generate_local_ai_response(
    npc_data: Dict[str, Any],
    npc_config: Dict[str, Any],
    player_input: Dict[str, Any],
    game_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a response from an NPC using a local AI model.
    
    Args:
        npc_data: Data about the NPC.
        npc_config: Configuration for the NPC.
        player_input: Input provided by the player.
        game_context: Context information about the current game state.
        
    Returns:
        The NPC's response.
    """
    # In a real implementation, this would use a local AI model
    # For now, we'll return a simple response
    
    return {
        "text": "I understand you need a ticket to Odawara. Would you like a one-way or round-trip ticket?",
        "japanese": "小田原までの切符が必要なのですね。片道と往復どちらがよろしいですか？",
        "animation": "thinking",
        "emotion": "helpful",
        "feedback": {
            "grammar": [
                {
                    "pattern": "〜までの",
                    "explanation": "Indicates destination with particle 'made'",
                    "level": "N5"
                }
            ],
            "vocabulary": [
                {
                    "word": "片道",
                    "reading": "かたみち",
                    "meaning": "one-way",
                    "level": "N4"
                },
                {
                    "word": "往復",
                    "reading": "おうふく",
                    "meaning": "round-trip",
                    "level": "N4"
                }
            ]
        }
    }


def generate_cloud_ai_response(
    npc_data: Dict[str, Any],
    npc_config: Dict[str, Any],
    player_input: Dict[str, Any],
    game_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a response from an NPC using a cloud AI service.
    
    Args:
        npc_data: Data about the NPC.
        npc_config: Configuration for the NPC.
        player_input: Input provided by the player.
        game_context: Context information about the current game state.
        
    Returns:
        The NPC's response.
    """
    # In a real implementation, this would call a cloud AI service
    # For now, we'll return a simple response
    
    return {
        "text": "I see you're trying to buy a ticket to Odawara. The fare is 1,490 yen for a one-way ticket. Would you like to proceed with the purchase?",
        "japanese": "小田原までの切符を買おうとしているのですね。片道料金は1,490円です。購入を進めますか？",
        "animation": "explaining",
        "emotion": "helpful",
        "feedback": {
            "grammar": [
                {
                    "pattern": "〜ようとしている",
                    "explanation": "Indicates an action one is about to do",
                    "level": "N3"
                }
            ],
            "vocabulary": [
                {
                    "word": "料金",
                    "reading": "りょうきん",
                    "meaning": "fare/fee",
                    "level": "N4"
                },
                {
                    "word": "購入",
                    "reading": "こうにゅう",
                    "meaning": "purchase",
                    "level": "N3"
                }
            ]
        }
    }


def generate_expected_input(
    npc_data: Dict[str, Any],
    npc_config: Dict[str, Any],
    game_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate the expected input from the player.
    
    Args:
        npc_data: Data about the NPC.
        npc_config: Configuration for the NPC.
        game_context: Context information about the current game state.
        
    Returns:
        The expected input.
    """
    # In a real implementation, this would be more sophisticated
    # For now, we'll return a simple expected input
    
    if random.random() < 0.3:  # 30% chance of selection input
        return {
            "type": "selection",
            "options": [
                {
                    "id": "one_way",
                    "text": "One-way ticket",
                    "japanese": "片道",
                    "hint": "For travel in one direction only"
                },
                {
                    "id": "round_trip",
                    "text": "Round-trip ticket",
                    "japanese": "往復",
                    "hint": "For travel to and from a destination"
                }
            ],
            "prompt": "Please select a ticket type"
        }
    else:  # 70% chance of free text input
        return {
            "type": "free_text",
            "prompt": "Please respond to the station attendant"
        }


def determine_game_state_changes(
    npc_data: Dict[str, Any],
    npc_config: Dict[str, Any],
    player_input: Dict[str, Any],
    game_context: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Determine any changes to the game state based on the dialogue.
    
    Args:
        npc_data: Data about the NPC.
        npc_config: Configuration for the NPC.
        player_input: Input provided by the player.
        game_context: Context information about the current game state.
        
    Returns:
        A list of game state changes.
    """
    # In a real implementation, this would be more sophisticated
    # For now, we'll return a simple game state change
    
    changes = []
    
    # Check if this interaction should progress a quest
    current_quest = game_context.get("currentQuest")
    quest_step = game_context.get("questStep")
    
    if current_quest == "buy_ticket_to_odawara" and quest_step == "find_ticket_machine":
        # Progress the quest
        changes.append({
            "type": "quest_progress",
            "data": {
                "quest": "buy_ticket_to_odawara",
                "step": "interact_with_ticket_operator",
                "completed": False
            }
        })
    
    # Add language learning progress
    changes.append({
        "type": "language_progress",
        "data": {
            "vocabularyLearned": ["切符", "片道", "往復"],
            "grammarPointsPracticed": ["〜ください", "〜までの"]
        }
    })
    
    return changes 