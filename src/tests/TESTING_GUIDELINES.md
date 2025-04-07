# Testing Guidelines

## Core Principles

### 1. Test Independence and Resource Isolation
- Each test must be self-contained and independent
- NO shared test files, datasets, or state between tests
- Clean up any test data or state after each test
- Use temporary directories/files when file operations are needed
- Tests must be able to run in any order
- Use fresh fixtures for each test

### 2. Model and Data Management

#### Model Dependency Testing
- Test all components that depend on a model when that model changes
- Verify required fields are present and correctly typed
- Test model serialization/deserialization
- Add regression tests when model fields are removed or renamed

#### Test Data Management
- Create test data programmatically within each test
- Create comprehensive fixture factories
- Document required fields and relationships
- Test with both minimal and complete data
- Use small, focused datasets specific to each test case
- Clean up all test data after test completion
- Use pytest fixtures for complex test data setup

### 3. Context and State Management

#### Context Setup
- Explicitly set up all required context in tests
- Document context requirements in test docstrings
- Use fixture factories to create consistent test contexts
- Don't assume empty/default state is sufficient for testing behavior

#### State Management
- Test state transitions
- Verify behavior in different states
- Test edge cases and invalid states
- Document expected state behavior

Example:
```python
def test_conversation_state_detection():
    """
    Test conversation state detection with proper context setup.
    
    Requirements:
    - Conversation history must be present
    - Context must include previous responses
    - State transitions must be verified
    """
    # GIVEN
    # Explicitly set up required context
    context = create_test_context_with_history()
    
    # WHEN
    # Test specific state transition
    state = manager.detect_conversation_state(request, context)
    
    # THEN
    # Verify expected behavior
    assert state == ConversationState.FOLLOW_UP
    assert context.is_valid()  # State integrity check
```

### 4. Integration and Dependencies

#### Integration Testing
- Test full component chains
- Verify cross-component communication
- Test with realistic data flows
- Check all related components when making significant changes

#### Import and Naming
- Verify public API consistency
- Test correct import paths
- Maintain consistent naming across modules
- Add linting rules for import consistency

#### Feature Coverage
- Test both simplified and full feature paths
- Document intentionally removed features
- Add regression tests for simplified functionality
- Verify core requirements are still met after simplification

### 5. External Service Testing

#### Comprehensive Mocking
- Mock all LLM interactions (Ollama, AWS Bedrock)
- Mock file system operations (use `tmp_path`)
- Mock external API calls
- Mock database connections
- Mock time-dependent operations

#### Mocking Guidelines
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

### 6. Error Handling and Edge Cases

#### Exception Testing
- Test all error paths and exception handlers
- Verify error messages and error codes
- Test recovery procedures
- Validate error state cleanup
- Test error propagation through component chains

Example:
```python
def test_error_handling():
    """
    Test error handling and recovery.
    
    Requirements:
    - All exceptions should be caught and handled
    - Error messages should be user-friendly
    - System should recover to valid state
    """
    # GIVEN
    processor = create_processor_with_error_state()
    
    # WHEN
    with pytest.raises(ProcessingError) as exc_info:
        processor.process(invalid_request)
    
    # THEN
    assert "user-friendly error message" in str(exc_info.value)
    assert processor.is_valid()  # System recovered
```

### 7. Asynchronous Testing

#### Async Test Setup
- Use pytest.mark.asyncio for async tests
- Properly manage event loops
- Handle async timeouts appropriately
- Clean up async resources

#### Async Fixtures
```python
@pytest.fixture
async def async_client():
    client = AsyncClient()
    yield client
    await client.close()  # Cleanup

@pytest.mark.asyncio
async def test_async_operation(async_client):
    result = await async_client.process()
    assert result.status == "success"
```

### 8. Test Data Evolution

#### Managing Test Data Changes
- Version test fixtures with code changes
- Document data format changes
- Provide data migration tools
- Test with both old and new formats during transition

#### Test Data Maintenance
- Regular review of test data relevance
- Clean up obsolete test data
- Update test data when models change
- Maintain backwards compatibility tests

### 9. Dependency Management

#### Dependency Chain Testing
- Map component dependencies
- Test in dependency order
- Identify circular dependencies
- Test dependency chain changes

Example:
```python
# Component dependency map
COMPONENT_DEPS = {
    "conversation_manager": ["context_manager", "prompt_manager"],
    "prompt_manager": ["bedrock_client"],
    "context_manager": ["storage"]
}

def test_dependency_chain():
    """Test full dependency chain."""
    # Test in order: storage -> context -> prompt -> conversation
```

### 10. Performance Testing

#### Performance Baselines
- Establish performance benchmarks
- Test under various loads
- Monitor memory usage
- Test resource cleanup

#### Performance Test Guidelines
```python
@pytest.mark.performance
def test_response_time():
    """
    Test response time under load.
    
    Requirements:
    - Response time < 200ms
    - Memory usage < 100MB
    - No resource leaks
    """
    start_memory = get_memory_usage()
    
    for _ in range(100):
        response = processor.process(request)
        assert response.time < 0.2  # 200ms
    
    assert get_memory_usage() - start_memory < 100_000_000  # 100MB
```

## Model Serialization Testing

### Pydantic vs Custom Serialization
When testing model serialization, be aware of the differences between Pydantic and custom serialization:

