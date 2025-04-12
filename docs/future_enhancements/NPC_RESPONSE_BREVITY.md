# NPC Response Brevity Enhancement

## Executive Summary

This enhancement addresses the issue of Japanese NPC responses being too lengthy and incorrectly bilingual. Users expect responses limited to 1-2 short sentences in Japanese only, but were receiving paragraph-length bilingual responses. This update modifies the prompt templates and NPC profiles to ensure all Japanese NPC responses are concise and in Japanese only.

## Implementation Details

Two key components were modified:

1. The `BASE_SYSTEM_PROMPT` in `src/ai/npc/core/prompt_manager.py` was updated to:
   - Explicitly limit responses to 1-2 sentences maximum
   - Emphasize brevity as a critical constraint
   - Remove requirement for English translations
   - Specify Japanese-only responses
   - Update the example response format to demonstrate the desired brevity
   - Add a new constraint specifically for brevity

2. The language instructions in `src/ai/npc/core/profile/profile.py` were updated to:
   - Instruct Japanese NPCs to respond in Japanese only with 1-2 short sentences maximum
   - Remove instructions to provide English translations
   - Add emphasis on keeping answers "extremely brief and to the point"
   - Simplify example responses to demonstrate brevity
   - Ensure error messages for not understanding are also in Japanese

## Benefits

- More authentic Japanese conversational experience (native speakers in service roles typically use brief, concise responses)
- Easier for language learners to process and understand responses
- Better gameplay experience with quicker interactions
- Reduced token usage in AI model calls
- More realistic immersion in a Japanese-speaking environment

## Success Criteria

- Japanese NPC responses consistently limited to 1-2 sentences
- Japanese NPCs respond in Japanese only, without English translations
- Responses maintain grammatical correctness while being brief
- User feedback confirms the shorter responses improve game experience

## Status

**Completed** - Changes have been implemented in the codebase. The system now enforces brevity for all Japanese NPC responses and ensures they respond in Japanese only. 