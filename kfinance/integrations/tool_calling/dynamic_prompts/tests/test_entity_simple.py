"""Test script to demonstrate entity normalization concept."""

from entity_normalizer import EntityNormalizer


def main():
    """Test entity normalization functionality."""
    normalizer = EntityNormalizer()

    # Test queries with different entities
    test_queries = [
        "What is the revenue for Apple and Microsoft?",
        "Get Tesla's stock price for Q3 2023",
        "Show me JPMorgan's balance sheet",
        "Compare Amazon and Google's market cap",
        "What are the preferred dividends paid by Microsoft?",
        "Get quarterly revenue for Apple in Q1 2023"
    ]


    for i, query in enumerate(test_queries, 1):

        normalized, entity_mapping = normalizer.normalize_query(query)

        if entity_mapping:
            pass
        else:
            pass


    for placeholder in sorted(normalizer.get_placeholders()):
        pass

if __name__ == "__main__":
    main()
