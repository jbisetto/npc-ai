# NPC AI REST API

A FastAPI-based REST API for the NPC AI system. This API provides access to the core NPC interaction functionality through a set of HTTP endpoints.

## Features

- Chat with NPCs through a simple REST interface
- Get information about available NPCs
- Check system health and component status

## Getting Started

### Running with Docker Compose

The recommended way to run the API is using Docker Compose, which will handle all dependencies and configuration:

```bash
# From the project root
docker-compose up -d
```

The API will be available at `http://localhost:8002`

### Running Locally

To run the API locally for development:

1. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r api/requirements.txt
```

2. Run the API server:
```bash
cd api
python -m uvicorn main:app --reload --port 8000
```

## API Documentation

Once the API is running, you can access the Swagger documentation at:
- `http://localhost:8002/docs`

### Endpoints

#### Chat with NPC
- **POST** `/api/v1/chat`
- Request body:
  ```json
  {
    "message": "Hello, can you help me?",
    "npc_id": "station_attendant_osaka",
    "player_id": "player_1"
  }
  ```
- Response:
  ```json
  {
    "response_text": "こんにちは！何かお手伝いしましょうか？(Hello! How can I help you?)",
    "processing_tier": "local",
    "suggested_actions": ["Ask for directions", "Buy a ticket"],
    "learning_cues": {
      "vocabulary": [
        {"word": "こんにちは", "reading": "konnichiwa", "meaning": "hello"}
      ]
    },
    "emotion": "friendly",
    "confidence": 0.95
  }
  ```

#### Get Valid NPC IDs
- **GET** `/api/v1/valid-npc-ids`
- Response:
  ```json
  [
    "station_attendant_osaka",
    "station_attendant_kyoto",
    "station_attendant_odawara", 
    "information_booth_attendant",
    "ticket_booth_attendant",
    "companion_dog"
  ]
  ```

#### Get NPC Profiles
- **GET** `/api/v1/npcs`
- Response:
  ```json
  {
    "npcs": [
      {
        "id": "yamada",
        "name": "Yamada (Station Staff)",
        "role": "staff",
        "personality": "professional_helpful"
      },
      ...
    ]
  }
  ```

#### Health Check
- **GET** `/api/v1/health`
- Response:
  ```json
  {
    "status": "ok",
    "local_model": true,
    "hosted_model": true,
    "knowledge_base": true
  }
  ```

## Environment Variables

The API uses the following environment variables:

- `AWS_ACCESS_KEY_ID` - AWS Access Key for Bedrock
- `AWS_SECRET_ACCESS_KEY` - AWS Secret Key for Bedrock
- `AWS_REGION` - AWS Region for Bedrock
- `AWS_DEFAULT_REGION` - Default AWS Region
- `BEDROCK_MODEL_ID` - Bedrock model ID to use (optional) 