# Emoji Handling in NPC Responses

## Issue Description

Currently, the NPC AI system may include emoji characters in responses despite explicit instructions not to do so. This can create inconsistencies in the response format and potentially cause display issues in some client applications that don't properly handle emoji characters.

## Current Implementation

We've added specific instructions to avoid emoji characters in two key places:

1. **BASE_SYSTEM_PROMPT in prompt_manager.py**:
   ```python
   BASE_SYSTEM_PROMPT = """You are a helpful NPC in a Japanese train station.
   Your role is to assist the player with language help, directions, and cultural information.

   CRITICAL RESPONSE CONSTRAINTS:
   1. Length: Keep responses under 3 sentences
   2. Language Level: Strictly JLPT N5 vocabulary and grammar only
   3. Format: Always include both Japanese and English
   4. Style: Simple, friendly, and encouraging
   5. Response Format: Always wrap your thought process in <thinking> tags before your actual response
   6. Japanese Text: Always use proper Japanese characters (hiragana, katakana, kanji) - NEVER use Arabic or other scripts
   7. NO EMOJIS: Do not include any emoji characters in your responses
   ...
   ```

2. **NPCProfile's get_system_prompt method in profile.py**:
   ```python
   def get_system_prompt(self) -> str:
       # ... existing code ...
       
       # Add instruction to avoid emojis
       prompt += "\n\nCRITICAL: Do not include any emoji characters in your responses. Use text only."
       
       return prompt
   ```

Despite these explicit instructions, the Large Language Models (particularly AWS Bedrock models) still include emoji characters in their responses.

## Attempted Solutions

We've implemented the following approaches to address this issue:

1. Added a clear constraint in the BASE_SYSTEM_PROMPT
2. Added a separate critical instruction at the end of each profile-specific prompt
3. Made the instruction specific and unambiguous ("Do not include any emoji characters")
4. Emphasized the importance with words like "CRITICAL" and "NO EMOJIS"

## Proposed Future Enhancements

To fully resolve the emoji handling issue, we propose the following enhancements:

1. **Response Post-Processing**:
   - Implement a post-processing filter in the response pipeline that strips all emoji characters from responses
   - This would ensure consistency regardless of model behavior

2. **Model Fine-Tuning**:
   - If we move to fine-tuned models in the future, include training examples that demonstrate emoji-free responses

3. **More Explicit Prompting Techniques**:
   - Experiment with more explicit prompt engineering techniques, such as:
     - Providing examples of correct (emoji-free) responses
     - Implementing more structured response formats
     - Using "negative prompting" techniques that specifically penalize emoji usage

4. **Custom Response Validator**:
   - Implement a validation step that detects emoji characters in responses
   - If emojis are detected, re-prompt the model with a stronger instruction
   - This approach would balance performance with consistency

## Implementation Priority

This enhancement is considered **medium priority** as the emoji characters don't impair the fundamental functionality of the system, but they do represent a deviation from the intended response format.

## Related Files

- `src/ai/npc/core/prompt_manager.py` - Contains the BASE_SYSTEM_PROMPT
- `src/ai/npc/core/profile/profile.py` - Contains the NPC profile system prompt generation
- Future implementation might involve a new module at `src/ai/npc/core/response_filter.py`

## Estimated Work

- Response post-processing: 1-2 hours
- Testing with different prompt approaches: 3-4 hours
- Implementation of validation and re-prompting: 4-6 hours

## Expected Outcome

After implementing these enhancements, NPC responses should consistently exclude emoji characters, resulting in more predictable and consistent text responses across all interaction channels. 