"""
Multi-turn Conversation Management for Tier 3 processing.

This module provides functionality for managing multi-turn conversations,
including detecting conversation state, generating contextual prompts,
and handling follow-up questions and clarifications.
"""

import re
import logging
import enum
from typing import Optional, List, Dict, Any

from src.ai.npc.core.models import ClassifiedRequest
from src.ai.npc.core.context_manager import (
    ConversationContext,
    ContextManager
)

logger = logging.getLogger(__name__)


class ConversationState(enum.Enum):
    """
    Enum representing the state of a conversation.
    """
    NEW_TOPIC = "new_topic"
    FOLLOW_UP = "follow_up"
    CLARIFICATION = "clarification"


class ConversationManager:
    """
    Manager for multi-turn conversations.
    
    This class provides methods for detecting the state of a conversation,
    generating contextual prompts, and handling different types of
    conversation flows.
    """
    
    def __init__(self):
        """Initialize the conversation manager."""
        # Patterns for detecting follow-up questions
        self.follow_up_patterns = [
            r"what does .+ mean in that",
            r"can you explain .+ in that",
            r"what is .+ in that",
            r"how do you say .+ in that",
            r"what about .+",
            r"how about .+",
            r"tell me more about .+",
            r"what is the difference between .+",
            r"could you elaborate on .+"
        ]
        
        # Patterns for detecting clarification requests
        self.clarification_patterns = [
            r"can you explain that again",
            r"i don't understand",
            r"what do you mean",
            r"could you clarify",
            r"please explain again",
            r"i'm confused",
            r"that doesn't make sense",
            r"can you repeat that",
            r"what was that again"
        ]
    
    def detect_conversation_state(
        self,
        request: ClassifiedRequest,
        context: ConversationContext
    ) -> ConversationState:
        """
        Detect the state of a conversation based on the current request and context.
        
        Args:
            request: The current request
            context: The conversation context
            
        Returns:
            The detected conversation state
        """
        # If there are no previous entries, it's a new topic
        if not context.entries:
            return ConversationState.NEW_TOPIC
        
        # Get the player's input in lowercase for pattern matching
        player_input = request.player_input.lower()
        
        # Check for clarification patterns
        for pattern in self.clarification_patterns:
            if re.search(pattern, player_input):
                logger.debug(f"Detected clarification request: {player_input}")
                return ConversationState.CLARIFICATION
        
        # Check for follow-up patterns
        for pattern in self.follow_up_patterns:
            if re.search(pattern, player_input):
                logger.debug(f"Detected follow-up question: {player_input}")
                return ConversationState.FOLLOW_UP
        
        # Check for references to previous responses
        for entry in context.entries:
            # Split the response into words and check if any word appears in the current input
            response_words = set(entry.response.lower().split())
            input_words = set(player_input.split())
            if len(response_words.intersection(input_words)) > 2:  # If more than 2 words overlap
                logger.debug(f"Detected reference to previous response")
                return ConversationState.FOLLOW_UP
        
        # Default to new topic
        return ConversationState.NEW_TOPIC
    
    def generate_contextual_prompt(
        self,
        request: ClassifiedRequest,
        context: ConversationContext,
        state: ConversationState
    ) -> str:
        """
        Generate a contextual prompt based on the conversation history and state.
        
        Args:
            request: The current request
            context: The conversation context
            state: The detected conversation state
            
        Returns:
            A prompt that includes relevant context
        """
        # Get recent entries
        recent_entries = context.get_recent_entries(5)
        
        # Build the prompt
        prompt = "You are a helpful companion in a Japanese language learning game.\n\n"
        
        # Add conversation history
        if recent_entries:
            prompt += "Here are the previous exchanges:\n\n"
            for i, entry in enumerate(reversed(recent_entries)):
                prompt += f"Player: {entry.request}\n"
                prompt += f"Companion: {entry.response}\n\n"
        
        # Add specific instructions based on the conversation state
        if state == ConversationState.FOLLOW_UP:
            prompt += "The player is asking a follow-up question related to the previous exchanges.\n"
            prompt += "Please provide a response that takes into account the conversation history.\n\n"
        elif state == ConversationState.CLARIFICATION:
            prompt += "The player is asking for clarification about something in the previous exchanges.\n"
            prompt += "Please provide a more detailed explanation of the most recent topic.\n\n"
        else:  # NEW_TOPIC
            prompt += "The player is asking about a new topic.\n"
            prompt += "Please provide a response to their question.\n\n"
        
        # Add the current request
        prompt += f"Player: {request.player_input}\n"
        prompt += "Companion: "
        
        return prompt
    
    def handle_follow_up_question(
        self,
        request: ClassifiedRequest,
        context_manager: ContextManager,
        bedrock_client
    ) -> str:
        """
        Handle a follow-up question.
        
        Args:
            request: The current request
            context_manager: The context manager
            bedrock_client: The Bedrock client for generating responses
            
        Returns:
            The response to the follow-up question
        """
        # Get the conversation context
        context = context_manager.get_context(request.additional_params.get("conversation_id"))
        if not context:
            logger.warning("No context found for follow-up question")
            return "I'm sorry, I don't have enough context to answer that question."
        
        # Generate a contextual prompt
        prompt = self.generate_contextual_prompt(
            request,
            context,
            ConversationState.FOLLOW_UP
        )
        
        # Generate a response using the Bedrock client
        response = bedrock_client.generate_text(prompt)
        
        logger.debug(f"Generated response to follow-up question: {response}")
        return response
    
    def handle_clarification(
        self,
        request: ClassifiedRequest,
        context_manager: ContextManager,
        bedrock_client
    ) -> str:
        """
        Handle a clarification request.
        
        Args:
            request: The current request
            context_manager: The context manager
            bedrock_client: The Bedrock client for generating responses
            
        Returns:
            The response to the clarification request
        """
        # Get the conversation context
        context = context_manager.get_context(request.additional_params.get("conversation_id"))
        if not context:
            logger.warning("No context found for clarification request")
            return "I'm sorry, I don't have enough context to clarify."
        
        # Generate a contextual prompt
        prompt = self.generate_contextual_prompt(
            request,
            context,
            ConversationState.CLARIFICATION
        )
        
        # Generate a response using the Bedrock client
        response = bedrock_client.generate_text(prompt)
        
        logger.debug(f"Generated response to clarification request: {response}")
        return response
    
    def handle_new_topic(
        self,
        request: ClassifiedRequest,
        bedrock_client
    ) -> str:
        """
        Handle a new topic.
        
        Args:
            request: The current request
            bedrock_client: The Bedrock client for generating responses
            
        Returns:
            The response to the new topic
        """
        # Generate a simple prompt for the new topic
        prompt = f"You are a helpful companion in a Japanese language learning game.\n\n"
        prompt += f"Player: {request.player_input}\n"
        prompt += "Companion: "
        
        # Generate a response using the Bedrock client
        response = bedrock_client.generate_text(prompt)
        
        logger.debug(f"Generated response to new topic: {response}")
        return response
    
    def process(
        self,
        request: ClassifiedRequest,
        context_manager: ContextManager,
        bedrock_client
    ) -> str:
        """
        Process a request using multi-turn conversation management.
        
        Args:
            request: The current request
            context_manager: The context manager
            bedrock_client: The Bedrock client for generating responses
            
        Returns:
            The response to the request
        """
        # Get the conversation context
        context = context_manager.get_context(request.additional_params.get("conversation_id"))
        
        # If there's no context, handle it as a new topic
        if not context:
            logger.debug("No context found, handling as new topic")
            return self.handle_new_topic(request, bedrock_client)
        
        # Detect the conversation state
        state = self.detect_conversation_state(request, context)
        
        # Handle the request based on the conversation state
        if state == ConversationState.FOLLOW_UP:
            return self.handle_follow_up_question(request, context_manager, bedrock_client)
        elif state == ConversationState.CLARIFICATION:
            return self.handle_clarification(request, context_manager, bedrock_client)
        else:  # NEW_TOPIC
            return self.handle_new_topic(request, bedrock_client) 