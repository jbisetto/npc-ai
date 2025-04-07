"""
Test utilities package for the NPC AI system.

This package provides shared utilities for testing, including:
- Request/Context factories
- Mock response generators
- File system helpers
- Assertion helpers
"""

from .factories import *
from .mock_responses import *
from .fs_helpers import *
from .assertions import *

__all__ = [
    # Factories
    'create_test_request',
    'create_test_game_context',
    'create_test_conversation_context',
    
    # Mock Responses
    'create_mock_llm_response',
    'create_mock_japanese_response',
    'create_mock_error_response',
    
    # File System Helpers
    'create_temp_json_file',
    'create_corrupted_json_file',
    'cleanup_test_files',
    
    # Assertions
    'assert_valid_response',
    'assert_valid_context',
    'assert_valid_json',
    'assert_valid_japanese'
] 