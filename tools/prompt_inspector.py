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
# Use absolute path to profiles directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILES_DIR = os.path.join(PROJECT_ROOT, "src/data/profiles")
profile_loader = ProfileLoader(PROFILES_DIR)
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
            # Create a list of options with display names
            profile_options = [(f"{display_name} [{profile_id}]", profile_id) 
                              for profile_id, display_name in available_profiles.items()]
            
            npc_selector = gr.Dropdown(
                choices=profile_options,
                label="Select NPC",
                value=profile_options[0][1] if profile_options else None,
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
        info += f"**Profile ID:** `{profile.get('profile_id')}`\n\n"
        info += f"**Description:** {profile.get('backstory')}\n\n"
        
        # Get base profiles that this profile extends
        extends = profile.get('extends', [])
        if extends:
            info += f"**Extends base profiles:** {', '.join(extends)}\n\n"
        
        # Display personality traits
        info += "**Personality Traits:**\n"
        traits = profile.get('personality_traits', {})
        if traits:
            for trait, value in traits.items():
                # Create a visual bar to represent the trait value
                bar_length = int(value * 10)
                bar = "█" * bar_length + "░" * (10 - bar_length)
                info += f"- **{trait}:** {bar} ({value:.1f})\n"
        else:
            info += "- No personality traits defined\n"
        
        info += "\n"
        
        # Get knowledge areas with sources
        knowledge_areas = profile_loader.get_knowledge_areas_with_sources(npc_id)
        info += "**Knowledge Areas:**\n"
        
        for ka in knowledge_areas:
            area = ka["area"]
            source = ka["source"]
            
            if source == "original":
                info += f"- {area}\n"
            else:
                info += f"- {area} *(inherited from {source})*\n"
        
        # Show response formats
        info += "\n**Response Formats:**\n"
        response_formats = profile.get('response_format', {})
        if response_formats:
            for intent, format_template in response_formats.items():
                info += f"- **{intent}:** `{format_template}`\n"
        else:
            info += "- No custom response formats defined\n"
        
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