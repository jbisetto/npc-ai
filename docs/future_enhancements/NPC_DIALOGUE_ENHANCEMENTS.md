# Enhancing NPC Dialogue Boundaries for Language Learning Games

## Current Challenges and Analysis

As a senior developer with AI expertise, I've identified several critical issues with our current NPC dialogue system that pose risks to the educational integrity and immersion of our language learning game:

### 1. Knowledge Boundary Problems

The current implementation of the `NPCProfile` system lacks proper boundaries to constrain LLM responses to our game world. The `get_system_prompt()` method in `src/ai/npc/core/profile/profile.py` is notably simplistic:

```python
def get_system_prompt(self) -> str:
    prompt = f"""You are {self.name}, a {self.role}. {self.backstory}

Your personality traits are:
"""
    for trait, value in self.personality_traits.items():
        prompt += f"- {trait}: {value}\n"
        
    prompt += f"\nYou are knowledgeable about: {', '.join(self.knowledge_areas)}"
    
    return prompt
```

This implementation has several shortcomings:
- It fails to explicitly prohibit the LLM from generating responses outside the game world
- The "knowledge_areas" are vague and insufficiently tied to concrete game assets
- There's no mechanism to enforce JLPT N5 constraints for Japanese language use
- Nothing prevents the model from generating fictional information about Tokyo or Japanese culture

### 2. Knowledge Representation Issues

The current knowledge areas in NPC profiles are general and disconnected from the actual knowledge base:

```json
"knowledge_areas": [
  "Japanese language",
  "Japanese culture",
  "Daily life in Japan",
  "Basic conversation"
]
```

These knowledge areas:
- Are too broad and subjective
- Don't correspond to specific entries in our knowledge base
- Allow the LLM to "hallucinate" plausible but incorrect information
- Provide no clear boundaries between what NPCs should and shouldn't know

### 3. Contextual Knowledge Retrieval Limitations

Our current contextual search function doesn't give special weight to knowledge items relevant to an NPC's profile or role. This leads to:
- Inconsistent NPC responses
- NPCs sometimes "knowing" information outside their character
- Responses that transcend the intended game world boundaries
- Insufficient grounding in our curated game knowledge

## Proposed Enhancements

I propose a comprehensive approach to reinforce the boundaries of our game world and ensure NPCs remain within character, using appropriate Japanese language levels:

### 1. Enhanced System Prompt with Explicit Boundaries

Modify the `get_system_prompt()` method to include explicit guardrails:

```python
def get_system_prompt(self) -> str:
    """Generate the system prompt for this NPC."""
    prompt = f"""You are {self.name}, a {self.role}. {self.backstory}

Your personality traits are:
"""
    for trait, value in self.personality_traits.items():
        prompt += f"- {trait}: {value}\n"
        
    prompt += f"\nYou are knowledgeable about: {', '.join(self.knowledge_areas)}"
    
    # Add explicit boundary statements
    prompt += """

IMPORTANT: You only exist within this game world set in Tokyo Station. You cannot discuss:
1. Real-world events or news
2. Any locations outside of Tokyo Station
3. Topics not related to train station activities or basic Japanese language
4. Advanced Japanese beyond JLPT N5 level
5. Personal opinions on politics, religion, or controversial topics

If asked about something outside your knowledge areas, politely redirect the conversation back to topics within the game world."""
    
    return prompt
```

This enhancement explicitly constrains the LLM to our game world, setting clear boundaries about what the NPC can discuss.

### 2. Game-Specific Knowledge Areas

Update the knowledge areas in all profiles to directly reference entries in our knowledge base:

```json
"knowledge_areas": [
  "Tokyo Train Station Overview",
  "JLPT N5 Station Vocabulary",
  "Essential Station Phrases",
  "Tokyo Station Layout and Navigation"
]
```

This ties NPC knowledge to concrete game content and prevents fabrication of information.

### 3. Boundary-Reinforcing Backstories

Modify NPC backstories to emphasize their limited knowledge scope:

```json
"backstory": "A station staff member at Tokyo Station who only knows information about the game's station layout, train schedules, and ticket procedures. Cannot provide information about anything outside the game world."
```

These explicit limitations in the character description help maintain NPC consistency.

### 4. Knowledge Retrieval Enhancement (Future Work)

For a more comprehensive solution, I recommend enhancing the `contextual_search` method in our `KnowledgeStore` implementation to:
1. Prioritize knowledge entries that match an NPC's knowledge areas
2. Apply higher relevance scores to entries aligned with the NPC's role
3. Implement a filtering mechanism that excludes knowledge outside an NPC's domain

## Implementation Plan

1. **Immediate Tasks:**
   - Update all NPC profile JSONs with game-specific knowledge areas
   - Modify backstories to reinforce knowledge boundaries
   - Update the `NPCProfile.get_system_prompt()` method to include boundary statements

2. **Testing:**
   - Conduct comprehensive testing with diverse user queries to evaluate containment
   - Test edge cases that attempt to extract real-world information
   - Verify Japanese language level stays within JLPT N5 constraints

3. **Future Enhancements:**
   - Implement knowledge retrieval weighting based on NPC profiles
   - Add real-time monitoring for out-of-bounds responses
   - Develop runtime constraints that can filter potentially problematic content

## Expected Outcomes

These enhancements will:
1. Create a more cohesive, bounded game world
2. Ensure NPCs remain in character and provide consistent information
3. Maintain appropriate Japanese language difficulty levels
4. Reduce the risk of LLM hallucinations or inappropriate content
5. Improve the educational value of NPC interactions

By implementing these changes, we'll significantly improve the quality and consistency of our language learning game while maintaining the immersive experience critical for effective learning.
