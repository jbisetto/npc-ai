# Configuration Reference

This document provides a comprehensive reference for configuring the NPC AI system.

## Configuration File Structure

The system uses a YAML-based configuration structure with the following sections:

```yaml
# Main configuration file: config/npc-config.yaml
general:
  debug_mode: false
  log_level: "INFO"
  log_file: "logs/npc-ai.log"
  profiles_dir: "src/data/profiles"

retry:
  max_attempts: 3
  initial_backoff: 1.0
  max_backoff: 10.0
  backoff_factor: 2.0

local:
  base_url: "http://localhost:11434"
  default_model: "deepseek-r1:latest"
  cache_enabled: true
  cache_dir: "/tmp/cache"
  request_timeout: 30

hosted:
  debug_mode: false
  fallback_to_local: true
  bedrock:
    region_name: "us-west-2"
    model_id: "anthropic.claude-3-sonnet-20240229-v1:0"
    max_tokens: 4000
    temperature: 0.7
    top_p: 0.9
    top_k: 250
    stop_sequences: []

knowledge_store:
  persist_directory: "data/vector_store"
  collection_name: "tokyo_knowledge"
  embedding_model: "all-MiniLM-L6-v2"
  similarity_threshold: 0.75
  max_results: 5
  cache_size: 1000

conversation_manager:
  storage_dir: "data/conversations"
  max_history_items: 10
  ttl_days: 30

usage_tracking:
  enabled: true
  storage_path: "data/usage/bedrock_usage.json"
  auto_save: true
  quota:
    daily_request_limit: 1000
    daily_token_limit: 100000
    monthly_cost_limit: 50.0
```

## Environment Variables

Environment variables can override configuration settings:

| Variable | Description | Default |
|----------|-------------|---------|
| `NPC_DEBUG_MODE` | Enable debug mode | `false` |
| `NPC_LOG_LEVEL` | Logging level | `INFO` |
| `OLLAMA_BASE_URL` | Ollama API base URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Default Ollama model | `deepseek-r1:latest` |
| `AWS_REGION` | AWS region for Bedrock | `us-west-2` |
| `AWS_ACCESS_KEY_ID` | AWS access key ID | - |
| `AWS_SECRET_ACCESS_KEY` | AWS secret access key | - |
| `BEDROCK_MODEL_ID` | Bedrock model ID | `anthropic.claude-3-sonnet-20240229-v1:0` |
| `VECTOR_STORE_PATH` | Vector store directory | `data/vector_store` |

## Configuration Sections

### General Settings

```yaml
general:
  debug_mode: false      # Enable/disable debug mode
  log_level: "INFO"      # Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  log_file: "logs/npc-ai.log"  # Log file path
  profiles_dir: "src/data/profiles"  # NPC profiles directory
```

### Retry Settings

```yaml
retry:
  max_attempts: 3        # Maximum retry attempts
  initial_backoff: 1.0   # Initial backoff in seconds
  max_backoff: 10.0      # Maximum backoff in seconds
  backoff_factor: 2.0    # Backoff multiplication factor
```

### Local Processor Settings

```yaml
local:
  base_url: "http://localhost:11434"  # Ollama API base URL
  default_model: "deepseek-r1:latest"  # Default model to use
  cache_enabled: true    # Enable response caching
  cache_dir: "/tmp/cache"  # Cache directory
  request_timeout: 30    # Request timeout in seconds
```

### Hosted Processor Settings

```yaml
hosted:
  debug_mode: false      # Debug mode for hosted processor
  fallback_to_local: true  # Fall back to local if hosted fails
  bedrock:
    region_name: "us-west-2"  # AWS region for Bedrock
    model_id: "anthropic.claude-3-sonnet-20240229-v1:0"  # Model ID
    max_tokens: 4000     # Maximum tokens to generate
    temperature: 0.7     # Temperature for response generation
    top_p: 0.9           # Top-p sampling parameter
    top_k: 250           # Top-k sampling parameter
    stop_sequences: []   # Sequences to stop generation at
```

### Knowledge Store Settings

```yaml
knowledge_store:
  persist_directory: "data/vector_store"  # Vector store directory
  collection_name: "tokyo_knowledge"  # Collection name
  embedding_model: "all-MiniLM-L6-v2"  # Embedding model
  similarity_threshold: 0.75  # Similarity threshold
  max_results: 5         # Maximum results to return
  cache_size: 1000       # Cache size
```

### Conversation Manager Settings

```yaml
conversation_manager:
  storage_dir: "data/conversations"  # Conversation storage directory
  max_history_items: 10  # Maximum history items per conversation
  ttl_days: 30          # Time-to-live in days
```

### Usage Tracking Settings

