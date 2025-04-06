# Testing Guidelines

## Core Principles

### 1. Resource Isolation
- Each test must have its own isolated resources
- NO shared test files, datasets, or state between tests
- Each test should create and clean up its own test data
- Use temporary directories/files when file operations are needed
- Clean up all temporary resources in test teardown

### 2. Comprehensive Mocking

#### Must Mock
- All LLM interactions
  - Ollama API calls (avoid requiring local setup)
  - AWS Bedrock API calls (avoid costs and external dependencies)
- File system operations (use `tmp_path` or `tmp_path_factory` from pytest)
- External API calls
- Database connections
- Time-dependent operations

#### Mocking Guidelines
- Use pytest fixtures for common mocks
- Define explicit return values for mocked calls
- Mock at the lowest possible level (usually the client/API layer)
- Include error cases in mock scenarios
- Document mock behavior in test docstrings

### 3. Test Data Management
- Create test data programmatically within each test
- Don't rely on external files or shared datasets
- Use small, focused datasets specific to each test case
- Clean up all test data after test completion
- Use pytest fixtures for complex test data setup

### 4. Test Independence
- Tests must be able to run in any order
- No test should depend on the state from another test
- No shared global state between tests
- Each test should be self-contained
- Use fresh fixtures for each test

### 5. Test Structure

#### Fixture Usage
```python
# Good
@pytest.fixture
def mock_ollama_client():
    with patch('src.ai.npc.local.ollama_client.OllamaClient') as mock:
        mock.generate.return_value = {"response": "Test response"}
        yield mock

# Bad - Don't create shared resources
@pytest.fixture(scope="session")
def shared_test_data():  # DON'T DO THIS
    return load_shared_test_data()
```

#### Test Setup
```python
# Good
def test_local_processor(tmp_path, mock_ollama_client):
    # Setup isolated test data
    test_data = {"prompt": "test"}
    processor = LocalProcessor(tmp_path)
    
    # Run test with mocked client
    result = processor.process(test_data)
    
    # Assert expected results
    assert result == "Test response"

# Bad - Don't use shared resources
def test_with_shared_data(shared_data_file):  # DON'T DO THIS
    # This creates test dependencies
    pass
```

### 6. Testing External Services

#### Local LLM (Ollama)
- Mock all Ollama API calls
- Test different response scenarios
- Include error handling tests
- Verify request formatting
- Test rate limiting behavior

```python
def test_ollama_client_call(mock_ollama):
    client = OllamaClient()
    response = client.generate("test prompt")
    
    mock_ollama.assert_called_once_with(
        prompt="test prompt",
        model="specified_model"
    )
```

#### Hosted LLM (Bedrock)
- Mock all AWS Bedrock calls
- Test token counting and limits
- Include cost-related validations
- Test error handling and retries
- Verify request/response formatting

```python
def test_bedrock_client_call(mock_bedrock):
    client = BedrockClient()
    response = client.generate("test prompt")
    
    mock_bedrock.invoke_model.assert_called_once()
```

### 7. Common Pitfalls to Avoid
- Don't create actual files in the test directory
- Don't make real API calls in tests
- Don't use sleep() or time-based waits
- Don't rely on external services being available
- Don't use shared state between tests
- Don't create tests that require specific environment setup

### 8. Performance Considerations
- Keep test data small and focused
- Mock time-consuming operations
- Use appropriate scoping for fixtures
- Clean up resources promptly
- Avoid unnecessary file I/O

### 9. Documentation
- Document mock behavior and test assumptions
- Explain complex test setups
- Document any required fixture setup
- Include examples of expected outputs
- Document any special cleanup requirements

### 10. Test Coverage Goals
- Aim for high coverage of core logic
- Include error cases and edge conditions
- Test configuration validation
- Test response formatting
- Test resource cleanup
- Test proper mock usage

### 11. Version Control and Commits
- Commit after each component's tests are passing
- Use descriptive commit messages following this format:
  ```
  test(component): add tests for [component name]
  
  - List specific test cases added
  - Note any mock implementations
  - Reference related issues/tasks
  
  All tests passing: XX tests ✅
  ```
- Include test coverage stats in commit message if available
- Keep commits focused on single components
- Don't mix test implementations with feature code
- Update test implementation checklist in same commit
- Example commit:
  ```
  test(models): add tests for core data models
  
  - Add tests for ClassifiedRequest
  - Add tests for CompanionRequest
  - Add tests for ProcessingTier enum
  - Add tests for GameContext
  - Add tests for ConversationContext
  - Implement test fixtures for common test data
  
  All tests passing: 14 tests ✅
  Coverage: 92% (models.py)
  ``` 