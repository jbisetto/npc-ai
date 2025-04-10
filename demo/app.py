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

# Set module-specific logging levels
logging.getLogger('src.ai.npc.core').setLevel(logging.DEBUG)
logging.getLogger('src.ai.npc.local').setLevel(logging.DEBUG)
logging.getLogger('src.ai.npc').setLevel(logging.DEBUG)

# Import from src
from src.ai.npc import process_request
from src.ai.npc.core.models import NPCRequest, GameContext, ProcessingTier

# Define preset player IDs
preset_player_ids = [
    "player_1", 
    "player_2", 
    "visitor_jp", 
    "tourist_en", 
    "Custom..."
]

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

# Store conversation IDs for user sessions
# Key: player_id -> NPC -> conversation_id mappings
conversation_sessions = {}

# Simple processing function
async def process_message(message, selected_npc, player_id, session_id=None):
    """
    Process a user message through the AI components.
    
    Args:
        message: The user's message
        selected_npc: The selected NPC to interact with
        player_id: The ID of the player/user
        session_id: Optional session identifier for tracking conversations
        
    Returns:
        response_text: The AI's response
        processing_tier: Which tier processed the request
        raw_request: Raw request JSON (for Tier2/3)
        raw_response: Raw response JSON (for Tier2/3)
        prompt: The actual prompt sent to the AI model (for Tier2/3)
    """
    if not message.strip():
        return "Please enter a message.", "", "", "", ""
    
    # If no session_id provided, generate one
    if not session_id:
        session_id = str(uuid.uuid4())
        
    logger.info(f"Processing message for Player: {player_id}, NPC: {selected_npc}, Session: {session_id}")
    
    # Create or retrieve conversation ID for this player-NPC pair
    if player_id not in conversation_sessions:
        conversation_sessions[player_id] = {}
        
    if selected_npc not in conversation_sessions[player_id]:
        # First conversation with this NPC, create a new conversation ID
        conversation_sessions[player_id][selected_npc] = str(uuid.uuid4())
        
    # Get the conversation ID for this player-NPC pair
    conversation_id = conversation_sessions[player_id][selected_npc]
    logger.debug(f"Using conversation_id: {conversation_id} for player {player_id}")
    
    # Create a unique request ID 
    request_id = str(uuid.uuid4())
    
    # Get NPC data
    npc_data = npc_profiles[selected_npc]
    
    # Create game context with NPC ID
    game_context = GameContext(
        player_id=player_id,
        language_proficiency={
            "en": 0.8,  # English proficiency
            "ja": 0.3   # Japanese proficiency
        },
        player_location="station",  # Generic location
        current_objective="Buy ticket to Odawara",
        npc_id=selected_npc  # Associate the NPC with the request
    )
    
    # Create a dictionary of additional parameters - we'll track this but it's not directly passed
    additional_params = {
        'conversation_id': conversation_id,
        'npc_role': npc_data.get('role', 'companion'),
        'npc_personality': npc_data.get('personality', 'helpful')
    }
    
    # Create request with all necessary fields
    request = NPCRequest(
        request_id=request_id,
        player_input=message,
        game_context=game_context,
        additional_params=additional_params
    )
    
    # Create a JSON representation of the request (for debugging display)
    request_dict = request.model_dump()
    raw_request_json = json.dumps(request_dict, indent=2)
    
    try:
        # Process using the AI components
        logger.info(f"Sending request to AI components")
        
        # Add more detailed logging before processing
        logger.debug(f"Request details: player_id={player_id}, conversation_id={conversation_id}")
        logger.debug(f"NPC data: {json.dumps(npc_data, indent=2)}")
        
        # Process the request with NPCRequest
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
        
        # Include conversation diagnostics in response
        if debug_info:
            history_count = debug_info.get('history_count', 0)
            knowledge_count = debug_info.get('knowledge_count', 0)
            logger.info(f"Conversation included {history_count} history entries and {knowledge_count} knowledge items")
            
            # Add debug information about prompt creation to the prompt display
            prompt_display = prompt
            if not prompt_display:
                prompt_display = "No prompt available in debug info."
            else:
                # Analyze the prompt to check for relevant sections
                sections = []
                if "Relevant information:" in prompt_display:
                    sections.append("✅ Knowledge context included")
                else:
                    sections.append("❌ No knowledge context found")
                
                if "Previous conversation:" in prompt_display:
                    sections.append("✅ Conversation history included")
                else:
                    sections.append("❌ No conversation history found")
                
                # Add section analysis as a header
                prompt_display = "\n".join(sections) + "\n\n" + prompt_display
            
            raw_prompt_display = prompt_display
        
        # Return debug information
        return response_text, processing_tier.value, raw_request_json, raw_response_json, raw_prompt_display
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return f"Error processing request: {str(e)}", "ERROR", raw_request_json, "{}", ""

