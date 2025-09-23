#!/usr/bin/env python3
"""Script to update all examples with entity normalization and permission references."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from entity_normalizer import EntityNormalizer
from permission_resolver import PermissionResolver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_example_permissions(example: Dict[str, Any], permission_resolver: PermissionResolver) -> Dict[str, Any]:
    """Update example permissions to use reference strings."""
    if 'permissions_required' not in example:
        return example
    
    # Map current permission values to reference strings
    permission_mapping = {
        "StatementsPermission": "STATEMENTS",
        "PricingPermission": "PRICING", 
        "EarningsPermission": "EARNINGS",
        "MergersPermission": "MERGERS",
        "CompanyIntelligencePermission": "COMPANY_INTELLIGENCE",
        "RelationshipPermission": "RELATIONSHIPS",
        "SegmentsPermission": "SEGMENTS",
        "IDPermission": "ID",
        "CompetitorsPermission": "COMPETITORS",
        "TranscriptsPermission": "TRANSCRIPTS"
    }
    
    updated_permissions = []
    for perm in example['permissions_required']:
        if perm in permission_mapping:
            updated_permissions.append(permission_mapping[perm])
        else:
            logger.warning(f"Unknown permission: {perm}")
            updated_permissions.append(perm)
    
    example['permissions_required'] = updated_permissions
    return example


def update_examples_file(file_path: Path) -> None:
    """Update a single examples file with normalization and permission updates."""
    logger.info(f"Updating {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        normalizer = EntityNormalizer()
        permission_resolver = PermissionResolver()
        
        # Handle different file structures
        examples_to_update = []
        
        if 'examples' in data:
            # Single tool file
            examples_to_update = data['examples']
        elif 'tools' in data:
            # Multi-tool file
            for tool in data['tools']:
                if 'examples' in tool:
                    examples_to_update.extend(tool['examples'])
        
        # Update each example
        for example in examples_to_update:
            # Normalize entities in text fields
            if 'query' in example:
                normalized_query, _ = normalizer.normalize_query(example['query'])
                example['query'] = normalized_query
            
            if 'context' in example:
                normalized_context, _ = normalizer.normalize_query(example['context'])
                example['context'] = normalized_context
            
            if 'disambiguation_note' in example:
                normalized_note, _ = normalizer.normalize_query(example['disambiguation_note'])
                example['disambiguation_note'] = normalized_note
            
            # Update permissions to use reference strings
            example = update_example_permissions(example, permission_resolver)
        
        # Write back the updated file
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Successfully updated {file_path}")
        
    except Exception as e:
        logger.error(f"Failed to update {file_path}: {e}")


def main():
    """Update all example files in the tool_examples directory."""
    examples_dir = Path(__file__).parent / "tool_examples"
    
    if not examples_dir.exists():
        logger.error(f"Examples directory not found: {examples_dir}")
        return
    
    # Update all JSON files
    json_files = list(examples_dir.glob("*.json"))
    logger.info(f"Found {len(json_files)} example files to update")
    
    for json_file in json_files:
        update_examples_file(json_file)
    
    logger.info("Completed updating all example files")
    
    # Show some example normalizations
    normalizer = EntityNormalizer()
    test_queries = [
        "What is the revenue for Apple and Microsoft?",
        "Get Tesla's stock price for Q3 2023",
        "Show me JPMorgan's balance sheet",
        "Compare Amazon and Google's market cap"
    ]
    
    print("\n" + "="*60)
    print("EXAMPLE ENTITY NORMALIZATIONS")
    print("="*60)
    
    for query in test_queries:
        normalized, mapping = normalizer.normalize_query(query)
        print(f"\nOriginal:   {query}")
        print(f"Normalized: {normalized}")
        if mapping:
            print(f"Entities:   {mapping}")


if __name__ == "__main__":
    main()
