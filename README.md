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
src/
├── ai/
│   └── npc/
│       ├── core/           # Core components and interfaces
│       ├── local/         # Local processing using Ollama
│       ├── hosted/        # Cloud processing using Bedrock
│       └── utils/         # Shared utilities
├── config/                # Configuration files
├── data/                  # Game data and resources
└── tests/                # Test suite
```

## Getting Started

### Prerequisites

- Python 3.9+
- Ollama (for local processing)
- AWS credentials (for hosted processing)

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

### Running the Demo

```bash
python demo/app.py
```

## Configuration

The main configuration files are:

- `npc-config.yaml`: Core NPC settings including AI model selection (local/hosted)
  - Local model settings (Ollama)
  - Hosted model settings (Bedrock)
  - System prompts and optimization settings
  - Usage tracking and limits

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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Ollama team for the local LLM support
- AWS Bedrock team for the cloud LLM services

