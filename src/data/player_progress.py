"""
Data access layer for player progress.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class PlayerNotFoundError(Exception):
    """Raised when a player is not found."""
    pass

class PlayerProgressData:
    """Data structure for player progress."""
    def __init__(self, player_id: str, level: str):
        self.player_id = player_id
        self.level = level

class MockPlayerProgressProvider:
    """Provider for mock player progress data."""
    
    def __init__(self):
        """Initialize the mock data provider."""
        self._players = self._create_mock_players()
        self._vocabulary = self._create_mock_vocabulary()
        self._grammar = self._create_mock_grammar()
        self._conversation = self._create_mock_conversation()
        self._achievements = self._create_mock_achievements()
        self._recommendations = self._create_mock_recommendations()
        self._visualization_data = self._create_mock_visualization_data()
    
    def get_player(self, player_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a player by ID.
        
        Args:
            player_id: The player ID
            
        Returns:
            The player data, or None if not found
        """
        return self._players.get(player_id)
    
    def get_vocabulary_progress(self, player_id: str) -> Dict[str, Any]:
        """
        Get vocabulary progress for a player.
        
        Args:
            player_id: The player ID
            
        Returns:
            The vocabulary progress data
        """
        return self._vocabulary.get(player_id, self._create_default_vocabulary_progress())
    
    def get_grammar_progress(self, player_id: str) -> Dict[str, Any]:
        """
        Get grammar progress for a player.
        
        Args:
            player_id: The player ID
            
        Returns:
            The grammar progress data
        """
        return self._grammar.get(player_id, self._create_default_grammar_progress())
    
    def get_conversation_metrics(self, player_id: str) -> Dict[str, Any]:
        """
        Get conversation metrics for a player.
        
        Args:
            player_id: The player ID
            
        Returns:
            The conversation metrics data
        """
        return self._conversation.get(player_id, self._create_default_conversation_metrics())
    
    def get_achievements(self, player_id: str) -> List[str]:
        """
        Get achievements for a player.
        
        Args:
            player_id: The player ID
            
        Returns:
            The achievements list
        """
        return self._achievements.get(player_id, [])
    
    def get_recommendations(self, player_id: str) -> Dict[str, List[str]]:
        """
        Get recommendations for a player.
        
        Args:
            player_id: The player ID
            
        Returns:
            The recommendations data
        """
        return self._recommendations.get(player_id, self._create_default_recommendations())
    
    def get_visualization_data(self, player_id: str) -> Dict[str, Any]:
        """
        Get visualization data for a player.
        
        Args:
            player_id: The player ID
            
        Returns:
            The visualization data
        """
        return self._visualization_data.get(player_id, self._create_default_visualization_data())
    
    def _create_mock_players(self) -> Dict[str, Dict[str, Any]]:
        """
        Create mock player data.
        
        Returns:
            Dictionary of player ID to player data
        """
        return {
            "player123": {
                "id": "player123",
                "level": "N5"
            },
            "player456": {
                "id": "player456",
                "level": "N4"
            },
            "player789": {
                "id": "player789",
                "level": "N3"
            }
        }
    
    def _create_mock_vocabulary(self) -> Dict[str, Dict[str, Any]]:
        """
        Create mock vocabulary data.
        
        Returns:
            Dictionary of player ID to vocabulary data
        """
        return {
            "player123": {
                "total": 86,
                "mastered_count": 42,
                "learning_count": 31,
                "needs_review": 13,
                "percent_complete": 48.8,
                "mastered": [
                    {
                        "word": "切符",
                        "reading": "きっぷ",
                        "meaning": "ticket",
                        "examples": [
                            "切符を買います。",
                            "切符はどこで買えますか？"
                        ]
                    },
                    {
                        "word": "電車",
                        "reading": "でんしゃ",
                        "meaning": "train",
                        "examples": [
                            "電車に乗ります。",
                            "電車は何時に来ますか？"
                        ]
                    }
                ],
                "learning": [
                    {
                        "word": "改札",
                        "reading": "かいさつ",
                        "meaning": "ticket gate",
                        "mastery_level": 0.56,
                        "last_seen": "2025-03-08T14:22:30Z"
                    },
                    {
                        "word": "遅延",
                        "reading": "ちえん",
                        "meaning": "delay",
                        "mastery_level": 0.42,
                        "last_seen": "2025-03-09T10:15:45Z"
                    }
                ],
                "for_review": [
                    {
                        "word": "乗り換え",
                        "reading": "のりかえ",
                        "meaning": "transfer (trains)",
                        "due_for_review": True
                    },
                    {
                        "word": "特急",
                        "reading": "とっきゅう",
                        "meaning": "express train",
                        "due_for_review": False
                    }
                ]
            }
        }
    
    def _create_mock_grammar(self) -> Dict[str, Dict[str, Any]]:
        """
        Create mock grammar data.
        
        Returns:
            Dictionary of player ID to grammar data
        """
        return {
            "player123": {
                "total": 24,
                "mastered_count": 11,
                "learning_count": 8,
                "needs_review": 5,
                "percent_complete": 45.8,
                "accuracy_rates": {
                    "particles": 0.78,
                    "verb_forms": 0.65,
                    "sentences": 0.71
                },
                "mastered": [
                    {
                        "pattern": "〜ます",
                        "explanation": "Polite present affirmative verb ending",
                        "examples": [
                            "行きます (I go/will go)",
                            "買います (I buy/will buy)"
                        ]
                    },
                    {
                        "pattern": "〜ください",
                        "explanation": "Please do ~",
                        "examples": [
                            "見てください (Please look)",
                            "教えてください (Please tell me)"
                        ]
                    }
                ],
                "learning": [
                    {
                        "pattern": "〜てもいいですか",
                        "explanation": "May I ~?/Is it okay if I ~?",
                        "mastery_level": 0.65
                    },
                    {
                        "pattern": "〜なければなりません",
                        "explanation": "Must do ~/Have to do ~",
                        "mastery_level": 0.45
                    }
                ],
                "for_review": [
                    {
                        "pattern": "〜たことがあります",
                        "explanation": "Have experience doing ~",
                        "due_for_review": True
                    },
                    {
                        "pattern": "〜ながら",
                        "explanation": "While doing ~",
                        "due_for_review": False
                    }
                ]
            }
        }
    
    def _create_mock_conversation(self) -> Dict[str, Dict[str, Any]]:
        """
        Create mock conversation metrics data.
        
        Returns:
            Dictionary of player ID to conversation metrics data
        """
        return {
            "player123": {
                "success_rate": 0.82,
                "completed_exchanges": 27
            }
        }
    
    def _create_mock_achievements(self) -> Dict[str, List[str]]:
        """
        Create mock achievements data.
        
        Returns:
            Dictionary of player ID to achievements list
        """
        return {
            "player123": [
                "first_conversation_completed",
                "ticket_purchased",
                "five_new_vocabulary_mastered",
                "particle_master_level_1"
            ]
        }
    
    def _create_mock_recommendations(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Create mock recommendations data.
        
        Returns:
            Dictionary of player ID to recommendations data
        """
        return {
            "player123": {
                "focusAreas": [
                    "verb_conjugation",
                    "station_vocabulary",
                    "direction_phrases"
                ],
                "suggestedActivities": [
                    "practice_ticket_machine_dialogue",
                    "review_direction_vocabulary",
                    "complete_station_announcement_challenge"
                ]
            }
        }
    
    def _create_mock_visualization_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Create mock visualization data.
        
        Returns:
            Dictionary of player ID to visualization data
        """
        return {
            "player123": {
                "skill_pentagon": {
                    "reading": 0.62,
                    "writing": 0.48,
                    "listening": 0.71,
                    "speaking": 0.54,
                    "vocabulary": 0.65
                },
                "progress_over_time": [
                    {
                        "date": "2025-03-01",
                        "vocabulary_mastered": 25,
                        "grammar_mastered": 8
                    },
                    {
                        "date": "2025-03-05",
                        "vocabulary_mastered": 34,
                        "grammar_mastered": 9
                    },
                    {
                        "date": "2025-03-10",
                        "vocabulary_mastered": 42,
                        "grammar_mastered": 11
                    }
                ]
            }
        }
    
    def _create_default_vocabulary_progress(self) -> Dict[str, Any]:
        """
        Create default vocabulary progress data.
        
        Returns:
            Default vocabulary progress data
        """
        return {
            "total": 50,
            "mastered_count": 10,
            "learning_count": 20,
            "needs_review": 20,
            "percent_complete": 20.0,
            "mastered": [],
            "learning": [],
            "for_review": []
        }
    
    def _create_default_grammar_progress(self) -> Dict[str, Any]:
        """
        Create default grammar progress data.
        
        Returns:
            Default grammar progress data
        """
        return {
            "total": 20,
            "mastered_count": 5,
            "learning_count": 10,
            "needs_review": 5,
            "percent_complete": 25.0,
            "accuracy_rates": {
                "particles": 0.5,
                "verb_forms": 0.5,
                "sentences": 0.5
            },
            "mastered": [],
            "learning": [],
            "for_review": []
        }
    
    def _create_default_conversation_metrics(self) -> Dict[str, Any]:
        """
        Create default conversation metrics data.
        
        Returns:
            Default conversation metrics data
        """
        return {
            "success_rate": 0.5,
            "completed_exchanges": 10
        }
    
    def _create_default_recommendations(self) -> Dict[str, List[str]]:
        """
        Create default recommendations data.
        
        Returns:
            Default recommendations data
        """
        return {
            "focusAreas": [
                "basic_vocabulary",
                "basic_grammar"
            ],
            "suggestedActivities": [
                "complete_basic_conversation_tutorial",
                "practice_basic_greetings"
            ]
        }
    
    def _create_default_visualization_data(self) -> Dict[str, Any]:
        """
        Create default visualization data.
        
        Returns:
            Default visualization data
        """
        return {
            "skill_pentagon": {
                "reading": 0.3,
                "writing": 0.3,
                "listening": 0.3,
                "speaking": 0.3,
                "vocabulary": 0.3
            },
            "progress_over_time": [
                {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "vocabulary_mastered": 10,
                    "grammar_mastered": 5
                }
            ]
        }


class PlayerProgressService:
    """Service for managing player progress."""
    
    def __init__(self):
        """Initialize the service with mock data provider."""
        self._provider = MockPlayerProgressProvider()
    
    def get_player_progress(self, player_id: str) -> PlayerProgressData:
        """
        Get progress data for a player.
        
        Args:
            player_id: The player ID
            
        Returns:
            PlayerProgressData object with progress information
            
        Raises:
            PlayerNotFoundError: If player is not found
        """
        player = self._provider.get_player(player_id)
        if not player:
            raise PlayerNotFoundError(f"Player {player_id} not found")
            
        return PlayerProgressData(
            player_id=player["id"],
            level=player["level"]
        )


# Create a singleton instance of the service
player_progress_service = PlayerProgressService() 