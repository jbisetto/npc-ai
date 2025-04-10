# NPC AI Request Processing Flow

This document describes how the NPC AI system processes requests using both local and hosted processors. It includes sequence diagrams and explanations of the key components and their interactions.

## Processor Selection

The system uses a simple processor selection based on the `processing_tier` field in the request:

1. **Selection Logic**
   ```mermaid
   sequenceDiagram
       Player->>ProcessorFramework: NPCRequest
       Note over ProcessorFramework: Check processing_tier
       
       alt processing_tier == LOCAL
           ProcessorFramework->>LocalProcessor: Process Request
           LocalProcessor-->>Player: Response
       else processing_tier == HOSTED
           ProcessorFramework->>HostedProcessor: Process Request
           HostedProcessor-->>Player: Response
       end
   ```

2. **Request Model**
   ```python
   class NPCRequest(BaseModel):
       request_id: str
       player_input: str
       game_context: Optional[GameContext] = None
       processing_tier: Optional[ProcessingTier] = None
       additional_params: Dict[str, Any] = field(default_factory=lambda: {
           METADATA_KEY_INTENT: INTENT_DEFAULT
       })
   ```

3. **Processing Tier Enum**
   ```python
   class ProcessingTier(Enum):
       LOCAL = "local"
       HOSTED = "hosted"
   ```

## Response Formatting Flow
The system uses a formatter-based approach to handle different LLM response formats:

```mermaid
sequenceDiagram
    participant Client
    participant ResponseParser
    participant ResponseFormatter
    participant DeepSeekFormatter
    participant DefaultFormatter

    Client->>ResponseParser: parse_response(raw_response, request)
    
    alt using DeepSeekFormatter
        ResponseParser->>DeepSeekFormatter: format_response(raw_response)
        Note over DeepSeekFormatter: Extract <thinking> section
        DeepSeekFormatter-->>ResponseParser: (response_text, thinking_section)
    else using DefaultFormatter
        ResponseParser->>DefaultFormatter: format_response(raw_response)
        Note over DefaultFormatter: No special formatting
        DefaultFormatter-->>ResponseParser: (raw_response, None)
    end
    
    ResponseParser->>ResponseParser: clean_response()
    ResponseParser->>ResponseParser: validate_response()
    ResponseParser-->>Client: formatted_result
```

## Local Processor Flow
The local processor uses Ollama for generating responses locally.

```mermaid
sequenceDiagram
    Client->>LocalProcessor: process(request)
    
    alt has conversation history
        LocalProcessor->>ConversationManager: get_player_history(player_id, standardized_format=True)
        ConversationManager-->>LocalProcessor: history
    end
    
    alt has npc_id in game context
        LocalProcessor->>ProfileRegistry: get_profile(npc_id, as_object=True)
        ProfileRegistry-->>LocalProcessor: profile
    end
    
    LocalProcessor->>KnowledgeStore: contextual_search(request, standardized_format=True)
    KnowledgeStore-->>LocalProcessor: knowledge_context
    
    LocalProcessor->>PromptManager: create_prompt(request, history, profile, knowledge_context)
    PromptManager-->>LocalProcessor: prompt
    
    LocalProcessor->>OllamaClient: generate(prompt)
    alt success
        OllamaClient-->>LocalProcessor: response_text
        LocalProcessor->>ResponseParser: parse_response(response_text, request)
        ResponseParser-->>LocalProcessor: result
        
        alt has conversation history
            LocalProcessor->>ConversationManager: add_to_history(conversation_id, user_query, response, npc_id, player_id)
        end
        LocalProcessor-->>Client: result with debug_info
    else error
        OllamaClient-->>LocalProcessor: error
        LocalProcessor-->>Client: fallback_response
    end
```

## Hosted Processor Flow
The hosted processor uses Amazon Bedrock for cloud-based response generation.

```mermaid
sequenceDiagram
    Client->>HostedProcessor: process(request)
    Note over HostedProcessor: Record start time
    
    alt has conversation history
        HostedProcessor->>ConversationManager: get_player_history(player_id, standardized_format=True)
        ConversationManager-->>HostedProcessor: history
    end
    
    HostedProcessor->>KnowledgeStore: contextual_search(request, standardized_format=True)
    KnowledgeStore-->>HostedProcessor: knowledge_context
    
    HostedProcessor->>PromptManager: create_prompt(request, history, knowledge_context)
    PromptManager-->>HostedProcessor: prompt
    
    HostedProcessor->>BedrockClient: generate(prompt)
    alt success
        BedrockClient-->>HostedProcessor: response_text
        HostedProcessor->>ResponseParser: parse_response(response_text, request)
        ResponseParser-->>HostedProcessor: result
        
        alt has conversation history
            HostedProcessor->>ConversationManager: add_to_history(conversation_id, user_query, response, npc_id, player_id)
        end
        HostedProcessor-->>Client: result with debug_info
    else API error
        BedrockClient-->>HostedProcessor: api_error
        HostedProcessor-->>Client: fallback_response
    else quota exceeded
        BedrockClient-->>HostedProcessor: quota_error
        HostedProcessor-->>Client: quota_exceeded_response
    end
    
    Note over HostedProcessor: Log elapsed time
```

