# Player History Storage Design

## Current Implementation

The player history is currently implemented using a file-based JSON storage system through the `ConversationManager` class. Each player's history is stored in a separate JSON file, with in-memory caching for performance.

### Current Approach
- Storage: Individual JSON files per player
- Location: `src/data/conversations/` (configurable via the `storage_dir` parameter)
- Format: `{player_id}.json`
- Caching: In-memory dictionary `player_histories` with disk persistence
- Access Pattern: Lazy loading on first access, async writes on update
- Adapter Pattern: `DefaultConversationHistoryAdapter` for format conversion

### JSON Schema Structure
```json
{
  "player_id": "unique_player_identifier",
  "conversations": {
    "conversation_id_1": {
      "entries": [
        {
          "timestamp": "2023-07-01T12:34:56.789",
          "user_query": "Original user message",
          "response": "NPC response text",
          "user": "Original user message",
          "assistant": "NPC response text",
          "npc_id": "identifier_for_npc",
          "player_id": "player_identifier",
          "session_id": "optional_session_id",
          "metadata": {
            "optional_field1": "value1",
            "optional_field2": "value2"
          },
          "conversation_id": "conversation_id_1"
        }
        // Additional conversation entries...
      ]
    },
    // Additional conversations...
  }
}
```

### Advantages of Current Implementation
1. Simple to implement and debug
2. Human-readable data format
3. No external dependencies
4. Easy to backup and restore
5. Suitable for prototyping and development
6. Direct file system access for debugging
7. Supports multiple conversations per player
8. Standardized format adapters for flexibility

### Limitations
1. Not optimized for scale (many users)
2. No built-in indexing
3. Potential I/O bottlenecks with async disk writes
4. Limited concurrent access guarantees
5. No ACID properties
6. File system constraints
7. No built-in cleanup mechanism for old conversations
8. No resource management (e.g., closing file handles)

## Future Considerations

### Database Migration
When scaling becomes necessary, migration to a proper database system should be considered:

1. **Options**:
   - SQLite: For simple deployments
   - PostgreSQL: For production deployments
   - MongoDB: For maintaining JSON-like structure

2. **Benefits**:
   - Better concurrency handling
   - ACID compliance
   - Proper indexing
   - Query capabilities
   - Transaction support
   - Better performance at scale

### Resource Management Improvements

For the current file-based implementation, resource management could be improved by:

1. Adding a `close()` method to `ConversationManager` to:
   - Flush pending writes
   - Close file handles
   - Release resources properly during shutdown

2. Implementing a caching strategy with:
   - TTL for cached entries
   - Memory usage limits
   - LRU eviction policy

### Vector Storage Potential

The conversation history data could be valuable for advanced features through vector storage:

1. **Use Cases**:
   - Semantic search across conversation history
   - Finding similar conversations/patterns
   - Enhanced context building
   - Model training and fine-tuning

2. **Architecture Consideration**:
   - Primary storage (DB) for raw history (source of truth)
   - Vector storage for semantic features (derived data)
   - Synchronization mechanism between the two

## Recommended Path Forward

### Short Term (Current)
1. **Maintain File-Based Storage**
   - Continue using JSON files for simplicity
   - Focus on core functionality
   - Suitable for current development phase

2. **Design for Future**
   - Abstract storage behind interfaces
   - Implement repository pattern
   - Make storage backend pluggable
   - Document storage format and schema

3. **Resource Management**
   - Add `close()` method to `ConversationManager`
   - Implement proper shutdown sequence
   - Add cleanup utilities for old/unused data

### Medium Term
1. **Database Migration**
   - Move to SQLite as intermediate step
   - Then PostgreSQL for production
   - Keep JSON as export/backup format
   - Implement proper migration tools

### Long Term
1. **Advanced Features**
   - Add vector storage capabilities
   - Implement event-based synchronization
   - Enhanced semantic search
   - Analytics and insights

## Decision

For the current phase of development, we will:
1. Keep the file-based JSON storage
2. Focus on implementing proper tests
3. Document the storage format
4. Design interfaces for future abstraction
5. Add resource management capabilities

This decision allows us to:
- Move quickly in development
- Maintain simplicity
- Defer complexity until needed
- Plan for future scaling
- Ensure proper resource cleanup

## Next Steps

1. Implement comprehensive tests for current implementation
2. Document JSON schema and storage format
3. Create interfaces for storage abstraction
4. Add a `close()` method to `ConversationManager` for proper resource management
5. Monitor performance and usage patterns
6. Identify trigger points for migration

## Future Migration Triggers

Consider migration when:
1. Number of users exceeds 1000
2. File I/O becomes a bottleneck
3. Concurrent access issues arise
4. Need for complex queries emerges
5. ACID properties become critical 