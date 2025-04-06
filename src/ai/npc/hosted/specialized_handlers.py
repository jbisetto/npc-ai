"""
Specialized handlers for complex scenarios in Tier 3.

These handlers are designed to process specific types of complex requests
that require specialized prompt engineering and response processing.
"""

import abc
import logging
from typing import Dict, Optional, Any, List, Type

from src.ai.npc.core.models import (
    ClassifiedRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)
from src.ai.npc.hosted.bedrock_client import BedrockClient
from src.ai.npc.hosted.context_manager import ConversationContext
from src.ai.npc.config import get_config

logger = logging.getLogger(__name__)


class SpecializedHandler(abc.ABC):
    """
    Abstract base class for specialized handlers.
    
    Specialized handlers are responsible for handling specific types of complex
    requests that require specialized prompt engineering and response processing.
    """
    
    def __init__(self, bedrock_client: Optional[BedrockClient] = None):
        """
        Initialize the specialized handler.
        
        Args:
            bedrock_client: The Bedrock client to use for generating responses.
                If not provided, a new client will be created when needed.
        """
        self.bedrock_client = bedrock_client or BedrockClient()
    
    @abc.abstractmethod
    def can_handle(self, intent: IntentCategory) -> bool:
        """
        Check if this handler can handle the given intent.
        
        Args:
            intent: The intent to check.
            
        Returns:
            True if this handler can handle the intent, False otherwise.
        """
        pass
    
    @abc.abstractmethod
    def create_prompt(self, request: ClassifiedRequest) -> str:
        """
        Create a prompt for the given request.
        
        Args:
            request: The request to create a prompt for.
            
        Returns:
            The prompt to send to the LLM.
        """
        pass
    
    def process_response(self, response: str, request: ClassifiedRequest) -> str:
        """
        Process the response from the LLM.
        
        Args:
            response: The raw response from the LLM.
            request: The original request.
            
        Returns:
            The processed response to send to the player.
        """
        # By default, just return the response as-is
        return response.strip()
    
    async def handle_request(self, request: ClassifiedRequest) -> str:
        """
        Handle the request by creating a prompt and generating a response.
        
        Args:
            request: The request to handle.
            
        Returns:
            The response to send to the player.
        """
        prompt = self.create_prompt(request)
        
        logger.debug(f"Sending prompt to Bedrock: {prompt[:100]}...")
        
        # Get configuration from companion.yaml
        tier3_config = get_config('tier3', {})
        bedrock_config = tier3_config.get('bedrock', {})
        
        response = await self.bedrock_client.generate(
            prompt=prompt,
            max_tokens=bedrock_config.get("max_tokens", 1000),
            temperature=bedrock_config.get("temperature", 0.7),
            model_id=bedrock_config.get("default_model", "anthropic.claude-3-sonnet-20240229-v1:0")
        )
        
        return self.process_response(response, request)
    
    def handle(self, request: ClassifiedRequest, context: ConversationContext, bedrock_client: BedrockClient) -> str:
        """
        Synchronous version of handle_request for use with scenario detection.
        
        Args:
            request: The request to handle.
            context: The conversation context.
            bedrock_client: The Bedrock client to use for generating responses.
            
        Returns:
            The response to send to the player.
        """
        prompt = self._create_scenario_prompt(request, context)
        
        logger.debug(f"Sending prompt to Bedrock: {prompt[:100]}...")
        
        response = bedrock_client.generate_text(
            prompt=prompt,
            max_tokens=1000
        )
        
        return self.process_response(response, request)
    
    def _create_scenario_prompt(self, request: ClassifiedRequest, context: ConversationContext) -> str:
        """
        Create a prompt for the given request and context.
        
        Args:
            request: The request to create a prompt for.
            context: The conversation context.
            
        Returns:
            The prompt to send to the LLM.
        """
        # Default implementation - can be overridden by subclasses
        prompt = f"""You are Yuki, a friendly AI companion in the Tokyo Train Station Adventure game.
The player has asked: "{request.player_input}"

Player's language level: {context.player_language_level}
Current location: {context.current_location}

Recent conversation:
"""
        
        # Add recent conversation context
        for entry in context.entries[-3:]:
            prompt += f"Player: {entry.request}\n"
            prompt += f"Yuki: {entry.response}\n\n"
        
        prompt += "Provide a helpful, friendly response that addresses the player's request."
        
        return prompt


