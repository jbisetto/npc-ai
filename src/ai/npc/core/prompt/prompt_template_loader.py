"""
Prompt Template Loader

This module provides a loader for prompt templates from JSON files,
supporting intent-specific prompts and profile-specific instructions.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

from src.ai.npc.core.models import IntentCategory

logger = logging.getLogger(__name__)


class PromptTemplateLoader:
    """
    Loads and manages prompt templates from JSON files.
    
    This class handles loading prompt templates, retrieving intent-specific
    prompts, and applying profile-specific instructions.
    """
    
    def __init__(self, templates_directory: str):
        """
        Initialize the prompt template loader.
        
        Args:
            templates_directory: Path to directory containing template JSON files
        """
        self.templates_directory = templates_directory
        self.templates = {}  # Stores loaded templates
        self.active_template_id = "default_prompts"  # Default template ID
        
        # Load all templates
        self._load_all_templates()
        
        logger.debug(f"Loaded {len(self.templates)} prompt templates")
    
    def _load_all_templates(self):
        """
        Load all template files from the templates directory.
        """
        if not os.path.exists(self.templates_directory):
            logger.warning(f"Templates directory not found: {self.templates_directory}")
            return
        
        for filename in os.listdir(self.templates_directory):
            if filename.endswith(".json"):
                filepath = os.path.join(self.templates_directory, filename)
                self._load_template(filepath)
    
    def _load_template(self, file_path: str):
        """
        Load a template from a JSON file.
        
        Args:
            file_path: Path to the template JSON file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
                template_id = template_data.get("template_id")
                
                if not template_id:
                    logger.warning(f"Template missing template_id: {file_path}")
                    return
                
                self.templates[template_id] = template_data
                logger.debug(f"Loaded template: {template_id}")
                
        except Exception as e:
            logger.error(f"Error loading template from {file_path}: {e}")
    
    def set_active_template(self, template_id: str):
        """
        Set the active template to use for prompt generation.
        
        Args:
            template_id: The ID of the template to use
        """
        if template_id not in self.templates:
            logger.warning(f"Template not found: {template_id}, using default")
            return
            
        self.active_template_id = template_id
        logger.debug(f"Set active template to: {template_id}")
    
    def get_intent_prompt(self, intent: IntentCategory, profile_id: Optional[str] = None) -> str:
        """
        Get a prompt for a specific intent and optional profile.
        
        Args:
            intent: The intent category to get a prompt for
            profile_id: Optional profile ID to get profile-specific instructions
            
        Returns:
            A prompt string for the intent, or empty string if not found
        """
        # Get the active template
        template = self.templates.get(self.active_template_id)
        if not template:
            logger.warning(f"Active template not found: {self.active_template_id}")
            return ""
        
        # Get prompts section
        intent_prompts = template.get("intent_prompts", {})
        
        # Get intent-specific prompt or default
        intent_name = intent.value.upper()
        prompt = intent_prompts.get(intent_name)
        
        if prompt is None:
            prompt = intent_prompts.get("DEFAULT", "")
        
        # Add response instructions if available
        response_instructions = template.get("response_instructions")
        if response_instructions:
            prompt = f"{prompt}\n\n{response_instructions}"
        
        # Add profile-specific instructions if available
        if profile_id:
            npc_specific = template.get("npc_specific_instructions", {})
            profile_instructions = npc_specific.get(profile_id)
            
            if profile_instructions:
                prompt = f"{prompt}\n\n{profile_instructions}"
        
        return prompt 