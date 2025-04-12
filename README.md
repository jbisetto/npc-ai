# NPC AI

A flexible AI-powered NPC system that provides natural language interactions in a Japanese train station setting. The system uses both local and cloud-based language models to generate contextually appropriate responses.

## Features

- **Dual Processing Modes**
  - Local processing using Ollama for offline capabilities
  - Hosted processing using Amazon Bedrock for enhanced responses

- **Japanese Language Support** _(Developed for ExamPro GenAI Bootcamp)_
  - JLPT N5 level vocabulary and grammar constraints
  - Bilingual responses with English translations
  - Romaji pronunciation guides
  - Basic cultural context in responses

- **Conversation Management**
  - Conversation history tracking
  - Response validation and formatting
  - Simple prompt-based interactions

- **Performance Optimization**
  - Token-aware prompt management
  - Response validation and cleaning
  - Usage tracking and rate limiting
  - Efficient conversation context handling

## Architecture

```
project/
├── src/
│   ├── ai/
│   │   └── npc/
│   │       ├── core/                 # Core components and interfaces
│   │       │   ├── profile/          # NPC profile implementations
│   │       │   ├── prompt/           # Prompt templates and generation
│   │       │   ├── storage/          # Storage interfaces
│   │       │   ├── vector/           # Vector store implementations
│   │       │   ├── adapters.py       # Format conversion adapters
│   │       │   ├── context_manager.py # Request context management
│   │       │   ├── knowledge_adapter.py # Knowledge format standardization
│   │       │   ├── history_adapter.py  # Conversation history adapters
│   │       │   ├── models.py         # Data models and request types
│   │       │   ├── prompt_manager.py # Prompt creation and optimization
│   │       │   └── processor_framework.py # Processing tier management
│   │       ├── local/                # Local processing using Ollama
│   │       │   ├── local_processor.py # Ollama integration
│   │       │   └── ollama_client.py  # Ollama API client
│   │       ├── hosted/               # Cloud processing using Bedrock
│   │       │   ├── hosted_processor.py # Bedrock integration
│   │       │   ├── bedrock_client.py # AWS Bedrock client
│   │       │   └── usage_tracker.py  # API usage monitoring
│   │       └── utils/                # Shared utilities
│   ├── config/                       # Configuration files
│   │   └── npc-config.yaml          # Main configuration file
│   ├── data/                         # Game data and resources
│   └── tests/                        # Test suite
├── api/                              # REST API implementation
│   ├── routes/                       # API endpoint definitions
│   ├── models/                       # API data models
│   ├── main.py                       # FastAPI application
│   ├── test_api.sh                   # API test script
│   ├── test_valid_ids.sh             # Valid NPC IDs test
│   └── test_invalid_npc.sh           # Invalid NPC ID test
├── demo/                             # Demo application
│   └── app.py                        # Gradio demo interface
├── docs/                             # Documentation
│   └── crazy-response.json           # Example of problematic responses
└── tools/                            # Development tools
    └── prompt_inspector.py           # Prompt visualization tool
```

## Getting Started

### Prerequisites

- Python 3.9+
- Ollama (for local processing)
- AWS credentials (for hosted processing)
- Docker and Docker Compose (for REST API)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/jbisetto/npc-ai.git
cd npc-ai
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the system:
- Copy `src/config/npc-config.yaml.example` to `src/config/npc-config.yaml`
- Update configuration settings as needed

5. Initialize the knowledge base:
```bash
python initialize_knowledge_base.py
```
This step is required before starting the demo to ensure the knowledge store is properly populated with the Tokyo train station information. The initialization script:
- Loads documents from the knowledge base JSON file
- Correctly assigns intents based on document types (DIRECTION_GUIDANCE, GENERAL_HINT, VOCABULARY_HELP)
- Creates vector embeddings for semantic search
- Verifies documents are loaded successfully with appropriate logging
- Runs quality tests to ensure the knowledge base is functioning properly

### Running the Demo

```bash
python demo/app.py
```
<img src="demo/docs/images/ai-demo.png" alt="AI Demo Screenshot" width="600"/>

### Running the REST API

The project includes a FastAPI-based REST API that provides access to the NPC AI functionality through HTTP endpoints.

1. Using Docker Compose (recommended):
```bash
docker-compose up -d
```

2. Accessing the API:
   - The API will be available at http://localhost:8002
   - Swagger documentation: http://localhost:8002/docs

See the [API documentation](api/README.md) for more details on available endpoints.

## Known Issues and Future Enhancements

### ⚠️ MAJOR ISSUE: DeepSeek Model with Ollama - English-Only Responses

**IMPORTANT:** When using the DeepSeek model through Ollama, we are currently experiencing an issue where NPCs only respond in English, ignoring the Japanese language instructions in the prompts. This behavior is unexpected and inconsistent with other models.

- This affects all NPCs when the local processing mode with DeepSeek is enabled
- The issue appears to be with how DeepSeek interprets bilingual instructions
- The problem does not occur with hosted models (Amazon Bedrock)

Investigation is ongoing to determine:
- Whether this is a limitation of the DeepSeek model itself
- If there are prompt engineering approaches that could resolve this
- Whether specific Ollama configuration changes might help

