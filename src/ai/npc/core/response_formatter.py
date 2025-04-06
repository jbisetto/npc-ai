"""
Response Formatter for the Companion AI.

This module contains the ResponseFormatter class, which is responsible for
formatting responses from the processors to add personality, learning cues,
and other enhancements.
"""

import random
import logging
from typing import Dict, List, Optional, Any

from src.ai.npc.core.models import ClassifiedRequest
from src.ai.npc.personality.config import PersonalityConfig

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """
    Formats processor responses to add personality, learning cues, and other enhancements.
    
    The ResponseFormatter takes the raw response from a processor and enhances it with:
    - Personality traits (friendliness, enthusiasm, etc.)
    - Learning cues (tips, hints, etc.)
    - Emotional expressions (happy, excited, etc.)
    - Suggested actions for the player
    
    It also validates responses to ensure they meet minimum quality standards.
    """
    
    # Default personality traits if none are provided
    DEFAULT_PERSONALITY = {
        "friendliness": 0.8,  # 0.0 = cold, 1.0 = very friendly
        "enthusiasm": 0.7,    # 0.0 = subdued, 1.0 = very enthusiastic
        "helpfulness": 0.9,   # 0.0 = minimal help, 1.0 = very helpful
        "playfulness": 0.6,   # 0.0 = serious, 1.0 = very playful
        "formality": 0.3      # 0.0 = casual, 1.0 = very formal
    }
    
    # Emotion expressions for the companion
    EMOTION_EXPRESSIONS = {
        "happy": [
            "I wag my tail happily!",
            "My tail wags with joy!",
            "*happy bark*",
            "*smiles with tongue out*",
            "I'm so happy to help you!"
        ],
        "excited": [
            "I bounce around excitedly!",
            "*excited barking*",
            "I can barely contain my excitement!",
            "*tail wagging intensifies*",
            "I'm super excited about this!"
        ],
        "neutral": [
            "*attentive ears*",
            "*tilts head*",
            "*looks at you with curious eyes*",
            "*sits attentively*",
            "I'm here to help!"
        ],
        "thoughtful": [
            "*thoughtful head tilt*",
            "*contemplative look*",
            "*ears perk up in thought*",
            "Hmm, let me think about that...",
            "*looks up thoughtfully*"
        ],
        "concerned": [
            "*concerned whimper*",
            "*worried look*",
            "*ears flatten slightly*",
            "I'm a bit worried about that...",
            "*concerned head tilt*"
        ]
    }
    
    # Learning cues to add to responses
    LEARNING_CUES = {
        "default": [
            "Remember: Practice makes perfect!",
            "Tip: Taking notes can help reinforce what you're learning.",
            "Practice point: Try using what you've learned in a real conversation.",
            "Note: Learning a language takes time and patience.",
            "Hint: Don't be afraid to make mistakes - they're part of learning!"
        ]
    }
    
    # Friendly phrases to add based on friendliness level
    FRIENDLY_PHRASES = {
        "high": [
            "I'm so happy to help you with this!",
            "That's a great question, friend!",
            "I'm really glad you asked about this!",
            "It's wonderful to see you learning Japanese!",
            "You're doing an excellent job with your Japanese studies!"
        ],
        "medium": [
            "I'm happy to help with this.",
            "That's a good question.",
            "I'm glad you asked about this.",
            "It's nice to see you learning Japanese.",
            "You're doing well with your Japanese studies."
        ],
        "low": [
            "Here's the information.",
            "The answer is as follows.",
            "This is what you need to know.",
            "Here's what I can tell you.",
            "This should answer your question."
        ]
    }
    
    # Enthusiasm phrases to add based on enthusiasm level
    ENTHUSIASM_PHRASES = {
        "high": [
            "I'm super excited to explain this!",
            "This is such a fun topic to explore!",
            "I absolutely love helping with this kind of question!",
            "Learning Japanese is so exciting, isn't it?",
            "I can't wait to see you master this concept!"
        ],
        "medium": [
            "I'm happy to explain this.",
            "This is an interesting topic.",
            "I enjoy helping with these questions.",
            "Learning Japanese is rewarding.",
            "You'll get better with practice."
        ],
        "low": [
            "Let me explain this.",
            "Here's how it works.",
            "This is the explanation.",
            "Japanese has these patterns.",
            "Practice will help you improve."
        ]
    }
    
    def __init__(
        self, 
        default_personality: Optional[Dict[str, float]] = None,
        personality_traits: Optional[Dict[str, float]] = None,
        personality_config: Optional[PersonalityConfig] = None,
        profile_registry: Optional[Any] = None,
        force_enable_personality: bool = False  # Added for testing
    ):
        """
        Initialize the response formatter.
        
        Args:
            default_personality: Optional custom personality traits to use (legacy)
            personality_traits: Optional custom personality traits to use (same as default_personality)
            personality_config: Optional personality configuration to use
            profile_registry: Optional registry for NPC personality profiles
            force_enable_personality: Force enable personality features for testing
        """
        # Set up logger
        self.logger = logging.getLogger(__name__)
        
        # Start with the default personality
        self.personality = self.DEFAULT_PERSONALITY.copy()
        
        # Set personality traits, with priority order:
        # 1. personality_traits (for backward compatibility)
        # 2. default_personality (for new code)
        if personality_traits:
            self.personality.update(personality_traits)
        elif default_personality:
            self.personality.update(default_personality)
            
        # Store personality config and profile registry
        self.personality_config = personality_config
        self.profile_registry = profile_registry
        
        # Store force enable flag for testing
        self.force_enable_personality = force_enable_personality
        
    def format_response(
        self,
        response_text: Optional[str] = None,
        request: Optional[ClassifiedRequest] = None,
        emotion: Optional[str] = None,
        processor_response: Optional[str] = None,
        classified_request: Optional[ClassifiedRequest] = None,
        add_learning_cues: bool = True,
        suggested_actions: Optional[List[str]] = None
    ) -> str:
        """
        Format a response with personality traits, learning cues, and other enhancements.
        
        Args:
            response_text: The raw response text (new style)
            request: The classified request (new style)
            emotion: Optional emotion to express
            processor_response: The raw response text (legacy)
            classified_request: The classified request (legacy)
            add_learning_cues: Whether to add learning cues
            suggested_actions: Optional list of suggested actions
            
        Returns:
            The formatted response string
        """
        # Handle both new and legacy parameter styles
        response = response_text if response_text is not None else processor_response
        req = request if request is not None else classified_request
        
        if not response:
            raise ValueError("No response text provided")
            
        # Start with the raw response
        formatted_response = response
        
        # Add name prefix if profile registry exists
        if self.profile_registry is not None:
            try:
                # If request has a profile_id, use that profile
                if req and req.profile_id:
                    profile = self.profile_registry.get_profile(req.profile_id)
                    if profile and profile.name:
                        formatted_response = f"{profile.name}: {formatted_response}"
                    else:
                        formatted_response = f"Hachi: {formatted_response}"
                else:
                    # Otherwise use active profile
                    active_profile = self.profile_registry.get_active_profile()
                    if active_profile and active_profile.name:
                        formatted_response = f"{active_profile.name}: {formatted_response}"
                    else:
                        formatted_response = f"Hachi: {formatted_response}"
            except Exception as e:
                self.logger.warning(f"Failed to get profile: {e}")
                formatted_response = f"Hachi: {formatted_response}"
        
        # Only add personality if enabled in config or forced for testing
        if self.force_enable_personality:
            # Build the response with personality elements
            personality_elements = []
            
            # Add friendly greeting based on friendliness level
            if random.random() < self.personality["friendliness"]:
                friendly_level = "high" if self.personality["friendliness"] > 0.7 else "medium" if self.personality["friendliness"] > 0.3 else "low"
                friendly_phrase = random.choice(self.FRIENDLY_PHRASES[friendly_level])
                personality_elements.append(friendly_phrase)
                
            # Add enthusiasm based on enthusiasm level
            if random.random() < self.personality["enthusiasm"]:
                enthusiasm_level = "high" if self.personality["enthusiasm"] > 0.7 else "medium" if self.personality["enthusiasm"] > 0.3 else "low"
                enthusiasm_phrase = random.choice(self.ENTHUSIASM_PHRASES[enthusiasm_level])
                personality_elements.append(enthusiasm_phrase)
                
            # Add emotion expression if provided
            if emotion and emotion in self.EMOTION_EXPRESSIONS:
                emotion_phrase = random.choice(self.EMOTION_EXPRESSIONS[emotion])
                personality_elements.append(emotion_phrase)
                
            # Add learning cues if enabled and request is provided
            if add_learning_cues and req:
                intent_cues = self.LEARNING_CUES.get(req.intent, self.LEARNING_CUES["default"])
                learning_cue = random.choice(intent_cues)
                
                # Format learning cue with extracted entities if available
                if req.extracted_entities:
                    try:
                        learning_cue = learning_cue.format(**req.extracted_entities)
                    except KeyError:
                        # If formatting fails, use a default cue
                        learning_cue = random.choice(self.LEARNING_CUES["default"])
                        
                personality_elements.append(learning_cue)
                
            # Add suggested actions if provided
            if suggested_actions:
                actions_text = "\n".join(f"- {action}" for action in suggested_actions)
                personality_elements.append(f"Suggested actions:\n{actions_text}")
                
            # Combine all elements
            if personality_elements:
                formatted_response = formatted_response + "\n\n" + "\n\n".join(personality_elements)
                
        # Log response details
        self.logger.debug(f"Formatted response length: {len(formatted_response)}")
        if req:
            self.logger.debug(f"Request type: {req.request_type}, Intent: {req.intent}")
            
        return formatted_response
    
    def _validate_response(self, response: str, request: ClassifiedRequest) -> str:
        """
        Validate and clean up a response.
        
        Args:
            response: The response to validate
            request: The request that generated the response
            
        Returns:
            The validated response
        """
        # Check if response is empty or too short
        if not response or len(response.strip()) < 10:
            logger.warning(f"Response too short, using fallback: {response}")
            return "I'm sorry, I couldn't generate a proper response. Could you please rephrase your question?"
        
        # Check if response is too long (more than 500 characters)
        if len(response) > 500:
            logger.info(f"Response too long ({len(response)} chars), truncating")
            # Try to truncate at a sentence boundary
            truncated = response[:497]
            last_period = truncated.rfind('.')
            if last_period > 400:  # Only truncate at period if it's not too short
                truncated = truncated[:last_period + 1]
            else:
                truncated += "..."
            return truncated
        
        return response
    
    def _create_opening(self, request: ClassifiedRequest) -> Optional[str]:
        """
        Create an opening/greeting based on personality and request.
        
        Args:
            request: The request to create an opening for
            
        Returns:
            An opening string, or None if no opening should be added
        """
        # Get the friendliness level
        friendliness = float(self.personality.get("friendliness", 0.5))
        
        # Determine which set of phrases to use based on friendliness
        if friendliness > 0.7:
            phrases = self.FRIENDLY_PHRASES["high"]
        elif friendliness > 0.3:
            phrases = self.FRIENDLY_PHRASES["medium"]
        else:
            phrases = self.FRIENDLY_PHRASES["low"]
        
        # Only add an opening sometimes, based on friendliness
        if random.random() < friendliness:
            return random.choice(phrases)
        
        return None
    
    def _create_closing(self, request: ClassifiedRequest) -> Optional[str]:
        """
        Create a closing based on personality and request.
        
        Args:
            request: The request to create a closing for
            
        Returns:
            A closing string, or None if no closing should be added
        """
        # Get the helpfulness level
        helpfulness = float(self.personality.get("helpfulness", 0.9))
        
        # Closings for different helpfulness levels
        closings = {
            "high": [
                "Is there anything else you'd like to know?",
                "Let me know if you need any more help!",
                "Feel free to ask if you have any other questions!",
                "I'm here if you need any more assistance!",
                "Don't hesitate to ask if you need more help!"
            ],
            "medium": [
                "Hope that helps.",
                "Let me know if you have questions.",
                "Feel free to ask more questions.",
                "I'm here to help if needed.",
                "Ask if you need more information."
            ],
            "low": [
                "That's the information.",
                "That concludes my explanation.",
                "That's all for this topic.",
                "That's what you need to know.",
                "That's the answer to your question."
            ]
        }
        
        # Determine which set of closings to use
        if helpfulness > 0.7:
            closing_set = closings["high"]
        elif helpfulness > 0.3:
            closing_set = closings["medium"]
        else:
            closing_set = closings["low"]
        
        # Only add a closing sometimes, based on helpfulness
        if random.random() < helpfulness * 0.5:
            return random.choice(closing_set)
        
        return None
    
    def _create_learning_cue(self, request: ClassifiedRequest) -> Optional[str]:
        """
        Create a learning cue based on the request intent.
        
        Args:
            request: The request to create a learning cue for
            
        Returns:
            A learning cue string, or None if no cue could be created
        """
        # Get the appropriate cues for the intent
        intent = request.intent if hasattr(request, 'intent') else None
        cues = self.LEARNING_CUES.get(intent, self.LEARNING_CUES["default"])
        
        # Select a random cue
        cue_template = random.choice(cues)
        
        # Try to fill in placeholders
        try:
            # Get entities from the request
            entities = getattr(request, 'extracted_entities', {}) or {}
            
            # For vocabulary help, try to extract word and meaning
            if intent == IntentCategory.VOCABULARY_HELP and 'word' in entities:
                word = entities['word']
                meaning = entities.get('meaning', 'unknown')
                return cue_template.format(word=word, meaning=meaning)
            
            # For grammar explanation, try to extract pattern
            elif intent == IntentCategory.GRAMMAR_EXPLANATION and 'pattern' in entities:
                pattern = entities['pattern']
                return cue_template.format(pattern=pattern)
            
            # For translation confirmation, try to extract original and translation
            elif intent == IntentCategory.TRANSLATION_CONFIRMATION:
                original = entities.get('original', 'phrase')
                translation = entities.get('translation', 'translation')
                return cue_template.format(original=original, translation=translation)
            
            # For other intents, just return the template as is
            else:
                return cue_template
                
        except KeyError as e:
            logger.warning(f"Failed to format learning cue: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating learning cue: {e}")
            return None
    
    def _format_suggested_actions(self, actions: List[str]) -> str:
        """
        Format a list of suggested actions for the player.
        
        Args:
            actions: List of suggested actions
            
        Returns:
            Formatted string with suggested actions
        """
        # Get the formality level
        formality = float(self.personality.get("formality", 0.3))
        
        # Different headers based on formality
        if formality > 0.7:
            header = "I would suggest the following actions:"
        elif formality > 0.3:
            header = "Here are some things you could try:"
        else:
            header = "Try these:"
        
        # Format each action as a bullet point
        action_items = [f"• {action}" for action in actions]
        
        # Combine header and actions
        return header + "\n" + "\n".join(action_items)

    def _get_emotion_expression(self, emotion: str) -> str:
        """
        Get an emotion expression based on the provided emotion.
        
        Args:
            emotion: The emotion to get an expression for
            
        Returns:
            A randomly chosen emotion expression
        """
        if emotion in self.EMOTION_EXPRESSIONS:
            return random.choice(self.EMOTION_EXPRESSIONS[emotion])
        else:
            return random.choice(self.EMOTION_EXPRESSIONS["neutral"])

    def _get_playful_ending(self) -> str:
        """
        Get a playful ending based on the current personality.
        
        Returns:
            A randomly chosen playful ending
        """
        # Get the playfulness level
        playfulness = float(self.personality.get("playfulness", 0.6))
        
        # Choose a random playful phrase
        playful_phrases = [
            "I'm having so much fun!",
            "Isn't this fun?",
            "I love being with you!",
            "I'm really enjoying this!",
            "This is so much fun!"
        ]
        
        return random.choice(playful_phrases)

def format_response(response: str, request: ClassifiedRequest) -> str:
    """
    Format a response based on the request.
    
    Args:
        response: The raw response to format
        request: The request that generated the response
        
    Returns:
        The formatted response
    """
    if not response:
        return ""
        
    # Basic cleaning
    formatted = response.strip()
    
    # Add any game-specific formatting here based on processing_tier
    
    return formatted 