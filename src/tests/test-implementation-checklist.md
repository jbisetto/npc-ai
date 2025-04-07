# Test Implementation Checklist

This checklist organizes test implementation priorities based on dependency levels, starting with the most isolated components and moving towards more integrated ones.

## Placeholder Components to Implement
These components currently have minimal placeholder implementations that need to be properly implemented and tested:

- [ ] `core/npc_profile.py`
  - [ ] Implement full personality trait system
  - [ ] Add proper response formatting logic
  - [ ] Add emotion expression system
  - [ ] Add proper profile loading/saving
  - [ ] Test all implemented functionality

- [ ] `core/storage_manager.py`
  - [ ] Implement actual data persistence
  - [ ] Add proper error handling
  - [ ] Add data validation
  - [ ] Add proper async file operations
  - [ ] Test all implemented functionality

## Level 1: Core Models and Utilities
These components have minimal or no dependencies and should be tested first.

- [x] `core/models.py` ✅ (14 tests passing)
  - [x] Test `ClassifiedRequest` class
  - [x] Test `CompanionRequest` class
  - [x] Test `ProcessingTier` enum
  - [x] Test request validation methods
  - [x] Test `GameContext` class
  - [x] Test `CompanionResponse` class
  - [x] Test `ConversationContext` class

- [x] `core/formatter_standalone.py` ✅ (7 component tests passing)
  - [x] Test standalone formatting functions
  - [x] Test text cleaning utilities
  - [x] 100% line coverage achieved
  - [x] All edge cases covered
  - [x] Unicode/Japanese text support verified

- [ ] `utils/monitoring.py`
  - [ ] Test monitoring utilities
  - [ ] Test logging functionality
  - NOTE: This component is currently not actively used. Its functionality is handled by Logger, UsageTracker, direct logging in HostedProcessor, and PlayerHistoryManager. Need to determine whether to integrate, remove, or refactor before implementing tests.

## Level 2: Core Services
These components depend primarily on core models.

- [x] `core/prompt_manager.py` ✅ (17 tests passing)
  - [x] Test prompt creation
  - [x] Test token estimation
  - [x] Test prompt optimization
  - [x] Test game context formatting
  - [x] Test error handling
  - [x] Test performance characteristics

- [ ] `core/response_formatter.py`
  - [ ] Test response formatting
  - [ ] Test text cleaning
  - [ ] Test Japanese text handling

- [ ] `local/response_parser.py`
  - [ ] Test response validation
  - [ ] Test response cleaning

- [ ] `hosted/usage_tracker.py`
  - [ ] Test usage tracking
  - [ ] Test limit enforcement
  - [ ] Test cost calculations

## Level 3: Storage and Context
These components handle state and persistence.

- [ ] `core/player_history_manager.py`
  - [ ] Test history storage
  - [ ] Test retrieval methods
  - [ ] Test history updates

- [x] `core/context_manager.py` ✅ (13 tests passing)
  - [x] Test context creation and retrieval
  - [x] Test context updates and deletion
  - [x] Test error handling and edge cases
  - [x] Test state management and timestamps
  - [x] Test serialization and deserialization

- [ ] `core/conversation_manager.py`
  - [ ] Test conversation state tracking
  - [ ] Test history management
  - [ ] Test contextual prompt generation

## Level 4: API Clients
These components handle external service interactions.

- [ ] `local/ollama_client.py`
  - [ ] Test client initialization
  - [ ] Test request formatting
  - [ ] Test response handling
  - [ ] Mock API interactions

- [ ] `hosted/bedrock_client.py`
  - [ ] Test client initialization
  - [ ] Test request formatting
  - [ ] Test response handling
  - [ ] Mock API interactions

## Level 5: Processors
These components integrate multiple services.

- [ ] `local/local_processor.py`
  - [ ] Test request processing
  - [ ] Test error handling
  - [ ] Test integration with Ollama client

- [ ] `hosted/hosted_processor.py`
  - [ ] Test request processing
  - [ ] Test error handling
  - [ ] Test integration with Bedrock client

## Level 6: Framework and Integration
These components represent the highest level of integration.

- [ ] `core/processor_framework.py`
  - [ ] Test processor selection
  - [ ] Test request routing
  - [ ] Test error handling
  - [ ] Test tier-based processing

- [ ] `core/request_handler.py`
  - [ ] Test request classification
  - [ ] Test processor selection
  - [ ] Test end-to-end request handling

## Test Infrastructure

- [x] Set up test fixtures
  - [x] Sample requests
  - [x] Test configurations
  - [ ] Mock API responses

- [x] Configure test environment
  - [x] Test configuration files
  - [x] Environment variables
  - [x] Logging setup

- [ ] Create test utilities
  - [ ] Request builders
  - [ ] Response validators
  - [ ] Mock service providers

## Notes

1. Each component should have:
   - Unit tests for individual functions
   - Integration tests for component interactions
   - Mock external dependencies
   - Error case coverage

2. Test coverage goals:
   - Line coverage: 80%+
   - Branch coverage: 70%+
   - Function coverage: 90%+

3. Testing standards:
   - Use pytest fixtures
   - Mock external services
   - Clear test naming
   - Comprehensive docstrings
   - Test both success and failure cases

4. Dependency Management:
   - Use lazy loading for component initialization
   - Avoid circular dependencies
   - Keep core models isolated
   - Use dependency injection where possible

5. Future Considerations:
   - Consider renaming `GameContext` to `LanguageContext` to better reflect its current purpose (only contains language-related information)
   - Update all references to use consistent naming (e.g., `game_context` to `language_context`) 