**Workaround:** If bilingual responses are crucial for your use case, consider:
- Using a different local model
- Switching to hosted processing (Amazon Bedrock)
- Adding explicit Japanese text/translations in your inputs

This issue is a high priority for resolution in future updates.

### ⚠️ Knowledge Context (RAG) Disabled Due to Hallucinations

**IMPORTANT:** We have intentionally disabled the knowledge context inclusion in prompts (RAG implementation) due to issues with hallucinations and off-character responses. 

The system has a fully implemented Retrieval Augmented Generation (RAG) capability using vector store embeddings, but we found that adding knowledge context to prompts caused some models to:
- Ignore their character role instructions
- Break the fourth wall by mentioning they are AI systems
- Provide meta-commentary rather than in-character responses

For example, see `docs/crazy-response.json` where Hachiko (dog companion) responds:
```
Hello! I'm not Hachiko, but I'm here to assist you as an AI system built by a team of inventors at Amazon.
```

This issue is particularly problematic for roleplaying characters and degrades the experience. The knowledge context option is set to `false` in `src/config/npc-config.yaml` as a precaution.

**Future Work:** We plan to explore alternative approaches to knowledge integration that don't cause character breaks, such as:
- Different prompt formatting for knowledge context
- Model-specific prompt engineering techniques
- Fine-tuning models to better respect character constraints

### ⚠️ ChromaDB Persistence Workaround

**IMPORTANT:** Currently, there is an issue with ChromaDB's persistence mechanism when storing vector embeddings. The system properly loads data into memory during initialization but has trouble maintaining persistence between application restarts. This affects the semantic search capabilities in some scenarios.

Workarounds implemented:
- The system includes robust fallback mechanisms to ensure knowledge retrieval works even when vector search fails
- Initial knowledge base loading is performed through a separate initialization script
- Additional diagnostics have been added to monitor knowledge store performance

This issue is planned to be addressed in a future update that will:
- Implement a more reliable persistence layer for the vector store
- Add migration capabilities for vector data
- Provide better configuration options for ChromaDB

### Future Enhancements

See [docs/future_enhancements](docs/future_enhancements)

## Configuration

The main configuration files are:

- `npc-config.yaml`: Core NPC settings including AI model selection (local/hosted)
  - Local model settings (Ollama)
  - Hosted model settings (Bedrock)
  - System prompts and optimization settings
  - Usage tracking and limits

***NOTE:*** current configuration has local tier disabled and hosted tier (ASW) enabled

## Environment Configuration

This project uses environment variables for configuration, particularly for AWS credentials. These should be stored in a `.env` file in the project root, which is not committed to version control.

### Setting up AWS credentials

1. Create a `.env` file in the project root with the following template:
   ```
   # AWS Credentials for Bedrock
   AWS_ACCESS_KEY_ID=your_access_key_here
   AWS_SECRET_ACCESS_KEY=your_secret_key_here
   AWS_REGION=us-east-1
   AWS_DEFAULT_REGION=us-east-1
   
   # Bedrock configuration
   BEDROCK_MODEL_ID=amazon.nova-micro-v1:0
   # Uncomment to use debug mode without real API calls
   # BEDROCK_DEBUG_MODE=true
   ```

2. Replace the placeholder values with your actual AWS credentials.

3. **IMPORTANT: Never commit the `.env` file or hardcode credentials in the source code.**

4. Ensure your IAM user has the necessary permissions, including:
   ```
   bedrock:InvokeModel
   ```

## Development

### Running Tests

```bash
cd src
./run_tests.sh
```

### Development Tools

#### Prompt Inspector

The Prompt Inspector is a GUI tool that helps visualize how prompts are generated for different NPCs without making actual API calls.

<img src="tools/docs/images/prompt_inspector.png" alt="Prompt Inspector Screenshot" width="600"/>

To use the Prompt Inspector:

1. Install the required dependencies:
   ```bash
   pip install -r tools/prompt_inspector_requirements.txt
   ```

2. Run the tool:
   ```bash
   python tools/prompt_inspector.py
   ```

3. Access the interface at http://localhost:7861

Key features:
- View detailed NPC profile information
- See which knowledge areas are inherited from base profiles
- Visualize personality traits with graphical indicators
- Preview the complete AI prompt for any NPC
- Explore base profile inheritance chains

The Prompt Inspector helps with debugging and understanding how profiles are composed without modifying any source code.

### Project Structure

- `core/`: Core components and interfaces
  - `models.py`: Data models and request types
  - `prompt_manager.py`: Prompt creation and optimization
  - `processor_framework.py`: Processing tier management
  - `context_manager.py`: Conversation and state management

- `local/`: Local processing components
  - `local_processor.py`: Ollama-based processing
  - `ollama_client.py`: Ollama API client
  - `response_parser.py`: Response validation

- `hosted/`: Cloud processing components
  - `hosted_processor.py`: Bedrock-based processing
  - `bedrock_client.py`: AWS Bedrock client
  - `usage_tracker.py`: API usage monitoring

## License

This project is licensed under the MIT License - see the LICENSE file for details.