class DefaultHandler(SpecializedHandler):
    """
    Default handler for requests that don't have a specialized handler.
    
    This handler uses a generic prompt template and minimal response processing.
    """
    
    def can_handle(self, intent: IntentCategory) -> bool:
        """
        Check if this handler can handle the given intent.
        
        The default handler can handle any intent.
        
        Args:
            intent: The intent to check.
            
        Returns:
            True, always.
        """
        return True
    
    def create_prompt(self, request: ClassifiedRequest) -> str:
        """
        Create a prompt for the given request.
        
        Args:
            request: The request to create a prompt for.
            
        Returns:
            The prompt to send to the LLM.
        """
        prompt = f"""
        You are a helpful AI companion in the Tokyo Train Station Adventure game.
        You are assisting a player who is learning Japanese while navigating Tokyo's train system.
        
        The player has asked: "{request.player_input}"
        
        Please provide a helpful, concise response that:
        1. Directly addresses their question
        2. Uses simple language appropriate for a language learner
        3. Includes relevant Japanese phrases with romaji pronunciation
        4. Keeps cultural context in mind
        5. Is friendly and encouraging
        
        Your response:
        """
        
        return prompt.strip()


class TicketPurchaseHandler(SpecializedHandler):
    """
    Handler for ticket purchase scenarios.
    
    This handler is responsible for helping players with purchasing tickets,
    understanding fare information, and navigating the ticket purchasing process.
    """
    
    def can_handle(self, intent: IntentCategory) -> bool:
        """Check if this handler can handle the given intent."""
        return intent == IntentCategory.GENERAL_HINT
    
    def create_prompt(self, request: ClassifiedRequest) -> str:
        """Create a prompt for the given request."""
        destination = request.extracted_entities.get("destination", "unknown location")
        
        prompt = f"""You are Yuki, a friendly AI companion in the Tokyo Train Station Adventure game.
The player is trying to purchase a ticket to {destination}.

Player's request: "{request.player_input}"

Provide a helpful response that:
1. Explains how to purchase a ticket to {destination}
2. Includes relevant Japanese phrases they can use
3. Mentions the approximate cost if known
4. Describes the ticket machines or counter process

Keep your response friendly, concise, and tailored to their language level.
"""
        return prompt
    
    def _create_scenario_prompt(self, request: ClassifiedRequest, context: ConversationContext) -> str:
        """Create a specialized prompt for ticket purchase scenarios."""
        destination = request.extracted_entities.get("destination", "unknown location")
        
        prompt = f"""You are Yuki, a friendly AI companion in the Tokyo Train Station Adventure game.
The player is trying to purchase a ticket to {destination}.

Player's language level: {context.player_language_level}
Current location: {context.current_location}

Recent conversation:
"""
        
        # Add recent conversation context
        for entry in context.entries[-3:]:
            prompt += f"Player: {entry.request}\n"
            prompt += f"Yuki: {entry.response}\n\n"
        
        prompt += f"""Player: {request.player_input}

Provide a helpful response that:
1. Explains how to purchase a ticket to {destination}
2. Includes relevant Japanese phrases they can use (with both Japanese script and romaji)
3. Mentions the approximate cost if known
4. Describes the ticket machines or counter process

Keep your response friendly, concise, and tailored to their language level ({context.player_language_level}).
"""
        return prompt


class NavigationHandler(SpecializedHandler):
    """
    Handler for navigation scenarios.
    
    This handler is responsible for helping players navigate the train station,
    find specific locations, and understand directions.
    """
    
    def can_handle(self, intent: IntentCategory) -> bool:
        """Check if this handler can handle the given intent."""
        return intent == IntentCategory.DIRECTION_GUIDANCE
    
    def create_prompt(self, request: ClassifiedRequest) -> str:
        """Create a prompt for the given request."""
        location = request.extracted_entities.get("location", "unknown location")
        
        prompt = f"""You are Yuki, a friendly AI companion in the Tokyo Train Station Adventure game.
The player is trying to navigate to {location}.

Player's request: "{request.player_input}"

Provide a helpful response that:
1. Gives clear directions to {location}
2. Includes relevant Japanese phrases they might see or hear
3. Mentions any landmarks or signs to look for
4. Estimates the walking time if applicable

Keep your response friendly, concise, and easy to follow.
"""
        return prompt
    
    def _create_scenario_prompt(self, request: ClassifiedRequest, context: ConversationContext) -> str:
        """Create a specialized prompt for navigation scenarios."""
        location = request.extracted_entities.get("location", "unknown location")
        
        prompt = f"""You are Yuki, a friendly AI companion in the Tokyo Train Station Adventure game.
The player is trying to navigate to {location}.

Player's language level: {context.player_language_level}
Current location: {context.current_location}

Recent conversation:
"""
        
        # Add recent conversation context
        for entry in context.entries[-3:]:
            prompt += f"Player: {entry.request}\n"
            prompt += f"Yuki: {entry.response}\n\n"
        
        prompt += f"""Player: {request.player_input}

Provide a helpful response that:
1. Gives clear directions from {context.current_location} to {location}
2. Includes relevant Japanese phrases they might see or hear (with both Japanese script and romaji)
3. Mentions any landmarks or signs to look for
4. Estimates the walking time if applicable

Keep your response friendly, concise, and tailored to their language level ({context.player_language_level}).
"""
        return prompt


