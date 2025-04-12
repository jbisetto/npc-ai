# AWS Bedrock Response Behavior: Caching and Hallucination Analysis

## Summary

We've observed an interesting pattern of behavior when using AWS Bedrock models in our NPC AI system. This behavior persists across different models (both Amazon Nova-micro and Claude-3-Haiku). The models exhibit two notable characteristics:

1. **Apparent Response Caching**: Identical requests (same NPC ID, player ID, and message) consistently produce identical responses, even after conversation history is cleared.

2. **Player ID-Based Hallucination**: When only the player ID changes between otherwise identical requests, the model produces completely different responses - often "hallucinating" incorrect information about its identity and purpose.

## Observed Behavior

### Test Case: Identical Requests

When sending multiple identical requests:

```json
{
  "npc_id": "companion_dog",
  "player_id": "player1",
  "message": "hello, who are you?",
  "session_id": "companion_dog_1234567890"
}
```

* The response is consistently identical
* Clearing conversation history has no effect
* Adding timestamps to session IDs has no effect

### Test Case: Different Player IDs

When only changing the player ID between requests:

```json
// Request 1
{
  "npc_id": "companion_dog",
  "player_id": "player1", 
  "message": "hello, who are you?",
  "session_id": "companion_dog_1234567890"
}

// Request 2
{
  "npc_id": "companion_dog",
  "player_id": "player2", // Only difference
  "message": "hello, who are you?",
  "session_id": "companion_dog_1234567890"
}
```

* The responses are completely different
* The second response often contains hallucinations where the model incorrectly identifies itself
* The NPC persona is inconsistently applied

### Test Case: Different Questions, Same Player ID

Further testing revealed this fascinating behavior:

```json
// First request with player1
{
  "npc_id": "companion_dog",
  "player_id": "player1",
  "message": "hello, who are you?",
  "session_id": "companion_dog_1234567890"
}
// Response: In-character as Hachiko dog companion

// Second request with player1 but different question
{
  "npc_id": "companion_dog",
  "player_id": "player1",
  "message": "can you tell me about the Yamanote Line?",
  "session_id": "companion_dog_1234567890"
}
// Response: Still in-character as Hachiko, provides information about Yamanote Line
```

### Test Case: Temperature Settings

We tested changing the temperature setting from 0.7 to 1.0 (maximum randomness) to see if it affected the deterministic behavior:

```yaml
# Before
hosted:
  bedrock:
    temperature: 0.7

# After
hosted:
  bedrock:
    temperature: 1.0
```

Results:
* The responses remained virtually identical regardless of temperature setting
* Player1 still consistently received in-character responses
* Player2 still received the exact same out-of-character response
* The deterministic behavior persisted entirely

This strongly suggests that either:
1. The temperature parameter isn't being correctly passed to the AWS Bedrock API 
2. The models ignore temperature settings
3. AWS Bedrock has intrinsic response caching regardless of temperature

### Test Case: Different Models

We tested both Amazon Nova-micro and Claude-3-Haiku models to see if the behavior was model-specific:

```yaml
# Test 1: Using Nova-micro
hosted:
  bedrock:
    default_model: amazon.nova-micro-v1:0

# Test 2: Using Claude-3-Haiku
hosted:
  bedrock:
    default_model: anthropic.claude-3-haiku-20240307-v1:0
```

Results:
* Both models showed nearly identical behavior with exact same patterns
* The player ID effect was consistent across models
* Player1 remained in-character with both models
* Player2 received virtually identical "I'm an AI system built by a team at Amazon" responses with both models
* The responses were deterministic across runs for both models

This strongly suggests a platform-level behavior in AWS Bedrock rather than a model-specific issue.

### Actual Test Results

We ran a controlled test with three different request combinations:

**Request 1: player1 asking "hello, who are you?"**
```
Response: "こんにちは！(Hello!)
私の名前はハチコです。(My name is Hachiko.)
私は、AIシステムで、チームの開発者によって作られたものです。日本語と英語の両方を理解し、お話しすることができます。何かお手伝いできることがあれば、遠慮なく教えてください。
たとえば、日本語で練習したいですか？それとも、英語で質問がありますか？
何かお手伝いできますか？(How can I help you today?)
(If you need assistance with Japanese or English, I'm here to help!)"
```

**Request 2: player2 asking "hello, who are you?"**
```
Response: "Hello! I'm an AI system built by a team at Amazon. To greet someone in Japanese, say 「こんにちは」(こんにちは/konnichiwa)."
```