```yaml
usage_tracking:
  enabled: true          # Enable usage tracking
  storage_path: "data/usage/bedrock_usage.json"  # Storage path
  auto_save: true        # Auto-save usage data
  quota:
    daily_request_limit: 1000  # Daily request limit
    daily_token_limit: 100000  # Daily token limit
    monthly_cost_limit: 50.0  # Monthly cost limit in USD
```

## Configuration Loading

The configuration is loaded from multiple sources with the following precedence:

1. Environment variables (highest priority)
2. Command-line arguments
3. User configuration file
4. Default configuration file

```python
def load_config():
    """Load configuration from multiple sources."""
    # Load default configuration
    default_config = load_yaml_config(DEFAULT_CONFIG_PATH)
    
    # Load user configuration if exists
    user_config = {}
    if os.path.exists(USER_CONFIG_PATH):
        user_config = load_yaml_config(USER_CONFIG_PATH)
    
    # Merge configurations
    config = deep_merge(default_config, user_config)
    
    # Apply environment variable overrides
    apply_env_overrides(config)
    
    # Validate configuration
    validate_config(config)
    
    return config
```

## Configuration Utility Functions

### Getting Configuration Values

```python
def get_config(key_path, default=None):
    """
    Get a configuration value by dot-separated path.
    
    Args:
        key_path: Dot-separated path to config value (e.g., 'local.base_url')
        default: Default value if key not found
        
    Returns:
        The configuration value or default
    """
    global _config
    
    if _config is None:
        _config = load_config()
    
    # Split the key path
    keys = key_path.split('.')
    
    # Navigate to the value
    value = _config
    for key in keys:
        if key in value:
            value = value[key]
        else:
            return default
    
    return value
```

### Configuration Validation

```python
def validate_config(config):
    """
    Validate configuration values.
    
    Args:
        config: Configuration dictionary
        
    Raises:
        ConfigError: If configuration is invalid
    """
    # Validate local configuration
    if 'local' in config:
        local_config = config['local']
        if 'base_url' not in local_config:
            raise ConfigError("Local processor config missing 'base_url'")
    
    # Validate hosted configuration
    if 'hosted' in config:
        hosted_config = config['hosted']
        if 'bedrock' not in hosted_config:
            raise ConfigError("Hosted processor config missing 'bedrock' section")
    
    # Validate knowledge store configuration
    if 'knowledge_store' in config:
        ks_config = config['knowledge_store']
        if 'persist_directory' not in ks_config:
            raise ConfigError("Knowledge store config missing 'persist_directory'")
```

## Configuration Files

### Default Configuration

The default configuration is defined in `config/npc-config.yaml`.

### User Configuration

Users can create their own configuration in `~/.npc-ai/config.yaml`, which will override the default configuration.

### Environment Configuration

Environment-specific configuration can be created in `config/npc-config.{ENV}.yaml`, where `{ENV}` is the environment name (e.g., `development`, `production`).

## Dynamic Configuration

Some configuration parameters can be changed at runtime:

```python
def update_config(key_path, value):
    """
    Update a configuration value at runtime.
    
    Args:
        key_path: Dot-separated path to config value
        value: New value
        
    Returns:
        True if successful, False otherwise
    """
    global _config
    
    if _config is None:
        _config = load_config()
    
    # Split the key path
    keys = key_path.split('.')
    
    # Navigate to the parent
    parent = _config
    for key in keys[:-1]:
        if key in parent:
            parent = parent[key]
        else:
            return False
    
    # Update the value
    parent[keys[-1]] = value
    return True
```

## Configuration Best Practices

1. **Never hardcode credentials** - Use environment variables for sensitive information
2. **Validate configuration** - Always validate configuration values before using them
3. **Provide sensible defaults** - Ensure the system works with default configuration
4. **Use environment-specific configurations** - Create separate configurations for development, testing, and production
5. **Document all configuration options** - Keep this documentation up to date

## Troubleshooting Configuration Issues

### Common Configuration Problems

1. **Missing credentials** - Check that AWS credentials are properly set
2. **Invalid file paths** - Ensure all file paths are correct and accessible
3. **Port conflicts** - Check if the port specified for Ollama is already in use
4. **Model not found** - Verify that the specified model is available

### Debugging Configuration

To debug configuration issues:

1. Set `NPC_LOG_LEVEL=DEBUG` in your environment
2. Check the log file for configuration loading messages
3. Use the `debug_config` utility to print the current configuration:

```python
python -m src.ai.npc.debug_config
```

## Example Configurations

### Development Configuration

```yaml
general:
  debug_mode: true
  log_level: "DEBUG"

local:
  cache_enabled: false

hosted:
  debug_mode: true
```

### Production Configuration

```yaml
general:
  debug_mode: false
  log_level: "WARNING"

retry:
  max_attempts: 5

local:
  cache_enabled: true

hosted:
  fallback_to_local: true
  
usage_tracking:
  enabled: true
  quota:
    daily_request_limit: 10000
    monthly_cost_limit: 500.0
``` 