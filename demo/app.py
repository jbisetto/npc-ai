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
from pathlib import Path

# Add the src directory to the Python path
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import from src
from src.ai.npc import process_request
from src.ai.npc.core.models import CompanionRequest, GameContext, ClassifiedRequest
from src.ai.npc.core.models import ProcessingTier

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
    
    # Create a unique request ID
    request_id = str(uuid.uuid4())
    
    # Get NPC data
    npc_data = npc_profiles[selected_npc]
    
    # Create minimal request
    request = CompanionRequest(
        request_id=request_id,
        player_input=message,
        game_context=GameContext(
            player_id="demo_player",
            language_proficiency={
                "en": 0.8,  # English proficiency
                "ja": 0.3   # Japanese proficiency
            },
            player_location="station",  # Generic location
            current_objective="Buy ticket to Odawara"
        )
    )
    
    # Create a JSON representation of the request (for debugging display)
    request_dict = {
        "request_id": request.request_id,
        "player_input": request.player_input,
        "game_context": request.game_context.to_dict() if request.game_context else None
    }
    raw_request_json = json.dumps(request_dict, indent=2)
    
    try:
        # Process using the AI components
        logger.info(f"Sending request to AI components")
        response = await process_request(request)
        
        logger.info(f"Response received - tier: {response.get('processing_tier', 'unknown')}")
        
        # Extract response text and metadata
        response_text = response.get("response_text", "I apologize, but I couldn't process your request.")
        processing_tier = response.get("processing_tier", "unknown")
        suggested_actions = response.get("suggested_actions", [])
        learning_cues = response.get("learning_cues", {})
        emotion = response.get("emotion", "neutral")
        confidence = response.get("confidence", 0.0)
        debug_info = response.get("debug_info", {})
        response_thinking = response.get("response_thinking", None)
        prompt = debug_info.get("prompt", "")
        
        # Create a JSON representation of the response (for debugging display)
        response_dict = {
            "request_id": response.get("request_id", request_id),
            "response_text": response_text,
            "response_thinking": response_thinking,
            "intent": response.get("intent", "unknown"),
            "processing_tier": processing_tier.value if isinstance(processing_tier, ProcessingTier) else str(processing_tier),
            "suggested_actions": suggested_actions,
            "learning_cues": learning_cues,
            "confidence": confidence,
            "debug_info": debug_info
        }
        raw_response_json = json.dumps(response_dict, indent=2)
        
        # Return debug information
        return response_text, processing_tier.value, raw_request_json, raw_response_json, prompt
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
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
            
            # AI Response Display
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
            with gr.Accordion("Advanced: Debug Information", open=False):
                # Show the actual prompt sent to the AI model in a separate tab
                with gr.Tabs():
                    with gr.TabItem("Raw Prompt"):
                        raw_prompt_display = gr.Textbox(
                            label="Actual Prompt Sent to AI",
                            interactive=False,
                            lines=10
                        )
                        
                    with gr.TabItem("Request/Response Data"):
                        with gr.Row():
                            with gr.Column():
                                raw_request_json = gr.JSON(
                                    label="Raw Request",
                                    value=None,
                                )
                            with gr.Column():
                                raw_response_json = gr.JSON(
                                    label="Raw Response",
                                    value=None,
                                )
        
        # Connect components
        def process_wrapper(msg, npc):
            if not msg.strip():
                return "Please enter a message.", "", {}, {}, ""
            result = asyncio.run(process_message(msg, npc))
            # Parse the JSON strings into dictionaries for the JSON components
            try:
                request_json = json.loads(result[2]) if result[2] != "{}" else {}
                response_json = json.loads(result[3]) if result[3] != "{}" else {}
            except json.JSONDecodeError:
                request_json = {}
                response_json = {}
            # Ensure we're returning the prompt from debug_info
            prompt = result[4] if result[4] else ""
            return result[0], result[1], request_json, response_json, prompt
        
        def clear_fields():
            """Return empty values for all fields."""
            return "", "", "", {}, {}, ""
            
        # Make all handlers consistent by ensuring the number of outputs matches
        submit_outputs = [response_display, tier_display, raw_request_json, raw_response_json, raw_prompt_display]
        
        submit_btn.click(
            fn=process_wrapper,
            inputs=[message_input, npc_selector],
            outputs=submit_outputs
        )
        
        message_input.submit(
            fn=process_wrapper,
            inputs=[message_input, npc_selector],
            outputs=submit_outputs
        )
        
        clear_btn.click(
            fn=clear_fields,
            inputs=[],
            outputs=[message_input] + submit_outputs
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