class VocabularyHelpHandler(SpecializedHandler):
    """
    Handler for vocabulary help scenarios.
    
    This handler is responsible for helping players understand Japanese vocabulary,
    providing translations, explanations, and examples.
    """
    
    def can_handle(self, intent: IntentCategory) -> bool:
        """Check if this handler can handle the given intent."""
        return intent == IntentCategory.VOCABULARY_HELP
    
    def create_prompt(self, request: ClassifiedRequest) -> str:
        """Create a prompt for the given request."""
        word = request.extracted_entities.get("word", "unknown word")
        
        prompt = f"""You are Yuki, a friendly AI companion in the Tokyo Train Station Adventure game.
The player is asking about the Japanese word "{word}".

Player's request: "{request.player_input}"

Provide a helpful response that:
1. Explains the meaning of "{word}" in English
2. Shows how to write it in Japanese (if not already provided)
3. Provides the pronunciation (romaji)
4. Gives 1-2 example sentences using the word
5. Mentions any relevant cultural context if applicable

Keep your response friendly, educational, and concise.
"""
        return prompt
    
    def _create_scenario_prompt(self, request: ClassifiedRequest, context: ConversationContext) -> str:
        """Create a specialized prompt for vocabulary help scenarios."""
        word = request.extracted_entities.get("word", "unknown word")
        
        prompt = f"""You are Yuki, a friendly AI companion in the Tokyo Train Station Adventure game.
The player is asking about the Japanese word "{word}".

Player's language level: {context.player_language_level}
Current location: {context.current_location}

Recent conversation:
"""
        
        # Add recent conversation context
        for entry in context.entries[-3:]:
            prompt += f"Player: {entry.request}\n"
            prompt += f"Yuki: {entry.response}\n\n"
        
        prompt += f"""Player: {request.player_input}

Provide a helpful response that:
1. Explains the meaning of "{word}" in English
2. Shows how to write it in Japanese (if not already provided)
3. Provides the pronunciation (romaji)
4. Gives 1-2 example sentences using the word
5. Mentions any relevant cultural context if applicable

Adjust your explanation to their language level ({context.player_language_level}). Keep your response friendly, educational, and concise.
"""
        return prompt


class GrammarExplanationHandler(SpecializedHandler):
    """
    Handler for grammar explanation scenarios.
    
    This handler is responsible for helping players understand Japanese grammar,
    providing explanations, examples, and practice opportunities.
    """
    
    def can_handle(self, intent: IntentCategory) -> bool:
        """Check if this handler can handle the given intent."""
        return intent == IntentCategory.GRAMMAR_EXPLANATION
    
    def create_prompt(self, request: ClassifiedRequest) -> str:
        """Create a prompt for the given request."""
        grammar_point = request.extracted_entities.get("grammar_point", "unknown grammar point")
        
        prompt = f"""You are Yuki, a friendly AI companion in the Tokyo Train Station Adventure game.
The player is asking about the Japanese grammar point "{grammar_point}".

Player's request: "{request.player_input}"

Provide a helpful response that:
1. Explains the grammar point clearly at JLPT N5 level
2. Shows the structure with examples
3. Provides 2-3 example sentences using the grammar
4. Mentions any common mistakes or nuances
5. Relates it to the train station context if possible

Keep your response friendly, educational, and structured for easy understanding.
"""
        return prompt
    
    def _create_scenario_prompt(self, request: ClassifiedRequest, context: ConversationContext) -> str:
        """Create a specialized prompt for grammar explanation scenarios."""
        grammar_point = request.extracted_entities.get("grammar_point", "unknown grammar point")
        
        prompt = f"""You are Yuki, a friendly AI companion in the Tokyo Train Station Adventure game.
The player is asking about the Japanese grammar point "{grammar_point}".

Player's language level: {context.player_language_level}
Current location: {context.current_location}

Recent conversation:
"""
        
        # Add recent conversation context
        for entry in context.entries[-3:]:
            prompt += f"Player: {entry.request}\n"
            prompt += f"Yuki: {entry.response}\n\n"
        
        prompt += f"""Player: {request.player_input}

Provide a helpful response that:
1. Explains the grammar point clearly
2. Shows the structure with examples
3. Provides 2-3 example sentences using the grammar (with both Japanese script and romaji)
4. Mentions any common mistakes or nuances
5. Relates it to the train station context if possible

Adjust your explanation to their language level ({context.player_language_level}). Keep your response friendly, educational, and structured for easy understanding.
"""
        return prompt


