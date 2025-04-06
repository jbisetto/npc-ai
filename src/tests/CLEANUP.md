# Cleanup Required: IntentCategory References

The following files still contain references to the removed `IntentCategory` enum and need to be updated:

## Core Components
1. `src/ai/npc/core/npc/profile.py`
   - Line 15: Import statement
   - Line 154: Used in `get_response_format` method

2. `src/ai/npc/core/processor_framework.py`
   - Line 14: Import statement
   - Lines 90-106: Used in intent tree mapping

3. `src/ai/npc/core/response_formatter.py`
   - Line 12: Import statement
   - Lines 81-109: Intent-based formatting templates
   - Lines 455-466: Intent-based response formatting logic

4. `src/ai/npc/core/prompt/prompt_template_loader.py`
   - Line 12: Import statement
   - Line 90: Used in `get_intent_prompt` method

5. `src/ai/npc/core/context_manager.py`
   - Line 16: Import statement
   - Line 33, 81: Used in context management

## Hosted Components
1. `src/ai/npc/hosted/test_conversation_manager.py`
   - Line 11: Import statement
   - Line 54: Used in test cases

2. `src/ai/npc/hosted/context_manager.py`
   - Line 16: Import statement
   - Lines 33, 81: Used in context management

3. `src/ai/npc/hosted/bedrock_client.py`
   - Line 15: Import statement

4. `src/ai/npc/hosted/specialized_handlers.py`
   - Line 13: Import statement
   - Multiple uses throughout the file in handler logic
   - Lines 709-741: Used in handler registration

## Action Items
1. Remove all imports of `IntentCategory`
2. Update handler logic to use new classification system
3. Update response formatting to use new metadata-based approach
4. Update context management to remove intent dependencies
5. Update tests to reflect new classification system 