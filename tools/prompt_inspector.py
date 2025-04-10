import gradio as gr
import os
import json
from pathlib import Path
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ai.npc.core.models import NPCRequest, GameContext, NPCProfileType
from src.ai.npc.core.prompt_manager import PromptManager
from src.ai.npc.core.profile.profile import NPCProfile
from src.ai.npc.core.profile.profile_loader import ProfileLoader

# Initialize components
profile_loader = ProfileLoader("src/data/profiles")
prompt_manager = PromptManager(max_prompt_tokens=800)

# Fixed player input for all tests
FIXED_PLAYER_INPUT = "Players actual input will be here."

def load_profiles():
    """Load profiles from the NPCProfileType enum and map them to display names."""
    profiles = {}
    
    # Get all profile enumeration values
    for profile_type in NPCProfileType:
        profile_id = profile_type.value
        
        # Try to get the actual profile data to extract the name and role
        profile_data = profile_loader.get_profile(profile_id)
        if profile_data:
            name = profile_data.get('name', 'Unknown')
            role = profile_data.get('role', 'Unknown')
            profiles[profile_id] = f"{name} ({role})"
        else:
            # Fallback if profile data not found
            profiles[profile_id] = f"{profile_id.replace('_', ' ').title()}"
    
    return profiles

def create_test_prompt(npc_id):
    """Create a test prompt for the selected NPC."""
    # Create game context with default values
    game_context = GameContext(
        player_id="test_player",
        language_proficiency={"JLPT": 5.0, "speaking": 0.5, "listening": 0.5},
        player_location="Tokyo Station",
        npc_id=npc_id
    )
    
    # Create request
    request = NPCRequest(
        request_id="test_request",
        player_input=FIXED_PLAYER_INPUT,
        game_context=game_context
    )
    
    # Load profile
    profile = profile_loader.get_profile(npc_id, as_object=True)
    
    # Generate prompt
    prompt = prompt_manager.create_prompt(
        request=request,
        profile=profile
    )
    
    return prompt

def gradio_interface(npc_id):
    """Interface for Gradio."""
    return create_test_prompt(npc_id)

# Load available profiles
available_profiles = load_profiles()

# Create Gradio interface
with gr.Blocks(title="NPC Prompt Inspector") as app:
    gr.Markdown("# NPC Prompt Inspector")
    gr.Markdown(f"Select an NPC to see what prompt would be generated for input: **{FIXED_PLAYER_INPUT}**")
    
    with gr.Row():
        with gr.Column():
            npc_selector = gr.Dropdown(
                choices=list(available_profiles.keys()),
                label="Select NPC",
                value=list(available_profiles.keys())[0] if available_profiles else None,
                info="Choose which NPC persona to use"
            )
            
            submit_btn = gr.Button("Generate Prompt")
        
        with gr.Column():
            output = gr.Textbox(
                label="Generated Prompt",
                lines=20
            )
            
            npc_info = gr.Markdown("## NPC Information")
            
    # Update NPC info when selection changes
    def update_npc_info(npc_id):
        if not npc_id:
            return "No NPC selected"
        
        profile = profile_loader.get_profile(npc_id)
        if not profile:
            return "Profile not found"
        
        info = f"## {profile.get('name')}, {profile.get('role')}\n\n"
        info += f"**Description:** {profile.get('backstory')}\n\n"
        info += "**Knowledge Areas:**\n"
        for area in profile.get('knowledge_areas', []):
            info += f"- {area}\n"
        
        return info
    
    npc_selector.change(update_npc_info, inputs=npc_selector, outputs=npc_info)
    
    # Generate prompt when button is clicked
    submit_btn.click(
        gradio_interface,
        inputs=[npc_selector],
        outputs=output
    )

if __name__ == "__main__":
    app.launch(server_port=7861) 