class CulturalInformationHandler(SpecializedHandler):
    """
    Handler for cultural information scenarios.
    
    This handler is responsible for helping players understand Japanese culture,
    customs, etiquette, and traditions, particularly as they relate to train
    stations and public transportation.
    """
    
    def can_handle(self, intent: IntentCategory) -> bool:
        """Check if this handler can handle the given intent."""
        return intent == IntentCategory.GENERAL_HINT
    
    def create_prompt(self, request: ClassifiedRequest) -> str:
        """Create a prompt for the given request."""
        topic = request.extracted_entities.get("topic", "unknown cultural topic")
        
        prompt = f"""You are Yuki, a friendly AI companion in the Tokyo Train Station Adventure game.
The player is asking about Japanese cultural topic: "{topic}".

Player's request: "{request.player_input}"

Provide a helpful response that:
1. Explains the cultural aspect clearly and accurately
2. Provides historical context if relevant
3. Describes current practices and expectations
4. Offers practical advice for the player as a visitor
5. Includes any relevant Japanese terms (with translations)

Keep your response friendly, informative, and respectful of Japanese culture.
"""
        return prompt
    
    def _create_scenario_prompt(self, request: ClassifiedRequest, context: ConversationContext) -> str:
        """Create a specialized prompt for cultural information scenarios."""
        topic = request.extracted_entities.get("topic", "unknown cultural topic")
        
        prompt = f"""You are Yuki, a friendly AI companion in the Tokyo Train Station Adventure game.
The player is asking about Japanese cultural topic: "{topic}".

Player's language level: {context.player_language_level}
Current location: {context.current_location}

Recent conversation:
"""
        
        # Add recent conversation context
        for entry in context.entries[-3:]:
            prompt += f"Player: {entry.request}\n"
            prompt += f"Yuki: {entry.response}\n\n"
        
        prompt += f"""Player: {request.player_input}

Provide a helpful response that:
1. Explains the cultural aspect clearly and accurately
2. Provides historical context if relevant
3. Describes current practices and expectations
4. Offers practical advice for the player as a visitor
5. Includes any relevant Japanese terms (with translations and romaji)

Adjust your explanation to their language level ({context.player_language_level}). Keep your response friendly, informative, and respectful of Japanese culture.
"""
        return prompt


class TranslationHandler(SpecializedHandler):
    """
    Specialized handler for translation requests.
    
    This handler uses specialized prompts for translating between
    English and Japanese with detailed explanations.
    """
    
    def can_handle(self, intent: IntentCategory) -> bool:
        """
        Check if this handler can handle the given intent.
        
        Args:
            intent: The intent to check.
            
        Returns:
            True if this handler can handle the intent, False otherwise.
        """
        return intent == IntentCategory.TRANSLATION_CONFIRMATION
    
    def create_prompt(self, request: ClassifiedRequest) -> str:
        """
        Create a prompt for the given request.
        
        Args:
            request: The request to create a prompt for.
            
        Returns:
            The prompt to send to the LLM.
        """
        # Extract relevant entities if available
        destination = request.extracted_entities.get("destination", "")
        ticket_type = request.extracted_entities.get("ticket_type", "")
        
        prompt = f"""
        You are a Japanese language assistant in the Tokyo Train Station Adventure game.
        You specialize in providing accurate translations with helpful explanations.
        
        The player has asked for a translation: "{request.player_input}"
        
        Relevant details:
        - Destination: {destination}
        - Ticket type: {ticket_type}
        
        Please provide a response that:
        1. Gives the Japanese translation at JLPT N5 level
        2. Includes both Japanese script and romaji pronunciation
        3. Breaks down the translation with word-by-word explanations
        4. Provides cultural context if relevant
        5. Is formatted clearly with the translation highlighted
        
        Your translation and explanation:
        """
        
        return prompt.strip()
    
    def process_response(self, response: str, request: ClassifiedRequest) -> str:
        """
        Process the response from the LLM.
        
        Args:
            response: The raw response from the LLM.
            request: The original request.
            
        Returns:
            The processed response to send to the player.
        """
        # For translations, we want to ensure the response includes
        # both Japanese script and romaji for all phrases
        
        processed = response.strip()
        
        # Add a practice suggestion if not present
        if "practice" not in processed.lower() and "try saying" not in processed.lower():
            processed += "\n\nTry saying this phrase a few times to practice your pronunciation!"
        
        return processed


