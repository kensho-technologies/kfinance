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
    
    print("ENTITY NORMALIZATION TEST")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print("\n{}. Testing Query:".format(i))
        print("   Original:   {}".format(query))
        
        normalized, entity_mapping = normalizer.normalize_query(query)
        print("   Normalized: {}".format(normalized))
        
        if entity_mapping:
            print("   Entities:   {}".format(entity_mapping))
        else:
            print("   Entities:   None detected")
    
    print("\n\nSUMMARY:")
    print("- Total placeholders available: {}".format(len(normalizer.get_placeholders())))
    print("- Total entity variations: {}".format(len(normalizer.get_common_entities())))
    
    print("\nAvailable placeholders:")
    for placeholder in sorted(normalizer.get_placeholders()):
        print("  {}".format(placeholder))

if __name__ == "__main__":
    main()
