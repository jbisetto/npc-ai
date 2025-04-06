"""
Processor Framework

This module defines the abstract base class for processors and the factory
for creating processor instances.
"""

import abc
import logging
from typing import Dict, Any, Optional

from src.ai.npc.core.models import (
    ClassifiedRequest,
    ProcessingTier,
    IntentCategory
)

logger = logging.getLogger(__name__)


class Processor(abc.ABC):
    """
    Abstract base class for processors.
    
    A processor is responsible for generating a response to a classified request.
    Different processors use different techniques, from rule-based responses to
    local language models to cloud-based language models.
    """
    
    @abc.abstractmethod
    async def process(self, request: ClassifiedRequest) -> str:
        """
        Process a request and generate a response.
        
        Args:
            request: The classified request to process
            
        Returns:
            The generated response
        """
        pass


class Tier1Processor(Processor):
    """
    Tier 1 processor for the companion AI system.
    
    This processor uses rule-based techniques to generate responses to simple
    requests. It is the most limited but also the most reliable and fastest
    processor in the tiered processing framework.
    """
    
    def __init__(self):
        """Initialize the Tier 1 processor."""
        self.logger = logging.getLogger(__name__)
        self.decision_trees = {}
        self._load_default_trees()
        self.logger.debug("Initialized Tier1Processor")
    
    async def process(self, request: ClassifiedRequest) -> str:
        """
        Process a request using rule-based techniques.
        
        Args:
            request: The classified request to process
            
        Returns:
            The generated response
        """
        self.logger.info(f"Processing request {request.request_id} with Tier 1 processor")
        
        # Create a companion request from the classified request
        companion_request = self._create_companion_request(request)
        
        # Determine which decision tree to use based on the intent
        tree_name = self._get_tree_name_for_intent(request.intent)
        
        # Get the decision tree
        tree = self.decision_trees.get(tree_name)
        
        if not tree:
            self.logger.warning(f"No decision tree found for intent {request.intent.value}")
            return "I'm sorry, I don't know how to help with that."
        
        # Traverse the decision tree to generate a response
        response = self._traverse_tree(tree, companion_request)
        
        self.logger.info(f"Generated response for request {request.request_id}")
        return response
    
    def _get_tree_name_for_intent(self, intent: IntentCategory) -> str:
        """
        Get the name of the decision tree to use for a given intent.
        
        Args:
            intent: The intent of the request
            
        Returns:
            The name of the decision tree to use
        """
        # Map intents to decision tree names
        intent_to_tree = {
            IntentCategory.VOCABULARY_HELP: "vocabulary",
            IntentCategory.GRAMMAR_EXPLANATION: "grammar",
            IntentCategory.DIRECTION_GUIDANCE: "directions",
            IntentCategory.TRANSLATION_CONFIRMATION: "translation",
            IntentCategory.GENERAL_HINT: "general"
        }
        
        return intent_to_tree.get(intent, "general")
    
    def _traverse_tree(self, tree: Dict[str, Any], request: Any) -> str:
        """
        Traverse a decision tree to generate a response.
        
        Args:
            tree: The decision tree to traverse
            request: The companion request
            
        Returns:
            The generated response
        """
        # This is a simplified implementation
        # In a real system, this would be more complex
        return tree.get("default_response", "I'm sorry, I don't know how to help with that.")
    
    def _create_companion_request(self, request: ClassifiedRequest) -> Any:
        """
        Create a companion request from a classified request.
        
        Args:
            request: The classified request
            
        Returns:
            A companion request
        """
        # This is a simplified implementation
        # In a real system, this would create a proper companion request object
        return {
            "request_id": request.request_id,
            "player_input": request.player_input,
            "request_type": request.request_type,
            "intent": request.intent.value,
            "complexity": request.complexity.value,
            "extracted_entities": request.extracted_entities
        }
    
    def _load_default_trees(self):
        """Load the default decision trees."""
        # This is a simplified implementation
        # In a real system, this would load decision trees from files
        self.decision_trees = {
            "vocabulary": {
                "default_response": "That word means 'hello' in Japanese. In Japanese: こんにちは (konnichiwa)."
            },
            "grammar": {
                "default_response": "This grammar point is used to express a desire to do something. For example: 食べたい (tabetai) means 'I want to eat'."
            },
            "directions": {
                "default_response": "The ticket gate is straight ahead. In Japanese: きっぷうりば は まっすぐ です (kippu-uriba wa massugu desu)."
            },
            "translation": {
                "default_response": "Yes, that's correct! 'Thank you' in Japanese is ありがとう (arigatou)."
            },
            "general": {
                "default_response": "I'm Hachiko, your companion in Tokyo Train Station. How can I help you learn Japanese today?"
            }
        }
    
    def _create_prompt(self, request: ClassifiedRequest) -> str:
        """
        Create a prompt for the request.
        
        Args:
            request: The classified request
            
        Returns:
            A prompt string
        """
        # This is a simplified implementation
        # In a real system, this would create a more sophisticated prompt
        return f"Player asked: {request.player_input}\nIntent: {request.intent.value}\nComplexity: {request.complexity.value}"