## Resource Cleanup Flow

Both processors implement a `close` method to properly release resources when they're no longer needed:

```mermaid
sequenceDiagram
    participant Application
    participant Processor
    participant Client
    participant KnowledgeStore
    
    Application->>Processor: close()
    
    alt LocalProcessor
        Processor->>Client: close()
        Note over Client: OllamaClient closes session
        Client-->>Processor: Success/Error
    else HostedProcessor
        Processor->>Client: close()
        Note over Client: BedrockClient releases resources
        Client-->>Processor: Success/Error
    end
    
    Processor->>KnowledgeStore: clear()
    KnowledgeStore-->>Processor: Success/Error
    
    Processor->>KnowledgeStore: close()
    KnowledgeStore-->>Processor: Success/Error
    
    Processor-->>Application: Resources released
```

## Response Formatter Design

The system uses the Strategy pattern to handle different LLM response formats:

1. **ResponseFormatter Protocol**
   ```python
   class ResponseFormatter(Protocol):
       def format_response(self, raw_response: str) -> tuple[str, Optional[str]]:
           """Format a raw response from an LLM."""
           ...
   ```

2. **Concrete Formatters**
   ```python
   class DeepSeekFormatter:
       """Formats responses from DeepSeek models which use <thinking> tags."""
       def format_response(self, raw_response: str) -> tuple[str, Optional[str]]:
           # Extract <thinking> sections
           ...

   class DefaultFormatter:
       """Default formatter for LLMs that don't have special formatting needs."""
       def format_response(self, raw_response: str) -> tuple[str, Optional[str]]:
           return raw_response.strip(), None
   ```

3. **Usage**
   ```python
   # Parse response with the appropriate formatter
   result = self.response_parser.parse_response(response_text, request)
   ```

## Key Differences

1. **Model Backend**
   - Local: Uses Ollama for local model inference
   - Hosted: Uses Amazon Bedrock for cloud-based inference

2. **NPC Profile Handling**
   - Local: Loads and uses NPC profiles directly
   - Hosted: Currently doesn't explicitly use NPC profiles

3. **Response Formatting**
   - DeepSeek: Extracts thinking sections from `<thinking>` tags
   - Default: No special formatting, returns raw response

4. **Error Handling**
   - Local: Implements retry mechanism with error handling
   - Hosted: Handles quota errors specifically and tracks API usage

5. **Configuration**
   - Local: Simpler configuration focused on Ollama settings
   - Hosted: More complex configuration including API quotas, model settings

6. **Performance Monitoring**
   - Local: Basic error logging
   - Hosted: Comprehensive usage tracking and monitoring

7. **Resource Management**
   - Both processors implement a `close` method to release resources
   - Resources include clients, knowledge stores, and usage trackers

## Common Components

Both processors share these components:
- Conversation Manager: Tracks chat history
- Knowledge Store: Provides relevant context
- Prompt Manager: Creates optimized prompts
- Response Parser: Standardizes output format using appropriate formatter

## Component Details

### Response Parser and Formatters
- Uses Strategy pattern to handle different LLM response formats
- Supports multiple formatters for different LLMs
- Maintains clean separation of formatting logic
- Easy to add support for new LLM formats

```mermaid
sequenceDiagram
    participant Client
    participant ResponseParser
    participant FormatterRegistry
    participant Formatter
    
    Client->>ResponseParser: parse_response(raw_response, request)
    ResponseParser->>FormatterRegistry: get_formatter_for_model(model_id)
    FormatterRegistry-->>ResponseParser: appropriate_formatter
    
    ResponseParser->>Formatter: format_response(raw_response)
    alt has <thinking> tags
        Formatter->>Formatter: extract_thinking_section()
        Formatter->>Formatter: extract_response_section()
    end
    Formatter-->>ResponseParser: formatted_text, thinking_text
    
    ResponseParser->>ResponseParser: clean_response(formatted_text)
    Note over ResponseParser: Remove artifacts, normalize whitespace
    
    ResponseParser->>ResponseParser: extract_metadata(formatted_text)
    Note over ResponseParser: Extract language info, emotions, etc.
    
    ResponseParser->>ResponseParser: construct_result(text, metadata)
    ResponseParser-->>Client: result dictionary
```

### Conversation Manager
- Manages conversation history for each player
- Provides context for more coherent responses
- Handles conversation persistence
- Supports standardized format for interchangeable use between processors

```mermaid
sequenceDiagram
    participant Client
    participant ConversationManager
    participant Storage
    participant HistoryAdapter
    
    alt get history
        Client->>ConversationManager: get_player_history(player_id, standardized_format=True)
        ConversationManager->>Storage: load_history(player_id)
        Storage-->>ConversationManager: raw_history_data
        
        alt standardized format requested
            ConversationManager->>HistoryAdapter: to_standard_format(raw_history_data)
            HistoryAdapter-->>ConversationManager: standardized_history
            ConversationManager-->>Client: standardized_history
        else raw format
            ConversationManager-->>Client: raw_history_data
        end
    else add to history
        Client->>ConversationManager: add_to_history(conversation_id, user_query, response, npc_id, player_id)
        ConversationManager->>ConversationManager: create_history_entry(user_query, response)
        ConversationManager->>Storage: append_to_history(player_id, history_entry)
        Storage-->>ConversationManager: success/failure
        ConversationManager-->>Client: success/failure
    end
```

