# NPC AI Request Processing Flow

This document describes how the NPC AI system processes requests using both local and hosted processors. It includes sequence diagrams and explanations of the key components and their interactions.

## Local Processor Flow
The local processor uses Ollama for generating responses locally.

```mermaid
sequenceDiagram
    participant Player
    participant LocalProcessor
    participant ConversationManager
    participant KnowledgeStore
    participant PromptManager
    participant OllamaClient
    participant ResponseParser

    Player->>LocalProcessor: Request
    
    alt Has Conversation ID
        LocalProcessor->>ConversationManager: Get Player History
        ConversationManager-->>LocalProcessor: Conversation History
    end
    
    LocalProcessor->>KnowledgeStore: Contextual Search
    KnowledgeStore-->>LocalProcessor: Knowledge Context
    
    LocalProcessor->>PromptManager: Create Prompt
    PromptManager-->>LocalProcessor: Formatted Prompt
    
    loop Max 3 Retries
        LocalProcessor->>OllamaClient: Generate Response
        
        alt Success
            OllamaClient-->>LocalProcessor: Response Text
            break
        else Error
            OllamaClient-->>LocalProcessor: Error
            Note over LocalProcessor: Wait with exponential backoff
        end
    end
    
    LocalProcessor->>ResponseParser: Parse Response
    ResponseParser-->>LocalProcessor: Parsed Result
    
    alt Has Conversation ID
        LocalProcessor->>ConversationManager: Add To History
    end
    
    LocalProcessor-->>Player: Response

    alt Error Handling
        LocalProcessor-->>Player: Fallback Response
    end
```

## Hosted Processor Flow
The hosted processor uses Amazon Bedrock for cloud-based response generation.

```mermaid
sequenceDiagram
    participant Player
    participant HostedProcessor
    participant ConversationManager
    participant KnowledgeStore
    participant PromptManager
    participant BedrockClient
    participant UsageTracker
    participant ResponseParser

    Player->>HostedProcessor: Request
    
    alt Has Conversation ID
        HostedProcessor->>ConversationManager: Get Player History
        ConversationManager-->>HostedProcessor: Conversation History
    end
    
    HostedProcessor->>KnowledgeStore: Contextual Search
    KnowledgeStore-->>HostedProcessor: Knowledge Context
    
    HostedProcessor->>PromptManager: Create Prompt
    Note over PromptManager: Uses Bedrock-specific config
    PromptManager-->>HostedProcessor: Formatted Prompt
    
    HostedProcessor->>BedrockClient: Generate Response
    BedrockClient->>UsageTracker: Track API Usage
    
    alt Success
        BedrockClient-->>HostedProcessor: Response Text
        HostedProcessor->>ResponseParser: Parse Response
        ResponseParser-->>HostedProcessor: Parsed Result
        
        alt Has Conversation ID
            HostedProcessor->>ConversationManager: Add To History
        end
        
        HostedProcessor-->>Player: Response
    else Error
        alt Quota Error
            HostedProcessor-->>Player: Quota Exceeded Message
        else Other Error
            HostedProcessor-->>Player: Generic Fallback Response
        end
    end
```

## Key Differences

1. **Model Backend**
   - Local: Uses Ollama for local model inference
   - Hosted: Uses Amazon Bedrock for cloud-based inference

2. **Error Handling**
   - Local: Implements retry mechanism with exponential backoff
   - Hosted: Handles quota errors specifically and tracks API usage

3. **Configuration**
   - Local: Simpler configuration focused on Ollama settings
   - Hosted: More complex configuration including API quotas, model settings

4. **Performance Monitoring**
   - Local: Basic error logging
   - Hosted: Comprehensive usage tracking and monitoring

5. **Cost Considerations**
   - Local: Free to use, limited by local compute resources
   - Hosted: Pay-per-use, higher quality but more expensive

## Common Components

Both processors share these components:
- Conversation Manager: Tracks chat history
- Knowledge Store: Provides relevant context
- Prompt Manager: Creates optimized prompts
- Response Parser: Standardizes output format

## Component Details

### Conversation Manager
- Manages conversation history for each player
- Provides context for more coherent responses
- Handles conversation persistence

### Knowledge Store
- Stores and retrieves relevant game information
- Provides context-aware responses
- Implements caching for performance

### Prompt Manager
- Creates optimized prompts for each model
- Handles token limits and optimization
- Manages model-specific configurations

### Response Parser
- Standardizes response format
- Handles error cases
- Ensures consistent output structure

## Error Handling

### Local Processor
- Implements retry mechanism with exponential backoff
- Maximum of 3 retry attempts
- Provides generic fallback responses

### Hosted Processor
- Handles quota errors specifically
- Tracks API usage and limits
- Provides tiered fallback responses

## Performance Considerations

### Local Processor
- Limited by local compute resources
- No API costs
- May have slower response times

### Hosted Processor
- Higher quality responses
- Faster processing
- API usage costs
- Quota management required 