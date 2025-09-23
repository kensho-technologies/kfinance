# Dynamic Prompt Construction

This module implements **Query Time Prompt Construction**. It dynamically constructs prompts with query-specific examples and parameter descriptors to improve tool selection accuracy and reduce parameter disambiguation errors.

## Overview

The dynamic prompt construction system addresses key problems in the current tool calling implementation:

- **Parameter Disambiguation**: Helps LLMs choose correct parameters when multiple similar options exist (e.g., `preferred_stock_convertible` vs `convertible_preferred_stock`)
- **Token Efficiency**: Includes only relevant examples instead of all possible ones
- **Improved Accuracy**: Provides targeted examples and parameter guidance based on query similarity

## Architecture

```
dynamic_prompts/
├── __init__.py                    # Module exports
├── example_repository.py          # Storage and management of examples
├── similarity_search.py           # Cosine similarity search engine
├── prompt_constructor.py          # Dynamic prompt assembly
├── integration.py                 # Integration with existing system
├── demo.py                        # Demonstration script
├── evaluation.py                  # Evaluation framework
├── tool_examples/                 # JSON files with tool examples
│   └── get_financial_line_item_examples.json
└── parameter_descriptors/         # JSON files with parameter guidance
    └── get_financial_line_item_params.json
```

## Key Components

### ExampleRepository
- Loads tool usage examples from JSON files
- Computes embeddings using sentence transformers
- Manages parameter descriptors for disambiguation
- Supports permission-based filtering

### SimilaritySearchEngine
- Performs cosine similarity search on query embeddings
- Applies boosting for exact keyword matches
- Filters results by user permissions and available tools

### DynamicPromptConstructor
- Assembles prompts with relevant examples and parameter descriptors
- Respects token limits and example quotas per tool
- Formats examples with disambiguation notes

### Integration Layer
- Provides easy integration with existing tool calling pipeline
- Handles fallback to static prompts if dynamic construction fails
- Supports lazy initialization and caching

## Usage

### Basic Usage

```python
from kfinance.integrations.tool_calling.dynamic_prompts import construct_dynamic_prompt
from kfinance.client.permission_models import Permission

# Construct a dynamic prompt
user_permissions = {Permission.StatementsPermission}
query = "What is the preferred stock additional paid in capital for Apple?"

dynamic_prompt = construct_dynamic_prompt(
    query=query,
    user_permissions=user_permissions
)
```

### Precomputing Embeddings

For optimal performance, precompute embeddings before using the system:

```bash
# Precompute all embeddings
python -m kfinance.integrations.tool_calling.dynamic_prompts.cli precompute

# Force recomputation of all embeddings
python -m kfinance.integrations.tool_calling.dynamic_prompts.cli precompute --force

# Show cache statistics
python -m kfinance.integrations.tool_calling.dynamic_prompts.cli stats
```

### Advanced Usage

```python
from kfinance.integrations.tool_calling.dynamic_prompts import DynamicPromptManager

# Initialize manager with custom settings
manager = DynamicPromptManager(
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    enable_caching=True
)

# Get prompt with statistics
prompt, stats = manager.get_prompt_with_stats(
    query=query,
    user_permissions=user_permissions
)

print(f"Generated prompt with {stats['example_count']} examples")
print(f"Total tokens: ~{stats['total_words']}")

# Check cache statistics
cache_stats = manager.get_cache_stats()
print(f"Cache size: {cache_stats.get('cache_size_mb', 0)} MB")
print(f"Cached embeddings: {cache_stats.get('cached_embeddings', 0)}")
```

### Adding New Examples

```python
# Add example from successful query
manager.add_example_from_query(
    query="What is the convertible preferred stock for Tesla?",
    tool_name="get_financial_line_item_from_identifiers",
    parameters={"identifiers": ["TSLA"], "line_item": "preferred_stock_convertible"},
    context="Use 'preferred_stock_convertible' for preferred stock that can be converted to common stock.",
    permissions_required={Permission.StatementsPermission},
    disambiguation_note="Use 'preferred_stock_convertible' not 'convertible_preferred_stock'",
    tags=["preferred_stock", "convertible"]
)
```

