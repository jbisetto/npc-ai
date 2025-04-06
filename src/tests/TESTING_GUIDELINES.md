# Testing Guidelines

## Test Implementation Process

1. **Test Development**
   - Write tests following the test strategy outlined in each test file
   - Ensure comprehensive docstrings for all tests
   - Group tests logically (basic functionality, edge cases, etc.)
   - Use appropriate fixtures and mocks

2. **Test Execution and Validation**
   - First, run new component tests in isolation to verify implementation
   - Once component tests pass, IMMEDIATELY run ALL tests in the test suite
   - **CRITICAL**: No changes can be committed until both:
     a) New component tests pass
     b) ALL existing tests pass without regression
   - If any test fails, fix and repeat both steps

3. **Coverage Requirements**
   - Line coverage: 80%+
   - Branch coverage: 70%+
   - Function coverage: 90%+
   - Document any approved exceptions

4. **Version Control**
   - Only commit after BOTH new and existing tests pass
   - Include test counts in commit messages (e.g., "7 new tests ✅, all 21 existing tests ✅")
   - Document any test strategy changes

## Test Organization

1. **File Structure**
   ```
   src/tests/
   ├── core/           # Core component tests
   ├── local/          # Local processor tests
   ├── hosted/         # Hosted service tests
   └── utils/          # Utility tests
   ```

2. **Test File Format**
   ```python
   """
   Tests for [component]
   
   Test Strategy:
   -------------
   1. Unit Tests: [list key test areas]
   2. Coverage Goals: [specific targets]
   3. Dependencies: [list dependencies]
   """
   
   # Imports
   
   # Fixtures
   
   # Test Groups (with clear comments)
   ```

3. **Naming Conventions**
   - Files: `test_[component].py`
   - Functions: `test_[functionality]_[scenario]`
   - Fixtures: Descriptive of what they provide

## Best Practices

1. **Test Independence**
   - Each test should be self-contained
   - Clean up any test data or state
   - No dependencies between tests

2. **Resource Management**
   - Mock external services
   - Use appropriate fixtures
   - Clean up resources after tests

3. **Documentation**
   - Clear test strategy in module docstring
   - Comprehensive test docstrings
   - Document any non-obvious test decisions

4. **Error Handling**
   - Test both success and failure cases
   - Verify error messages and types
   - Test edge cases and boundaries

## Running Tests

1. **New Component Testing**
   ```bash
   python -m pytest path/to/test_file.py -v --cov=component_path
   ```

2. **Full Test Suite (REQUIRED)**
   ```bash
   python -m pytest src/tests/ -v
   ```

3. **Coverage Report**
   ```bash
   python -m pytest --cov=src --cov-report=term-missing
   ```

Remember: Changes are only complete when BOTH new tests AND the full test suite pass. Never skip running the full suite after adding new tests.

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
Before any commit, ALL existing tests must pass. The process is:

1. Implement new tests for the current component
2. Run the new component's tests to verify them
3. Run ALL existing tests to ensure no regressions
4. Only if all tests pass, the assistant will provide a commit message following this format:

```
test(component): add tests for [component name]

- List specific test cases added
- Note any significant implementation changes
- Reference related issues/tasks

Component tests passing: XX tests ✅
Total core tests passing: YY tests ✅
```

Example:
```
test(formatter): add tests for standalone formatter

- Add tests for basic text formatting
- Add tests for whitespace handling (leading, trailing, internal)
- Add tests for edge cases (None, empty string)
- Add test for Japanese text handling
- Create reusable request fixture

Component tests passing: 7 tests ✅
Total core tests passing: 21 tests ✅
```

The user will handle the actual commit process using GitHub Desktop.

If any test fails:
1. The issue must be investigated and fixed
2. All tests must be run again
3. This cycle continues until all tests pass
4. Only then can the changes be committed 