# Create Gradio interface
def create_demo():
    """Create and configure the Gradio demo interface."""
    with gr.Blocks(title="Tokyo Train Station Adventure Demo", theme=gr.themes.Soft()) as demo:
        # Store the session ID for this Gradio instance
        session_id = str(uuid.uuid4())
        
        gr.Markdown(
            """
            # AI Demo
            
            Select a player ID and an NPC to talk to, then type your message in English, Japanese, or a mix of both!
            """
        )
        
        with gr.Row():
            # Player ID Selection
            player_id_dropdown = gr.Dropdown(
                choices=preset_player_ids,
                value="player_1",
                label="Select or Enter Player ID",
                allow_custom_value=True
            )
        
        with gr.Row():
            # NPC Selection
            npc_selector = gr.Dropdown(
                choices=list(npc_profiles.keys()),
                value="Hachi (Dog Companion)",
                label="Select NPC to interact with"
            )
        
        with gr.Column():
            # Display conversation info
            conversation_info = gr.Markdown(
                """Conversation ID: None (start a conversation to generate ID)"""
            )
            
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
        
        # Updated wrapper to handle player ID
        def process_wrapper(msg, npc, player_id):
            if not msg.strip():
                return "Please enter a message.", "", {}, {}, ""
            
            # Handle "Custom..." selection
            if player_id == "Custom...":
                player_id = f"custom_player_{str(uuid.uuid4())[:8]}"
                
            # Update conversation info display text
            conv_info_text = "Starting new conversation..."
            if player_id in conversation_sessions and npc in conversation_sessions[player_id]:
                conv_id = conversation_sessions[player_id][npc]
                conv_info_text = f"**Conversation**: Player {player_id} talking to {npc}\n\n**Conversation ID**: {conv_id[:8]}..."
            
            # Pass the player ID when processing a message
            result = asyncio.run(process_message(msg, npc, player_id, session_id))
            
            # Parse the JSON strings into dictionaries for the JSON components
            try:
                request_json = json.loads(result[2]) if result[2] != "{}" else {}
                response_json = json.loads(result[3]) if result[3] != "{}" else {}
            except json.JSONDecodeError:
                request_json = {}
                response_json = {}
                
            # Ensure we're returning the prompt from debug_info
            prompt = result[4] if result[4] else ""
            
            # Check if conversation_id was created during processing
            if player_id in conversation_sessions and npc in conversation_sessions[player_id]:
                conv_id = conversation_sessions[player_id][npc]
                conv_info_text = f"**Conversation**: Player {player_id} talking to {npc}\n\n**Conversation ID**: {conv_id[:8]}..."
            
            # Return values including conversation info
            return result[0], result[1], request_json, response_json, prompt, conv_info_text
        
        def clear_fields():
            """Return empty values for all fields."""
            return "", "", {}, {}, "", "Conversation ID: None (start a conversation to generate ID)"
            
        # Make all handlers consistent by ensuring the number of outputs matches
        submit_outputs = [
            response_display, 
            tier_display, 
            raw_request_json, 
            raw_response_json, 
            raw_prompt_display,
            conversation_info
        ]
        
        submit_btn.click(
            fn=process_wrapper,
            inputs=[message_input, npc_selector, player_id_dropdown],
            outputs=submit_outputs
        )
        
        message_input.submit(
            fn=process_wrapper,
            inputs=[message_input, npc_selector, player_id_dropdown],
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