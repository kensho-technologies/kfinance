"""Test script to verify old placeholder conversion."""

from entity_normalizer import EntityNormalizer


def main():
    """Test old placeholder conversion."""
    normalizer = EntityNormalizer()

    # Test queries with old-style placeholders
    test_queries = [
        "what m&a activity has <company_pfizer> been involved in?",
        "what are the previous borrowers of <company_jpmorgan>?",
        "show me <company_tesla>'s stock price",
        "get <company_apple> and <company_microsoft> revenue"
    ]


    for i, query in enumerate(test_queries, 1):

        normalized, entity_mapping = normalizer.normalize_query(query)

        if entity_mapping:
            pass
        else:
            pass

if __name__ == "__main__":
    main()
