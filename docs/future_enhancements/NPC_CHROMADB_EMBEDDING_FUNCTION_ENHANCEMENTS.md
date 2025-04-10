# ChromaDB Embedding Function Issues

## Summary
The current implementation of `TokyoKnowledgeStore` has issues with the embedding function, falling back to a `DummyEmbeddingFunction` that returns random vectors. This causes vector search to be essentially random and not based on actual semantic similarity.

## Identified Issues

1. **Fallback to Random Embeddings**: When the main embedding function fails, the system falls back to `DummyEmbeddingFunction` which returns random 384-dimensional vectors.

2. **Silent Failure Handling**: The main embedding function failure is logged as a warning but the system continues with random vectors, masking the underlying issue.

3. **Poor Search Results**: With random embeddings, search results have no semantic relevance to queries.

4. **Inconsistent Results**: Random embeddings will give different results on each run, creating unpredictable behavior.

## Proposed Solutions

1. **Use ChromaDB's Built-in Embedding Functions**:
   ```python
   from chromadb.utils import embedding_functions
   self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
   ```

2. **Fail Explicitly**: Instead of silently falling back to a dummy function, throw a clear error during initialization if the embedding model can't be loaded.

3. **Verify Embedding Dimensions**: Ensure the embedding dimensions match what ChromaDB expects (384 for the MiniLM model).

4. **Add Explicit Dependency Installation**: Create a separate script that installs the required sentence-transformers package.

5. **Implement a Simplified but Meaningful Embedding Function**: Instead of random vectors, use a simpler but still meaningful approach like TF-IDF or Bag-of-Words if the main model fails.

## Required Changes

1. Remove `DummyEmbeddingFunction` class
2. Update the error handling in `TokyoKnowledgeStore.__init__` method
3. Use ChromaDB's built-in embedding functions directly
4. Add proper dependency checking
5. Implement explicit error messages if embeddings can't be generated

## Related Files
- `/src/ai/npc/core/vector/tokyo_knowledge_store.py` - Main implementation with DummyEmbeddingFunction
- `/initialize_knowledge_base.py` - Script that initializes the knowledge base

## Priority
Medium - Address after fixing conversation history issues. 