class ProcessorFactory:
    """
    Factory for creating processors based on the processing tier.
    Creates a single processor instance based on configuration.
    """
    
    _instance = None
    _processor = None
    _player_history_manager = None
    
    def __new__(cls, *args, **kwargs):
        """Create a singleton instance of the factory."""
        if cls._instance is None:
            cls._instance = super(ProcessorFactory, cls).__new__(cls)
            if 'player_history_manager' in kwargs:
                cls._player_history_manager = kwargs['player_history_manager']
        return cls._instance
    
    def __init__(self, player_history_manager=None):
        """
        Initialize the factory.
        
        Args:
            player_history_manager: Optional player history manager to pass to processors
        """
        if player_history_manager and not self.__class__._player_history_manager:
            self.__class__._player_history_manager = player_history_manager
    
    @classmethod
    def clear_cache(cls):
        """Clear the processor cache. Used primarily for testing."""
        cls._processor = None
    
    def get_processor(self, tier: ProcessingTier = None) -> Processor:
        """
        Get the appropriate processor based on configuration.
        If tier is specified, will try to get that specific tier.
        Otherwise will try HOSTED first, then fall back to LOCAL if HOSTED is disabled.
        
        Args:
            tier: Optional tier parameter to request a specific tier
            
        Returns:
            A processor instance
            
        Raises:
            ValueError: If no tiers are enabled in configuration or requested tier is disabled
        """
        # If we already have a processor and no specific tier is requested, return it
        if self._processor and tier is None:
            return self._processor
        
        # Import here to avoid circular imports
        from src.ai.npc.config import get_config
        
        local_config = get_config('local', {})
        hosted_config = get_config('hosted', {})
        
        # Check if any tier is enabled
        if not local_config.get('enabled', False) and not hosted_config.get('enabled', False):
            raise ValueError("No processor tiers are enabled in configuration")
        
        # If a specific tier is requested, try to get that tier
        if tier == ProcessingTier.LOCAL:
            if not local_config.get('enabled', False):
                raise ValueError("Local processing is disabled in configuration")
            from src.ai.npc.local.local_processor import LocalProcessor
            self._processor = LocalProcessor(self._player_history_manager)
            return self._processor
        elif tier == ProcessingTier.HOSTED:
            if not hosted_config.get('enabled', False):
                raise ValueError("Hosted processing is disabled in configuration")
            from src.ai.npc.hosted.hosted_processor import HostedProcessor
            self._processor = HostedProcessor(self._player_history_manager)
            return self._processor
        
        # No specific tier requested, try HOSTED first, then fall back to LOCAL
        if hosted_config.get('enabled', False):
            from src.ai.npc.hosted.hosted_processor import HostedProcessor
            self._processor = HostedProcessor(self._player_history_manager)
            return self._processor
        elif local_config.get('enabled', False):
            from src.ai.npc.local.local_processor import LocalProcessor
            self._processor = LocalProcessor(self._player_history_manager)
            return self._processor
        else:
            raise ValueError("No processor tiers are enabled in configuration")
        
        return self._processor