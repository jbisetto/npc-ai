#!/usr/bin/env python
"""
Demo app for testing NPC AI functionality.
"""

import gradio as gr
import uuid
import asyncio
import sys
import os
import logging
import json
import re
from pathlib import Path

# Add the src directory to the Python path
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Fix configuration path before importing modules
from src.ai.npc.config import set_config_path
set_config_path(os.path.join(parent_dir, "src", "config", "npc-config.yaml"))
logger.info(f"Set NPC config path to: {os.path.join(parent_dir, 'src', 'config', 'npc-config.yaml')}")

# Import from src
from src.ai.npc import process_companion_request
from src.ai.npc.core.models import CompanionRequest, GameContext, ClassifiedRequest
from src.ai.npc.core.models import ProcessingTier
from src.ai.npc.core.processor_framework import ProcessorFramework

# Setup monkey patch to capture prompts sent to AI models
# This is needed because the prompt generation happens deep inside the tier2/tier3 processors
CAPTURED_PROMPTS = {}

# Import and monkey patch the tier2 processor
from src.ai.npc.tier2.tier2_processor import Tier2Processor
original_generate_with_retries = Tier2Processor._generate_with_retries

async def patched_generate_with_retries(self, request, model, prompt):
    # Capture the prompt before sending it to the LLM
    global CAPTURED_PROMPTS
    CAPTURED_PROMPTS[request.request_id] = prompt
    # Call the original method
    return await original_generate_with_retries(self, request, model, prompt)

Tier2Processor._generate_with_retries = patched_generate_with_retries

# Try to import and monkey patch bedrock client (for tier3)
try:
    from src.ai.npc.hosted.bedrock_client import BedrockClient
    original_generate = BedrockClient.generate
    
    async def patched_generate(self, request=None, model_id=None, prompt=None, **kwargs):
        # Capture the prompt before sending it to Bedrock
        global CAPTURED_PROMPTS
        if request and hasattr(request, 'request_id'):
            CAPTURED_PROMPTS[request.request_id] = prompt
        # Call the original method
        return await original_generate(self, request=request, model_id=model_id, prompt=prompt, **kwargs)
    
    BedrockClient.generate = patched_generate
except ImportError:
    logger.warning("Could not import BedrockClient for monkey patching")

# Define NPC profiles
npc_profiles = {
    "Hachi (Dog Companion)": {
        "role": "companion",
        "personality": "helpful_bilingual_dog",
    },
    "Station Staff": {
        "role": "staff",
        "personality": "professional_helpful",
    },
    "Ticket Vendor": {
        "role": "vendor",
        "personality": "busy_efficient",
    },
    "Fellow Tourist": {
        "role": "tourist",
        "personality": "confused_friendly",
    }
}

# Simple processing function
async def process_message(message, selected_npc):
    """
    Process a user message through the AI components.
    
    Args:
        message: The user's message
        selected_npc: The selected NPC to interact with
        
    Returns:
        response_text: The AI's response
        processing_tier: Which tier processed the request
        raw_request: Raw request JSON (for Tier2/3)
        raw_response: Raw response JSON (for Tier2/3)
        prompt: The actual prompt sent to the AI model (for Tier2/3)
    """
    if not message.strip():
        return "Please enter a message.", "", "", "", ""
    
    logger.info(f"Processing message for NPC: {selected_npc}")
    
    # Create a unique request ID we can use to track prompts
    request_id = str(uuid.uuid4())
    
    # Get NPC data
    npc_data = npc_profiles[selected_npc]
    
    # Create minimal request
    request = CompanionRequest(
        request_id=request_id,
        player_input=message,
        request_type="text",
        game_context=GameContext(
            player_location="station",  # Generic location
            current_objective="Buy ticket to Odawara"
        ),
        additional_params={
            "npc_profile": npc_data,
            "session_id": "demo_session"
        }
    )
    
    # Create a JSON representation of the request (for debugging display)
    request_dict = {
        "request_id": request.request_id,
        "player_input": request.player_input,
        "request_type": request.request_type,
        "game_context": {
            "player_location": request.game_context.player_location,
            "current_objective": request.game_context.current_objective
        },
        "additional_params": request.additional_params
    }
    raw_request_json = json.dumps(request_dict, indent=2)
    
    try:
        # Process using the AI components
        logger.info(f"Sending request to AI components")
        response = await process_companion_request(request)
        
        logger.info(f"Response received - tier: {response.processing_tier.value}")
        
        # Create a JSON representation of the response (for debugging display)
        response_dict = {
            "request_id": response.request_id,
            "response_text": response.response_text,
            "intent": response.intent,
            "processing_tier": response.processing_tier,
            "suggested_actions": response.suggested_actions,
            "learning_cues": response.learning_cues,
            "confidence": response.confidence,
            "debug_info": response.debug_info
        }
        raw_response_json = json.dumps(response_dict, indent=2)
        
        # Get the captured prompt if available
        captured_prompt = CAPTURED_PROMPTS.get(request_id, "")
        
        # Only show raw request/response for Tier2 or Tier3
        if response.processing_tier in [ProcessingTier.TIER_2, ProcessingTier.TIER_3]:
            return response.response_text, response.processing_tier.value, raw_request_json, raw_response_json, captured_prompt
        else:
            return response.response_text, response.processing_tier.value, "{}", "{}", ""
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        # Handle any errors
        return f"Error processing request: {str(e)}", "ERROR", raw_request_json, "{}", ""

