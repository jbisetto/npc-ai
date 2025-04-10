# AI Demo

This is a simplified Gradio demo for the AI components of the Tokyo Train Station Adventure language learning game.

## Features

- Select an NPC to interact with (Dog Companion, Station Staff, etc.)
- Text input supporting English, Japanese, or mixed language
- AI responses using the core AI components from the main project
- Automatic tier selection based on configuration
- Display of which processing tier was used
- Debug panel showing raw request/response data for Tier2 and Tier3 processing
- Display of the actual prompts sent to AI models in Tier2 and Tier3

## Setup

1. Make sure you're in the demo directory:
   ```bash
   cd demo
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Make sure you have access to the main project dependencies:
   ```bash
   pip install -r ../requirements.txt
   ```

4. Initialize the knowledge base (from the project root directory):
   ```bash
   cd ..
   python initialize_knowledge_base.py
   cd demo
   ```
   This step ensures the Tokyo train station knowledge base is properly loaded with documents and intents before running the app.

## Running the Demo

Start the Gradio app with:
```bash
python app.py
```

The app will be available at http://localhost:7860 (or another port if 7860 is in use).

<img src="docs/images/ai-demo.png" alt="AI Demo Screenshot" width="600"/>

## Usage

1. Select an NPC from the dropdown menu
2. Type your message in English, Japanese, or a mix of both
3. Click "Send Message" or press Enter
4. View the AI's response below your input
5. The "Processing Tier Used" field shows which tier processed your request
6. Use the "Clear" button to reset the input and output fields
7. For Tier2 or Tier3 processing, expand the "Advanced: Debug Information" section to view:
   - The raw prompt sent to the AI model (in the "Raw Prompt" tab)
   - The raw request and response data (in the "Request/Response Data" tab)

## Processing Tiers

- **TIER_1**: Local DeepSeek LLM (used for moderately complex queries) 
- **TIER_2**: AWS Bedrock (used for complex queries)

## Debug Information

The collapsible "Advanced: Debug Information" section at the bottom of the interface provides:

- **Raw Prompt Tab**: Shows the complete, unmodified prompt text sent to the AI model
- **Request/Response Data Tab**:
  - **Raw Request**: The JSON data sent to the AI processing component
  - **Raw Response**: The complete JSON response from the AI component

This information is only populated for Tier2 and Tier3 processing, as these tiers involve more complex AI interactions. The raw prompt display is particularly useful for understanding how the system constructs prompts for different types of queries and NPC interactions.

## Known Issues

### Knowledge Base Persistence

The demo currently experiences issues with ChromaDB's vector store persistence. If you find that knowledge-based queries (e.g., "Where can I buy a ticket?", "How do I say 'ticket' in Japanese?") don't return expected results, you may need to re-run the knowledge base initialization script:

```bash
cd ..  # Return to project root
python initialize_knowledge_base.py
cd demo
python app.py
```

A robust fallback system has been implemented to ensure that even when vector search fails, the system will return basic knowledge documents through alternative retrieval methods.

These persistence issues are planned to be addressed in a future update.

## Troubleshooting

If you encounter errors:

1. Check the console output for specific error messages
2. Ensure all dependencies are properly installed
3. Verify that the main project's AI components are functioning correctly
4. For Tier2/Tier3 issues, examine the debug information panel for detailed request/response data
5. Inspect the raw prompt to see exactly what was sent to the AI model

## Notes

This demo uses the same AI components as the full game, but without the API layer. It directly interfaces with the core AI system, removing the unnecessary complexity of the API while still showcasing the sophisticated AI capabilities.