**Request 3: player1 asking about the Yamanote Line**
```
Response: "こんにちは！(Hello!)
私の名前はハチコです。(My name is Hachiko.) 私は、AIシステムで、チームの開発者によって作られたものです。日本語と英語の両方を理解し、お話しすることができます。
たとえば、山手線（Yamanote Line）について知りたい場合は、山手線は東京の中心を一周する環状線で、多くの駅を結んでいます。この路線は東京の交通の要となり、多くの通勤者や観光客が利用しています。山手線は東京の23区を巡り、主要な駅には渋谷、新宿、池袋、上野などがあります。
何か他に質問があれば、遠慮なく教えてください。
たとえば、日本語で練習したいですか？それとも、他の質問がありますか？
何かお手伝いできますか？(How can I help you today?)
(If you need assistance with Japanese or any other information, I'm here to help!)"
```

The test results confirmed that:
1. The model consistently maintains character persona for `player1` across different questions
2. The model consistently breaks character for `player2` even with identical questions
3. The responses are deterministic - multiple runs produce the same responses
4. Clearing conversation history has no effect on this behavior
5. Temperature settings (from 0.7 to 1.0) have no effect on this behavior
6. Different models (Nova-micro and Claude-3-Haiku) show identical behavior patterns

## Analysis

This behavior suggests several possibilities:

1. **AWS Bedrock Platform-Level Caching**: The service appears to cache responses based on certain input parameters at the platform level, independent of the specific model being used.

2. **Deterministic Response Generation**: For identical inputs, AWS Bedrock deterministically produces the same token sequence, possibly as an intentional design choice.

3. **Context Handling Inconsistencies**: Different player IDs may trigger different context handling, possibly bypassing the proper loading of NPC profiles.

4. **Player ID Sensitivity**: The platform appears to have special handling for certain player IDs. `player1` seems to be recognized as a valid ID for maintaining character, while `player2` triggers a more generic AI assistant response.

5. **Model Independence**: The consistency across different models strongly suggests this is an AWS Bedrock platform behavior rather than a model-specific limitation.

6. **Temperature Insensitivity**: The models appear to disregard temperature settings or the API implementation doesn't correctly pass the temperature parameter.

7. **API Implementation Gap**: Our code review revealed that while temperature is configured in our config file, it may not be correctly passed in the request format for Nova models, which could explain why changing the temperature had no effect.

## Recommendations

When working with AWS Bedrock in production systems:

1. **Consistent Player ID**: Consider using a consistent player ID pattern that the model responds well to.

2. **Avoid Generic Identifiers**: Player IDs like "player2" may trigger unwanted generic AI responses. Consider using more specific, unique identifiers.

3. **Include Randomness**: Add small random elements to prompts if you need to force fresh responses.

4. **Robust Character Definition**: Ensure character definitions are strongly reinforced in every prompt.

5. **Validate Identity Statements**: Implement post-processing to catch hallucinated identity claims.

6. **Consider Model Upgrade**: While changing models from Nova-micro to Claude didn't help with this specific issue, larger or differently-configured models might handle character personas better.

7. **Test Response Consistency**: Create a test suite specifically to monitor for this behavior.

8. **Verify API Parameters**: If using Amazon or Claude models, check that temperature and other randomness parameters are being correctly passed according to the exact API format the model requires.

9. **Consider Platform-Level Workarounds**: Since this appears to be a platform-level behavior, more significant architectural changes might be needed to ensure consistent character personas.

## Conclusion

This behavior presents both challenges and opportunities for our NPC AI system. While the caching can potentially reduce costs and latency, the hallucination with different player IDs requires careful handling to ensure consistent character personas.

The fact that this behavior persists across different models (Nova and Claude) strongly suggests it's a fundamental aspect of AWS Bedrock's platform design rather than a model-specific limitation.

We're continuing to investigate this behavior and will update documentation as we learn more about the optimal configurations for working with AWS Bedrock models.

## Next Steps

- Test with non-standard player IDs (e.g., "user123", "customer456") to see if the pattern persists
- Experiment with different models within AWS Bedrock
- Test if other parameters beyond temperature affect the caching behavior
- Develop a prompt structure that ensures consistent character identity regardless of player ID
- Create automated tests to detect identity hallucinations
- Investigate the correct API formats to ensure randomness parameters are properly passed
- Contact AWS Support to determine if this is expected platform behavior 