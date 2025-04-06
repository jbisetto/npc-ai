# NPC Profile Refactoring Tasks

## Overview
During the recent refactoring, NPC profile functionality was partially removed but some code still exists. This checklist tracks what needs to be cleaned up or reimplemented.

## Files with NPC Profile References

- [ ] `src/ai/npc/core/npc/profile.py`
  - [ ] Remove unused emotion expressions
  - [ ] Remove personality traits system
  - [ ] Remove speech patterns
  - [ ] Consider removing entire file if not needed

- [ ] `src/data/profiles/`
  - [ ] Review and remove unused profile JSON files
  - [ ] Remove or update base_language_instructor.json
  - [ ] Clean up any other profile-related data files

- [ ] `src/ai/npc/core/response_formatter.py`
  - [ ] Remove personality-based formatting
  - [ ] Remove emotion expressions
  - [ ] Remove learning cues system
  - [ ] Clean up response formatting to basic functionality

## Configuration Updates

- [ ] `src/config/npc-config.yaml`
  - [ ] Remove profile-related settings
  - [ ] Update configuration examples
  - [ ] Remove personality configuration options

## Code Cleanup

- [ ] Remove Profile Dependencies
  - [ ] Check for imports of NPCProfile class
  - [ ] Remove profile initialization in processors
  - [ ] Clean up any profile-related type hints

- [ ] Clean Response Processing
  - [ ] Simplify response formatting
  - [ ] Remove personality-based modifications
  - [ ] Ensure basic response structure remains intact

## Documentation Updates

- [ ] Update Code Comments
  - [ ] Remove references to personality system
  - [ ] Remove references to emotion system
  - [ ] Update class and method documentation

- [ ] Update README
  - [ ] Remove any remaining profile references
  - [ ] Update feature list
  - [ ] Update architecture description

## Testing

- [ ] Update Tests
  - [ ] Remove profile-related test cases
  - [ ] Update response formatting tests
  - [ ] Remove personality/emotion test fixtures

## Final Verification

- [ ] Verify Core Functionality
  - [ ] Ensure basic response generation works
  - [ ] Check response formatting
  - [ ] Test conversation flow
  - [ ] Validate configuration loading

- [ ] Code Quality
  - [ ] Run linter on cleaned up code
  - [ ] Check for any remaining unused imports
  - [ ] Verify no broken references
  - [ ] Ensure documentation is consistent 