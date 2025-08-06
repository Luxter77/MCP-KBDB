# RAG-MCP Manual: Adding New Modalities

This manual explains how to add new search modalities to the RAG-MCP system. Each modality represents a different way of embedding and searching documents, optimized for specific use cases.

## Overview

The system supports multiple search modalities through three main components:
1. **Model Configuration**: Defines how text is preprocessed and which distance metric to use
2. **Task Configuration**: Describes the purpose of the search modality
3. **MCP Tool Function**: Exposes the search capability to the agent

## Adding a New Modality

### Step 1: Define the Model Configuration

Add a new entry to the `MODELS` dictionary in `rag_mcp_server.py`:

```python
MODELS = {
    # ... existing models ...
    "your_new_modality": Model(
        model="your-modality-optimized-model",  # Specify the embedding model to use
        prefix="Your custom prefix: ",
        suffix="Your custom suffix",
        distance_metric="cosine"  # or "inner_product", "l2"
    )
}
```

**Parameters:**
- `model`: The specific embedding model to use (e.g., "nomic-embed-text:v1.5")
- `prefix`: Text prepended to the query before embedding (internal to the model)
- `suffix`: Text appended to the query before embedding (internal to the model)
- `distance_metric`: Distance metric for similarity comparison
  - `"cosine"`: Cosine similarity (default)
  - `"inner_product"`: Inner product similarity
  - `"l2"`: Euclidean distance

### Step 2: Define the Task Configuration

Add a new entry to the `TASKS` dictionary:

```python
TASKS = {
    # ... existing tasks ...
    "your_new_modality": Task(
        name="your_new_modality",
        description="Description of your new modality's purpose"
    )
}
```

**Parameters:**
- `name`: Must match the model name
- `description`: Human-readable description of the modality

### Step 3: Add the MCP Tool Function

Create a new MCP tool function that exposes the search capability:

```python
@mcp.tool
def search_your_new_modality(query: str, top_k: int = 3) -> str:
    """Description of your new modality search"""
    try:
        model = MODELS["your_new_modality"]
        task = TASKS["your_new_modality"]
        
        query_embedding = rag_server._get_embedding(query, model)
        results = rag_server._search_database(query_embedding, model, task, top_k)
        
        return rag_server._format_results(results)
    except Exception as e:
        logger.error(f"Your modality search failed: {e}")
        return f"Search failed: {str(e)}"
```

**Function Requirements:**
- Name must follow the pattern `search_{modality_name}`
- Must accept `query: str` and `top_k: int = 3` parameters
- Must return a formatted string with search results
- Must include proper error handling and logging

## Example: Adding a "Keyword" Modality

Here's a complete example of adding a keyword-based search modality:

```python
# Add to MODELS dictionary
"keyword": Model(
    model="your-keywords-model",
    prefix="",
    suffix="",
    distance_metric="inner_product"
)

# Add to TASKS dictionary
"keyword": Task(
    name="keyword",
    description="Search based on keyword extraction and matching"
)

# Add the MCP tool function
@mcp.tool
def search_keyword(query: str, top_k: int = 3) -> str:
    """Search based on keyword extraction and matching"""
    try:
        model = MODELS["keyword"]
        task = TASKS["keyword"]
        
        query_embedding = rag_server._get_embedding(query, model)
        results = rag_server._search_database(query_embedding, model, task, top_k)
        
        return rag_server._format_results(results)
    except Exception as e:
        logger.error(f"Keyword search failed: {e}")
        return f"Search failed: {str(e)}"
```

## Database Requirements

The database must contain embeddings for your new modality. The embeddings should be stored in the `embeddings` table with:
- `model`: Set to your modality name
- `task`: Set to your modality name
- `embedding`: The actual embedding vector

The system assumes that embeddings are pre-computed and stored in the database by external services.

## Distance Metrics

Choose the appropriate distance metric based on your use case:

- **Cosine Similarity** (`cosine`): Best for semantic similarity, direction-based comparison
- **Inner Product** (`inner_product`): Best for QA pairs, magnitude-sensitive comparison
- **L2 Distance** (`l2`): Best for geometric similarity, Euclidean distance

## Testing

After adding a new modality:

1. Ensure the database contains embeddings for your modality
2. Test the MCP tool function with sample queries
3. Verify that the results are relevant and properly formatted
4. Check logs for any errors or warnings

## Best Practices

1. **Keep prefixes/suffixes simple**: Complex preprocessing may reduce embedding quality
2. **Choose appropriate distance metrics**: Match the metric to your use case
3. **Use descriptive names**: Make modality names clear and intuitive
4. **Test thoroughly**: Ensure the new modality works as expected before deployment
5. **Document your changes**: Update this manual if you add new patterns or conventions