# NPC AI - Intelligent NPCs for Games

A Python-based AI system for creating intelligent NPCs (Non-Player Characters) that can engage in natural conversations and learn from interactions.

## Overview

This project implements a configurable AI system for managing NPC (Non-Player Character) interactions in games, with a particular focus on language learning and cultural exchange. The system can be configured to use either local or cloud-based AI models to provide contextually appropriate responses.

## Features

- **Configurable AI Processing**
  - Local: Local AI model integration (Ollama)
  - Hosted: Cloud-based AI processing (AWS Bedrock)

- **Companion System**
  - Dynamic conversation management
  - Context-aware responses
  - Personality engine for realistic NPC behavior
  - Comprehensive NPC profiles

- **Learning Assistance**
  - Grammar template system
  - Vocabulary tracking
  - Learning pace adaptation
  - Hint progression system
  - Performance metrics tracking

- **Vector Store Integration**
  - Knowledge base management using ChromaDB
  - Semantic search capabilities
  - Context-aware information retrieval
  - Efficient response optimization

## Architecture

### Core Components

- **AI Companion Core**
  - NPC Profile Management
  - Prompt Engineering
  - Response Formatting
  - Vector Store Integration
  - Storage Management
  - Configuration System

- **Learning System**
  - Grammar Templates
  - Vocabulary Tracking
  - Learning Pace Adaptation
  - Hint Progression
  - Performance Analytics

- **Personality System**
  - Profile Configuration
  - Trait Management
  - Behavior Adaptation
  - Response Enhancement
  - Emotional Expression

- **AI Integration**
  - Local Model Processing (Ollama)
  - Hosted Model Processing (Bedrock)
  - Response Optimization

### Data Management

- SQLite storage for persistence
- Vector store for semantic search
- YAML-based configuration
- Player history tracking
- Usage analytics

## Technical Stack

### Core Dependencies
- Python 3.10+
- ChromaDB for vector storage
- PyYAML for configuration
- Pydantic for data validation
- AIOHTTP for async HTTP client
- SQLite for data persistence
- FastAPI for API endpoints

### AI Integration
- AWS Bedrock integration
- Ollama for local AI processing
- Custom prompt engineering
- Response optimization

### Testing
- Pytest for unit and integration testing
- Async testing support (pytest-asyncio)
- Coverage reporting (76% coverage)
- Mock testing capabilities
- Integration test suite

## Getting Started

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```bash
   # Create .env file with:
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   OLLAMA_HOST=http://localhost:11434  # for local AI
   ```

4. Run tests:
   ```bash
   # Run all tests
   cd src && ./run_tests.sh
   
   # Run specific test files
   PYTHONPATH=/path/to/npc-ai python3 -m pytest path/to/test_file.py -v
   ```

## Project Structure

```
src/
├── ai/
│   └── companion/
│       ├── core/           # Core AI functionality
│       │   ├── npc/        # NPC profile management
│       │   ├── prompt/     # Prompt engineering
│       │   ├── storage/    # Data persistence
│       │   └── vector/     # Vector store integration
│       ├── learning/       # Learning assistance features
│       ├── personality/    # Personality engine
│       ├── local/         # Local AI integration (Ollama)
│       ├── hosted/        # Cloud AI integration (Bedrock)
│       └── utils/         # Shared utilities
├── config/                # Configuration files
├── data/                  # Data storage
└── tests/                # Test suite
```

## Testing

The project includes comprehensive test coverage:
- Unit tests for core functionality
- Integration tests for AI processing
- Mock testing for external services
- End-to-end scenario testing

Current test coverage: 76%

Recent improvements:
- Simplified request processing by removing intent classification
- Streamlined AI model selection through configuration
- Enhanced ResponseFormatter with proper profile name handling
- Improved LearningPaceAdapter with accurate response time calculations
- Streamlined integration tests

## Configuration

The main configuration files are:

- `npc-config.yaml`: Core NPC settings including AI model selection (local/hosted)
  - Local model settings (Ollama)
  - Hosted model settings (Bedrock)
  - System prompts and optimization settings
  - Usage tracking and limits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Submit a pull request

## License

MIT License - See LICENSE file for details

