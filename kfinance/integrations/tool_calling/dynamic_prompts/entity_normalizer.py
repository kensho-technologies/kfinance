# -*- coding: utf-8 -*-
"""Entity normalization for reducing entity bias in semantic search."""

import re
from typing import Dict, List, Tuple, Set
from pathlib import Path
import json
import logging

from .entity_tagger import EntityTagger

logger = logging.getLogger(__name__)


class EntityNormalizer:
    """Normalizes entities in queries and examples to reduce semantic search bias using NER."""
    
    def __init__(self):
        """Initialize the entity normalizer with NER-based entity detection."""
        # Initialize the advanced entity tagger
        self.entity_tagger = EntityTagger()
        
        # Keep legacy company patterns for backward compatibility with existing placeholders
        self.legacy_company_patterns = {
            # Tech companies
            "apple": ["apple", "aapl", "apple inc", "apple computer"],
            "microsoft": ["microsoft", "msft", "microsoft corp", "microsoft corporation"],
            "google": ["google", "googl", "alphabet", "alphabet inc"],
            "amazon": ["amazon", "amzn", "amazon.com", "amazon inc"],
            "meta": ["meta", "facebook", "fb", "meta platforms"],
            "tesla": ["tesla", "tsla", "tesla inc", "tesla motors"],
            "netflix": ["netflix", "nflx", "netflix inc"],
            
            # Financial companies
            "jpmorgan": ["jpmorgan", "jpm", "jp morgan", "jpmorgan chase", "jp morgan chase"],
            "bank_of_america": ["bank of america", "bac", "bofa", "bank of america corp"],
            "wells_fargo": ["wells fargo", "wfc", "wells fargo & company"],
            "goldman_sachs": ["goldman sachs", "gs", "goldman", "goldman sachs group"],
            
            # Other major companies
            "walmart": ["walmart", "wmt", "wal-mart", "walmart inc"],
            "coca_cola": ["coca-cola", "ko", "coca cola", "coke", "the coca-cola company"],
            "ford": ["ford", "f", "ford motor", "ford motor company"],
            "general_electric": ["general electric", "ge", "ge company"],
            "exxon": ["exxon", "xom", "exxon mobil", "exxonmobil"],
            "pfizer": ["pfizer", "pfe", "pfizer inc"],
            
            # International companies
            "toyota": ["toyota", "tm", "toyota motor"],
            "samsung": ["samsung", "005930.ks", "samsung electronics"],
            "nestle": ["nestle", "nsrgy", "nestle sa"],
        }
        
        # Create reverse mapping for legacy patterns (for backward compatibility)
        self.legacy_entity_to_placeholder = {}
        self.legacy_placeholder_to_entities = {}
        
        # Create generic placeholders (COMPANY_A, COMPANY_B, etc.) for legacy patterns
        placeholder_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T']
        
        for i, (placeholder, variations) in enumerate(self.legacy_company_patterns.items()):
            if i < len(placeholder_letters):
                placeholder_key = f"<COMPANY_{placeholder_letters[i]}>"
                self.legacy_placeholder_to_entities[placeholder_key] = variations
                for variation in variations:
                    self.legacy_entity_to_placeholder[variation.lower()] = placeholder_key
    
    def normalize_query(self, query: str) -> Tuple[str, Dict[str, str]]:
        """
        Normalize entities in a query to placeholders using advanced NER.
        
        Args:
            query: Original query string
            
        Returns:
            Tuple of (normalized_query, entity_mapping)
        """
        # First, handle existing old-style placeholders (convert them to new format)
        normalized_query = query.lower()
        entity_mapping = {}
        
        old_placeholder_pattern = r'<company_(\w+)>'
        old_placeholders = re.findall(old_placeholder_pattern, normalized_query)
        for old_company_name in old_placeholders:
            # Find the new placeholder for this company using legacy patterns
            if old_company_name in self.legacy_entity_to_placeholder:
                new_placeholder = self.legacy_entity_to_placeholder[old_company_name]
                old_pattern = f'<company_{old_company_name}>'
                normalized_query = normalized_query.replace(old_pattern, new_placeholder.lower())
                entity_mapping[new_placeholder] = old_company_name
        
        # If no old placeholders found, use the advanced entity tagger
        if not old_placeholders:
            try:
                normalized_query, entity_mapping = self.entity_tagger.normalize_text(query)
            except Exception as e:
                logger.error(f"Error in entity tagger, falling back to legacy method: {e}")
                # Fallback to legacy method
                return self._normalize_query_legacy(query)
        
        return normalized_query, entity_mapping
    
    def _normalize_query_legacy(self, query: str) -> Tuple[str, Dict[str, str]]:
        """Legacy normalization method as fallback."""
        normalized_query = query.lower()
        entity_mapping = {}
        
        # Use legacy entity patterns
        sorted_entities = sorted(self.legacy_entity_to_placeholder.items(), 
                               key=lambda x: len(x[0]), reverse=True)
        
        for entity, placeholder in sorted_entities:
            pattern = r'\b' + re.escape(entity) + r'\b'
            if re.search(pattern, normalized_query, re.IGNORECASE):
                normalized_query = re.sub(pattern, placeholder.lower(), normalized_query, flags=re.IGNORECASE)
                entity_mapping[placeholder] = entity
        
        return normalized_query, entity_mapping
    
    def denormalize_query(self, normalized_query: str, entity_mapping: Dict[str, str]) -> str:
        """
        Convert normalized query back to original entities.
        
        Args:
            normalized_query: Query with placeholders
            entity_mapping: Mapping from placeholders to original entities
            
        Returns:
            Query with original entities restored
        """
        denormalized = normalized_query
        for placeholder, original_entity in entity_mapping.items():
            denormalized = denormalized.replace(placeholder, original_entity)
        return denormalized
    
    def normalize_examples_in_file(self, file_path: Path) -> None:
        """
        Normalize entities in an examples file.
        
        Args:
            file_path: Path to the examples JSON file
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Handle different file structures
            examples = []
            if 'examples' in data:
                examples = data['examples']
            elif 'tools' in data:
                # Multi-tool file structure
                for tool in data['tools']:
                    if 'examples' in tool:
                        examples.extend(tool['examples'])
            
            # Normalize each example
            for example in examples:
                if 'query' in example:
                    normalized_query, _ = self.normalize_query(example['query'])
                    example['query'] = normalized_query
                
                if 'context' in example:
                    normalized_context, _ = self.normalize_query(example['context'])
                    example['context'] = normalized_context
                
                if 'disambiguation_note' in example:
                    normalized_note, _ = self.normalize_query(example['disambiguation_note'])
                    example['disambiguation_note'] = normalized_note
            
            # Write back the normalized file
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Normalized entities in {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to normalize entities in {file_path}: {e}")
    
    def get_common_entities(self) -> Set[str]:
        """Get set of all common entity variations for testing."""
        entities = set()
        for variations in self.legacy_company_patterns.values():
            entities.update(variations)
        return entities
    
    def get_placeholders(self) -> Set[str]:
        """Get set of all placeholders."""
        return set(self.legacy_placeholder_to_entities.keys())


def normalize_all_examples(examples_dir: Path) -> None:
    """
    Normalize entities in all example files in a directory.
    
    Args:
        examples_dir: Directory containing example JSON files
    """
    normalizer = EntityNormalizer()
    
    for json_file in examples_dir.glob("*.json"):
        normalizer.normalize_examples_in_file(json_file)
    
    logger.info(f"Completed entity normalization for all files in {examples_dir}")


if __name__ == "__main__":
    # Test the normalizer
    normalizer = EntityNormalizer()
    
    test_queries = [
        "What is the revenue for Apple and Microsoft?",
        "Get Tesla's stock price",
        "Show me JPMorgan's balance sheet",
        "Compare Amazon and Google's market cap"
    ]
    
    for query in test_queries:
        normalized, mapping = normalizer.normalize_query(query)
        print(f"Original: {query}")
        print(f"Normalized: {normalized}")
        print(f"Mapping: {mapping}")
        print()