### Knowledge Store
- Stores and retrieves relevant game information
- Provides context-aware responses using vector search
- Implements caching for performance
- Supports standardized format for consistent knowledge representation

```mermaid
sequenceDiagram
    participant Client
    participant KnowledgeStore
    participant Cache
    participant VectorDB
    participant KnowledgeAdapter
    
    Client->>KnowledgeStore: contextual_search(request, standardized_format=True)
    
    KnowledgeStore->>KnowledgeStore: generate_cache_key(request)
    KnowledgeStore->>Cache: check_cache(cache_key)
    
    alt cache hit
        Cache-->>KnowledgeStore: cached_results
    else cache miss
        KnowledgeStore->>KnowledgeStore: extract_query_text(request)
        KnowledgeStore->>KnowledgeStore: apply_filters(request)
        
        KnowledgeStore->>VectorDB: vector_search(query_text, filters)
        VectorDB-->>KnowledgeStore: search_results
        
        KnowledgeStore->>KnowledgeStore: rank_results(search_results)
        KnowledgeStore->>Cache: store_in_cache(cache_key, search_results)
    end
    
    alt standardized format requested
        KnowledgeStore->>KnowledgeAdapter: to_standard_format(results)
        KnowledgeAdapter-->>KnowledgeStore: standardized_results
        KnowledgeStore-->>Client: standardized_results
    else raw format
        KnowledgeStore-->>Client: raw_results
    end
```

### Prompt Manager
- Creates optimized prompts for each model
- Handles token limits and optimization
- Manages model-specific configurations
- Supports including NPC profiles, knowledge context, and conversation history

```mermaid
sequenceDiagram
    participant Client
    participant PromptManager
    participant TemplateEngine
    participant TokenCounter
    
    Client->>PromptManager: create_prompt(request, history, profile, knowledge_context)
    
    PromptManager->>PromptManager: select_template(request, processor_tier)
    PromptManager->>PromptManager: prepare_context(knowledge_context)
    PromptManager->>PromptManager: prepare_history(history)
    PromptManager->>PromptManager: prepare_profile(profile)
    
    PromptManager->>TemplateEngine: render_template(template, context_vars)
    TemplateEngine-->>PromptManager: full_prompt
    
    PromptManager->>TokenCounter: estimate_tokens(full_prompt)
    TokenCounter-->>PromptManager: token_count
    
    alt token count exceeds limit
        PromptManager->>PromptManager: truncate_context()
        PromptManager->>TemplateEngine: render_template(template, reduced_context)
        TemplateEngine-->>PromptManager: truncated_prompt
    end
    
    PromptManager-->>Client: optimized_prompt
```

### NPC Profile Registry
- Loads and manages NPC profiles
- Provides profile data for personalized responses
- Supports profile inheritance and extension

```mermaid
sequenceDiagram
    participant Client
    participant ProfileRegistry
    participant FileSystem
    participant ProfileCache
    
    Client->>ProfileRegistry: get_profile(npc_id, as_object=True)
    
    ProfileRegistry->>ProfileCache: check_cache(npc_id)
    
    alt cache hit
        ProfileCache-->>ProfileRegistry: cached_profile
    else cache miss
        ProfileRegistry->>FileSystem: load_profile_file(npc_id)
        FileSystem-->>ProfileRegistry: profile_data
        
        alt has parent profile
            ProfileRegistry->>ProfileRegistry: get_profile(parent_id)
            Note over ProfileRegistry: Recursive call to get parent
            ProfileRegistry->>ProfileRegistry: merge_profiles(parent_profile, profile_data)
        end
        
        ProfileRegistry->>ProfileCache: cache_profile(npc_id, profile)
    end
    
    alt as object requested
        ProfileRegistry->>ProfileRegistry: convert_to_object(profile_data)
        ProfileRegistry-->>Client: profile_object
    else as dictionary
        ProfileRegistry-->>Client: profile_dictionary
    end
```

## Error Handling

### Local Processor
- Implements error handling for OllamaClient errors
- Provides detailed error logging
- Generates fallback responses when errors occur

### Hosted Processor
- Handles quota errors specifically
- Tracks API usage and limits
- Provides tiered fallback responses
- Different messages for quota exceeded vs general errors

## Performance Considerations

### Local Processor
- Limited by local compute resources
- No API costs
- May have slower response times
- Lower infrastructure requirements

### Hosted Processor
- Higher quality responses
- Faster processing
- API usage costs
- Quota management required
- Higher infrastructure requirements

## Resource Management

Both processors implement a cleanup mechanism:

### LocalProcessor
- Closes OllamaClient to release network resources
- Clears and closes KnowledgeStore to release memory and database connections

### HostedProcessor
- Releases BedrockClient resources
- Closes UsageTracker if available
- Clears and closes KnowledgeStore to release memory and database connections