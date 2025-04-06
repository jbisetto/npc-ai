"""
Prompt template loader module.

This module handles loading and managing prompt templates for different processing tiers.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

from src.ai.npc.core.models import ProcessingTier

logger = logging.getLogger(__name__)

class PromptTemplateLoader:
    """Loads and manages prompt templates for different processing tiers."""
    
    def __init__(self, template_dir: str):
        """
        Initialize the prompt template loader.
        
        Args:
            template_dir: Directory containing prompt template files
        """
        self.template_dir = template_dir
        self.templates: Dict[str, Dict[str, Any]] = {}
        self._load_templates()
        
    def _load_templates(self) -> None:
        """Load all prompt templates from the template directory."""
        if not os.path.exists(self.template_dir):
            logger.warning(f"Template directory not found: {self.template_dir}")
            return
            
        for filename in os.listdir(self.template_dir):
            if not filename.endswith('.json'):
                continue
                
            template_path = os.path.join(self.template_dir, filename)
            try:
                with open(template_path, 'r') as f:
                    self.templates[filename[:-5]] = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load template {filename}: {e}")
                
    def get_processing_tier_prompt(self, tier: ProcessingTier, profile_id: Optional[str] = None) -> str:
        """
        Get the prompt template for a specific processing tier.
        
        Args:
            tier: The processing tier to get the prompt for
            profile_id: Optional profile ID to get profile-specific prompts
            
        Returns:
            The prompt template string
        """
        template_key = f"{tier.value}"
        if profile_id:
            template_key = f"{template_key}_{profile_id}"
            
        template = self.templates.get(template_key)
        if not template:
            logger.warning(f"No template found for {template_key}")
            return ""
            
        return template.get("prompt", "") 