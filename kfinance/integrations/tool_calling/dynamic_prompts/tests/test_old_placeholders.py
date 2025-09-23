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
    
    print("OLD PLACEHOLDER CONVERSION TEST")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing Query:")
        print(f"   Original:   {query}")
        
        normalized, entity_mapping = normalizer.normalize_query(query)
        print(f"   Normalized: {normalized}")
        
        if entity_mapping:
            print(f"   Entities:   {entity_mapping}")
        else:
            print("   Entities:   None detected")

if __name__ == "__main__":
    main()