## Example Format

Examples are stored in JSON files with the following structure:

```json
{
  "tool_name": "get_financial_line_item_from_identifiers",
  "examples": [
    {
      "query": "What is the preferred stock additional paid in capital for Apple?",
      "tool_name": "get_financial_line_item_from_identifiers",
      "parameters": {
        "identifiers": ["AAPL"],
        "line_item": "additional_paid_in_capital_preferred_stock"
      },
      "context": "Use 'additional_paid_in_capital_preferred_stock' for capital received from preferred stock issuance above par value.",
      "permissions_required": ["StatementsPermission"],
      "disambiguation_note": "Key difference: 'additional_paid_in_capital_preferred_stock' vs 'preferred_stock_additional_paid_in_capital' - the first follows standard accounting terminology.",
      "tags": ["preferred_stock", "capital", "disambiguation"]
    }
  ]
}
```

## Parameter Descriptors

Parameter descriptors provide enhanced guidance for disambiguation:

```json
{
  "tool_name": "get_financial_line_item_from_identifiers",
  "parameters": [
    {
      "parameter_name": "line_item",
      "description": "The specific financial line item to retrieve. Must match exact parameter names from the allowed list.",
      "examples": ["revenue", "total_revenue", "preferred_stock_convertible"],
      "common_mistakes": [
        "Using 'convertible_preferred_stock' instead of 'preferred_stock_convertible'",
        "Using 'total_debt_to_equity_ratio' instead of 'total_debt_to_equity'"
      ],
      "related_parameters": ["period_type", "start_year", "end_year"]
    }
  ]
}
```

## Evaluation

The module includes a comprehensive evaluation framework to test improvements:

```python
from kfinance.integrations.tool_calling.dynamic_prompts.evaluation import run_evaluation_suite

# Run evaluation on test cases
run_evaluation_suite()
```

The evaluation framework:
- Tests parameter disambiguation accuracy
- Measures prompt construction performance
- Compares static vs dynamic prompt effectiveness
- Generates detailed reports with metrics

## Demo

Run the demonstration script to see the system in action:

```python
from kfinance.integrations.tool_calling.dynamic_prompts.demo import (
    demo_dynamic_prompt_construction,
    demo_parameter_disambiguation,
    demo_permission_filtering
)

# Run all demonstrations
demo_dynamic_prompt_construction()
demo_parameter_disambiguation()
demo_permission_filtering()
```

## Benefits

### Improved Parameter Accuracy
- Addresses the eval failures mentioned in the design doc
- Provides targeted examples for confusing parameter pairs
- Includes disambiguation notes for common mistakes

### Token Efficiency
- Reduces prompt size by including only relevant examples
- Dynamically adjusts based on query content
- Respects token limits and example quotas

### Scalability
- Client-side processing with minimal latency impact
- Permission-based filtering ensures security
- Easy to add new examples and tools

### Maintainability
- Examples stored in human-readable JSON files
- Modular architecture with clear separation of concerns
- Comprehensive testing and evaluation framework

## Dependencies

- `sentence-transformers>=2.2.0,<3`: For embedding computation and similarity search
- `numpy>=1.22.4`: For numerical operations on embeddings
- `pydantic>=2.10.0,<3`: For data validation and serialization

## Future Enhancements

1. **Continuous Learning**: Automatically add successful queries as examples
2. **Multi-tool Examples**: Examples showing cross-tool interactions
3. **Personalization**: User-specific example preferences
4. **Performance Optimization**: Caching and indexing for large example repositories
5. **A/B Testing**: Framework for comparing different prompt strategies

## Integration with Existing System

The dynamic prompt constructor is designed to integrate seamlessly with the existing tool calling pipeline:

1. **Client Initialization**: Load example repository once per client
2. **Query Processing**: Intercept queries to construct dynamic prompts
3. **Fallback Handling**: Gracefully fall back to static prompts if needed
4. **Permission Enforcement**: Respect existing permission system

The system is backward compatible and can be enabled/disabled without affecting existing functionality.