1. **Pydantic Models**:
   - Use `.model_dump()` (Pydantic v2) or `.dict()` (Pydantic v1) for serialization
   - Automatically handles nested models and complex types
   - Includes type validation during serialization
   - Example:
     ```python
     def test_pydantic_model_serialization():
         model = MyPydanticModel(field1="value", field2=123)
         serialized = model.model_dump()  # or model.dict() for v1
         deserialized = MyPydanticModel(**serialized)
         assert deserialized == model
     ```

2. **Custom Serialization**:
   - Uses custom `.to_dict()` and `.from_dict()` methods
   - Requires explicit handling of nested objects
   - Needs manual datetime ISO format conversion
   - Example:
     ```python
     def test_custom_model_serialization():
         model = MyCustomModel(field1="value", field2=123)
         serialized = model.to_dict()
         deserialized = MyCustomModel.from_dict(serialized)
         assert deserialized.field1 == model.field1
     ```

### Best Practices for Serialization Testing

1. **Test Round-Trip Serialization**:
   ```python
   def test_serialization_round_trip():
       original = MyModel(...)
       serialized = original.to_dict()
       deserialized = MyModel.from_dict(serialized)
       assert deserialized == original  # For Pydantic
       # For custom models, compare individual fields
       assert deserialized.field1 == original.field1
   ```

2. **Test Nested Objects**:
   ```python
   def test_nested_serialization():
       nested = NestedModel(...)
       parent = ParentModel(nested_field=nested)
       serialized = parent.to_dict()
       assert "nested_field" in serialized
       assert isinstance(serialized["nested_field"], dict)
   ```

3. **Test DateTime Handling**:
   ```python
   def test_datetime_serialization():
       model = MyModel(timestamp=datetime.now())
       serialized = model.to_dict()
       assert isinstance(serialized["timestamp"], str)
       assert datetime.fromisoformat(serialized["timestamp"])
   ```

4. **Test Optional Fields**:
   ```python
   def test_optional_fields_serialization():
       model = MyModel(required_field="value", optional_field=None)
       serialized = model.to_dict()
       assert "required_field" in serialized
       assert serialized.get("optional_field") is None
   ```

### Common Pitfalls to Avoid

1. **Datetime Handling**: Always use ISO format for datetime serialization
2. **Nested Objects**: Ensure proper recursion for nested object serialization
3. **Type Consistency**: Maintain consistent types during serialization/deserialization
4. **None Values**: Handle None values explicitly in both directions
5. **Validation**: Include validation in deserialization for custom models

### Migration Considerations

When migrating between serialization approaches:

1. Create compatibility tests for both old and new formats
2. Implement version checking in deserialization
3. Add migration utilities for converting between formats
4. Document breaking changes in serialization

## Test Implementation Process

### 1. Test Organization

#### File Structure
```
src/tests/
├── core/           # Core component tests
├── local/          # Local processor tests
├── hosted/         # Hosted service tests
└── utils/          # Utility tests
```

#### Test File Format
```python
"""
Tests for [component]

Test Strategy:
-------------
1. Unit Tests: [list key test areas]
2. Coverage Goals: [specific targets]
3. Dependencies: [list dependencies]
4. Required Context: [list required context/state]
"""

# Imports

# Fixtures

# Test Groups (with clear comments)
```

#### Naming Conventions
- Files: `test_[component].py`
- Functions: `test_[functionality]_[scenario]`
- Fixtures: Descriptive of what they provide

### 2. Test Development and Validation
1. Write tests following the test strategy
2. Ensure comprehensive docstrings
3. Group tests logically
4. Run new component tests in isolation
5. Run ALL tests in the test suite
6. Fix any failures and repeat

### 3. Coverage Requirements
- Line coverage: 80%+
- Branch coverage: 70%+
- Function coverage: 90%+
- Document any approved exceptions

## Running Tests

### Component Testing
```bash
python -m pytest path/to/test_file.py -v --cov=component_path
```

### Full Test Suite (REQUIRED)
```bash
python -m pytest src/tests/ -v
```

### Coverage Report
```bash
python -m pytest --cov=src --cov-report=term-missing
```

## Version Control Process

1. **Pre-Commit Checklist**
   - All new component tests pass
   - ALL existing tests pass
   - Coverage requirements met
   - Documentation updated

2. **Commit Message Format**
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
- Add tests for whitespace handling
- Add tests for edge cases
- Add test for Japanese text handling
- Create reusable request fixture

Component tests passing: 7 tests ✅
Total core tests passing: 21 tests ✅
```

## Common Pitfalls to Avoid
- Don't create actual files in the test directory
- Don't make real API calls in tests
- Don't use sleep() or time-based waits
- Don't rely on external services
- Don't use shared state between tests
- Don't assume default/empty state is sufficient
- Don't skip running the full test suite
- Don't commit without fixing ALL test failures
- Don't ignore performance degradation
- Don't skip error path testing
- Don't leave async resources uncleaned
- Don't ignore dependency order in tests

Remember: When in doubt:
1. Add more explicit context
2. Document assumptions
3. Test edge cases
4. Check component dependencies
5. Run the full test suite
6. Test all error paths
7. Clean up async resources
8. Check performance impact
9. Verify dependency chain
10. Run the full test suite 