class ConversationContextHandler(SpecializedHandler):
    """
    Specialized handler for requests with conversation context.
    
    This handler incorporates previous conversation history to maintain
    context across multiple turns of conversation.
    """
    
    def can_handle(self, intent: IntentCategory) -> bool:
        """
        Check if this handler can handle the given intent.
        
        This handler can handle any intent if conversation context is available.
        
        Args:
            intent: The intent to check.
            
        Returns:
            True if this handler can handle the intent, False otherwise.
        """
        # This handler can handle any intent, as it's focused on maintaining
        # conversation context rather than specific intents
        return True
    
    def create_prompt(self, request: ClassifiedRequest) -> str:
        """
        Create a prompt for the given request.
        
        Args:
            request: The request to create a prompt for.
            
        Returns:
            The prompt to send to the LLM.
        """
        # Extract conversation context if available
        conversation_context = request.additional_params.get("conversation_context", {})
        previous_exchanges = conversation_context.get("previous_exchanges", [])
        player_language_level = conversation_context.get("player_language_level", "N5")
        current_location = conversation_context.get("current_location", "unknown")
        
        # Build the conversation history part of the prompt
        conversation_history = ""
        if previous_exchanges:
            conversation_history = "Previous conversation:\n"
            for i, exchange in enumerate(previous_exchanges):
                conversation_history += f"Player: {exchange.get('request', '')}\n"
                conversation_history += f"You: {exchange.get('response', '')}\n\n"
        
        prompt = f"""
        You are a helpful AI companion in the Tokyo Train Station Adventure game.
        You are assisting a player who is learning Japanese while navigating Tokyo's train system.
        
        Player's current location: {current_location}
        Player's Japanese language level: {player_language_level}
        
        {conversation_history}
        
        The player's current question is: "{request.player_input}"
        
        Please provide a helpful response that:
        1. Maintains continuity with the previous conversation
        2. Directly addresses their current question
        3. Uses simple language appropriate for their level ({player_language_level})
        4. Includes relevant Japanese phrases with romaji pronunciation
        5. Is friendly and encouraging
        
        Your response:
        """
        
        return prompt.strip()
    
    def process_response(self, response: str, request: ClassifiedRequest) -> str:
        """
        Process the response from the LLM.
        
        Args:
            response: The raw response from the LLM.
            request: The original request.
            
        Returns:
            The processed response to send to the player.
        """
        # For conversation context, we want to ensure the response
        # maintains a consistent tone and style
        
        processed = response.strip()
        
        return processed


class SpecializedHandlerRegistry:
    """
    Registry for specialized handlers.
    
    This class maintains a mapping of intent categories to specialized handlers
    and provides methods for registering and retrieving handlers.
    """
    
    def __init__(self):
        """Initialize the registry with an empty handler map."""
        self._handlers: Dict[IntentCategory, SpecializedHandler] = {}
        self._default_handler = DefaultHandler()
    
    def register_handler(self, intent: IntentCategory, handler: SpecializedHandler) -> None:
        """
        Register a handler for the given intent.
        
        Args:
            intent: The intent to register the handler for.
            handler: The handler to register.
        """
        self._handlers[intent] = handler
    
    def get_handler(self, intent: IntentCategory) -> SpecializedHandler:
        """
        Get the handler for the given intent.
        
        If no handler is registered for the intent, returns the default handler.
        
        Args:
            intent: The intent to get a handler for.
            
        Returns:
            The handler for the intent, or the default handler if none is registered.
        """
        return self._handlers.get(intent, self._default_handler)
    
    def initialize_default_handlers(self) -> None:
        """
        Initialize the registry with default handlers for common intents.
        """
        self.register_handler(IntentCategory.GRAMMAR_EXPLANATION, GrammarExplanationHandler())
        self.register_handler(IntentCategory.TRANSLATION_CONFIRMATION, TranslationHandler())
        
        # Add more default handlers as needed 