# Create Gradio interface
def create_demo():
    """Create and configure the Gradio demo interface."""
    with gr.Blocks(title="Tokyo Train Station Adventure Demo", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
            # AI Demo
            
            Select an NPC to talk to and type your message in English, Japanese, or a mix of both!
            """
        )
        
        with gr.Row():
            # NPC Selection
            npc_selector = gr.Dropdown(
                choices=list(npc_profiles.keys()),
                value="Hachi (Dog Companion)",
                label="Select NPC to interact with"
            )
        
        with gr.Column():
            # Input Box
            message_input = gr.Textbox(
                label="Your message (English, Japanese or mixed)",
                placeholder="Type your message here...",
                lines=2
            )
            
            with gr.Row():
                # Submit Button
                submit_btn = gr.Button("Send Message", variant="primary")
                # Clear Button
                clear_btn = gr.Button("Clear")
            
            # AI Response Display (positioned below input)
            response_display = gr.Textbox(
                label="AI Response",
                interactive=False,
                lines=5
            )
            
            # Processing tier display
            tier_display = gr.Textbox(
                label="Processing Tier Used",
                interactive=False
            )
            
            # Add collapsible sections for raw request/response data
            with gr.Accordion("Advanced: Debug Information (Tier2/Tier3 only)", open=False):
                # Show the actual prompt sent to the AI model in a separate tab
                with gr.Tabs():
                    with gr.TabItem("Raw Prompt"):
                        raw_prompt_display = gr.Textbox(
                            label="Actual Prompt Sent to AI (Tier2/Tier3)",
                            interactive=False,
                            lines=10
                        )
                        
                    with gr.TabItem("Request/Response Data"):
                        with gr.Row():
                            with gr.Column():
                                raw_request_json = gr.JSON(
                                    label="Raw Request (Tier2/Tier3)",
                                    value=None,
                                )
                            with gr.Column():
                                raw_response_json = gr.JSON(
                                    label="Raw Response (Tier2/Tier3)",
                                    value=None,
                                )
        
        # Connect components
        def process_wrapper(msg, npc):
            if not msg.strip():
                return "Please enter a message.", "", {}, {}, ""
            return asyncio.run(process_message(msg, npc))
        
        def clear_fields():
            # Return 6 values to match the number of components being updated
            # [message_input, response_display, tier_display, raw_request_json, raw_response_json, raw_prompt_display]
            return "", "", "", {}, {}, ""
        
        submit_btn.click(
            fn=process_wrapper,
            inputs=[message_input, npc_selector],
            outputs=[response_display, tier_display, raw_request_json, raw_response_json, raw_prompt_display]
        )
        
        message_input.submit(
            fn=process_wrapper,
            inputs=[message_input, npc_selector],
            outputs=[response_display, tier_display, raw_request_json, raw_response_json, raw_prompt_display]
        )
        
        clear_btn.click(
            fn=clear_fields,
            inputs=[],
            outputs=[message_input, response_display, tier_display, raw_request_json, raw_response_json, raw_prompt_display]
        )
        
    return demo

# Launch the demo
if __name__ == "__main__":
    try:
        logger.info("Starting Tokyo Train Station Adventure Demo")
        demo = create_demo()
        demo.launch(show_error=True)
    except Exception as e:
        logger.error(f"Error launching demo: {str(e)}", exc_info=True) 