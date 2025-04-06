# NPC AI

A flexible AI-powered NPC system that provides natural language interactions in a Japanese train station setting. The system uses both local and cloud-based language models to generate contextually appropriate responses.

## Features

- **Dual Processing Modes**
  - Local processing using Ollama
  - Hosted processing using Amazon Bedrock
  - Automatic fallback and tier-based processing

- **Japanese Language Support**
  - JLPT N5 level vocabulary and grammar
  - Bilingual responses (Japanese and English)
  - Pronunciation guides
  - Cultural context integration

- **Context Management**
  - Conversation history tracking
  - Player state management
  - Game context integration
  - NPC profile system

- **Performance Optimization**
  - Token-aware prompt management
  - Response validation
  - Efficient context handling
  - Usage tracking and limits

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

