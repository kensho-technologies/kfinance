# -*- coding: utf-8 -*-
"""Entity tagging system using NER for comprehensive company detection."""

import re
import logging
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try to import spaCy for NER, with fallback
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available - falling back to pattern-based entity detection")


@dataclass
class EntityMatch:
    """Represents a detected entity match."""
    text: str
    start: int
    end: int
    entity_type: str
    placeholder: str


class EntityTagger:
    """Advanced entity tagger using NER and pattern matching for comprehensive company detection."""
    
    def __init__(self):
        """Initialize the entity tagger."""
        self.nlp = None
        self._init_spacy_model()
    
    def _init_spacy_model(self):
        """Initialize spaCy NER model if available."""
        if not SPACY_AVAILABLE:
            return
        
        try:
            # Try to load English model
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy English model for NER")
        except OSError:
            try:
                # Fallback to smaller model
                self.nlp = spacy.load("en_core_web_md")
                logger.info("Loaded spaCy medium English model for NER")
            except OSError:
                logger.warning("No spaCy English model found - using pattern-based detection only")
                self.nlp = None
    
    def detect_entities(self, text: str) -> List[EntityMatch]:
        """
        Detect company entities in text using spaCy NER only.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of detected entity matches (empty if spaCy not available)
        """
        entities = []
        
        # Only use spaCy NER if available
        if self.nlp:
            entities = self._detect_with_spacy(text)
            # Remove duplicates and overlaps
            entities = self._deduplicate_entities(entities)
        
        return entities
    
    def _detect_with_spacy(self, text: str) -> List[EntityMatch]:
        """Detect entities using spaCy NER."""
        entities = []
        
        try:
            doc = self.nlp(text)
            
            # Count entities by type for placeholder numbering
            entity_counts = {"COMPANY": 0, "GPE": 0, "PERSON": 0}
            
            for ent in doc.ents:
                cleaned_text = self._clean_entity_text(ent.text)
                if not cleaned_text:
                    continue
                
                placeholder = None
                entity_type = None
                
                # Handle different entity types
                if ent.label_ == "ORG":
                    # Organizations - filter for likely companies and exclude geographic terms
                    if self._is_likely_company(cleaned_text) and not self._is_geographic_entity(cleaned_text):
                        entity_counts["COMPANY"] += 1
                        placeholder = f"<COMPANY_{chr(64 + entity_counts['COMPANY'])}>"  # A, B, C, etc.
                        entity_type = "COMPANY_NER"
                
                elif ent.label_ == "GPE":
                    # Geo-political entities (countries, cities, states)
                    entity_counts["GPE"] += 1
                    placeholder = f"<GPE_{chr(64 + entity_counts['GPE'])}>"  # A, B, C, etc.
                    entity_type = "GPE_NER"
                
                elif ent.label_ == "PERSON":
                    # Person names (CEOs, executives, etc.)
                    entity_counts["PERSON"] += 1
                    placeholder = f"<PERSON_{chr(64 + entity_counts['PERSON'])}>"  # A, B, C, etc.
                    entity_type = "PERSON_NER"
                
                # Add entity if we created a placeholder
                if placeholder and entity_type:
                    entities.append(EntityMatch(
                        text=cleaned_text,
                        start=ent.start_char,
                        end=ent.end_char,
                        entity_type=entity_type,
                        placeholder=placeholder
                    ))
        except Exception as e:
            logger.error(f"Error in spaCy NER: {e}")
        
        return entities
    
    def _clean_entity_text(self, text: str) -> str:
        """Clean entity text by removing common prefixes and normalizing."""
        cleaned = text.strip()
        
        # Remove common prefixes that shouldn't be part of company names
        prefixes_to_remove = [
            'compare ', 'get ', 'show ', 'what ', 'how ', 'when ', 'where ', 'why ',
            'find ', 'search ', 'look ', 'see ', 'view ', 'display ', 'list ',
            'tell ', 'give ', 'provide ', 'fetch ', 'retrieve ', 'obtain '
        ]
        
        cleaned_lower = cleaned.lower()
        for prefix in prefixes_to_remove:
            if cleaned_lower.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                break
        
        # Remove trailing punctuation
        cleaned = cleaned.rstrip('.,!?;:')
        
        return cleaned
    
    def _is_likely_company(self, text: str) -> bool:
        """Determine if detected entity is likely a company."""
        text_lower = text.lower()
        
        # Company indicators
        company_indicators = [
            'inc', 'corp', 'corporation', 'company', 'ltd', 'limited', 'llc', 'plc',
            'technologies', 'systems', 'solutions', 'services', 'group', 'holdings',
            'bank', 'financial', 'capital', 'investment', 'fund', 'insurance',
            'pharmaceutical', 'biotech', 'energy', 'oil', 'gas', 'mining',
            'automotive', 'motors', 'airlines', 'airways', 'communications',
            'media', 'entertainment', 'studios', 'networks', 'broadcasting'
        ]
        
        # Check if contains company indicators
        for indicator in company_indicators:
            if indicator in text_lower:
                return True
        
        # Check if it's a known ticker pattern (2-5 uppercase letters)
        if re.match(r'^[A-Z]{2,5}$', text):
            return True
        
        # Check if it's a well-known company name (expanded list)
        known_companies = {
            # Tech companies
            'apple', 'microsoft', 'google', 'alphabet', 'amazon', 'meta', 'facebook', 
            'tesla', 'netflix', 'nvidia', 'intel', 'cisco', 'oracle', 'salesforce',
            'adobe', 'paypal', 'uber', 'lyft', 'airbnb', 'zoom', 'slack', 'shopify',
            'spotify', 'twitter', 'snap', 'pinterest', 'reddit', 'palantir', 'snowflake',
            
            # Traditional companies
            'walmart', 'disney', 'nike', 'mcdonald', 'starbucks', 'boeing', 'caterpillar',
            'ford', 'general motors', 'general electric', 'ibm', 'hp', 'dell', 'xerox',
            
            # Financial companies
            'jpmorgan', 'goldman sachs', 'morgan stanley', 'bank of america', 'wells fargo',
            'citigroup', 'visa', 'mastercard', 'american express', 'berkshire hathaway',
            
            # International companies
            'samsung', 'toyota', 'sony', 'nintendo', 'softbank', 'alibaba', 'tencent',
            'tsmc', 'asml', 'nestle', 'unilever', 'lvmh', 'sap', 'siemens', 'volkswagen',
            
            # Healthcare & Pharma
            'johnson & johnson', 'pfizer', 'merck', 'abbott', 'bristol myers squibb',
            'eli lilly', 'novartis', 'roche', 'astrazeneca', 'glaxosmithkline',
            
            # Energy & Commodities
            'exxon mobil', 'chevron', 'conocophillips', 'bp', 'shell', 'total',
            'saudi aramco', 'gazprom', 'petrobras'
        }
        
        return any(company in text_lower for company in known_companies)
    
    def _is_geographic_entity(self, text: str) -> bool:
        """Determine if detected entity is a geographic location, not a company."""
        text_lower = text.lower().strip()
        
        # Common geographic terms that should not be treated as companies
        geographic_terms = {
            # Countries
            'us', 'usa', 'united states', 'america', 'uk', 'united kingdom', 'canada', 
            'china', 'japan', 'germany', 'france', 'italy', 'spain', 'russia', 'india',
            'brazil', 'mexico', 'australia', 'south korea', 'netherlands', 'switzerland',
            
            # US States
            'california', 'new york', 'texas', 'florida', 'illinois', 'pennsylvania',
            'ohio', 'georgia', 'north carolina', 'michigan', 'new jersey', 'virginia',
            'washington', 'arizona', 'massachusetts', 'tennessee', 'indiana', 'missouri',
            'maryland', 'wisconsin', 'colorado', 'minnesota', 'south carolina', 'alabama',
            
            # Major cities
            'new york city', 'los angeles', 'chicago', 'houston', 'phoenix', 'philadelphia',
            'san antonio', 'san diego', 'dallas', 'san jose', 'austin', 'jacksonville',
            'san francisco', 'columbus', 'charlotte', 'fort worth', 'detroit', 'el paso',
            'memphis', 'seattle', 'denver', 'washington dc', 'boston', 'nashville',
            'baltimore', 'oklahoma city', 'portland', 'las vegas', 'milwaukee', 'albuquerque',
            
            # International cities
            'london', 'paris', 'tokyo', 'beijing', 'shanghai', 'mumbai', 'delhi', 'sydney',
            'toronto', 'vancouver', 'berlin', 'munich', 'zurich', 'geneva', 'amsterdam',
            'stockholm', 'copenhagen', 'oslo', 'helsinki', 'dublin', 'madrid', 'barcelona',
            'rome', 'milan', 'moscow', 'st petersburg', 'hong kong', 'singapore', 'seoul',
            
            # Regions/Continents
            'europe', 'asia', 'north america', 'south america', 'africa', 'oceania',
            'middle east', 'latin america', 'caribbean', 'scandinavia', 'balkans',
            'eastern europe', 'western europe', 'southeast asia', 'east asia', 'south asia'
        }
        
        # Check exact matches and common variations
        if text_lower in geographic_terms:
            return True
            
        # Check for possessive forms (e.g., "US's" -> "us")
        if text_lower.endswith("'s") and text_lower[:-2] in geographic_terms:
            return True
            
        # Check for common geographic suffixes that indicate places, not companies
        geographic_suffixes = ['city', 'state', 'country', 'region', 'province', 'territory']
        for suffix in geographic_suffixes:
            if text_lower.endswith(f' {suffix}'):
                return True
        
        return False
    
    def _deduplicate_entities(self, entities: List[EntityMatch]) -> List[EntityMatch]:
        """Remove duplicate and overlapping entities."""
        if not entities:
            return entities
        
        # Sort by start position
        entities.sort(key=lambda x: x.start)
        
        deduplicated = []
        for entity in entities:
            # Check for overlap with existing entities
            overlaps = False
            for existing in deduplicated:
                if (entity.start < existing.end and entity.end > existing.start):
                    # Overlapping entities - keep the longer one
                    if len(entity.text) > len(existing.text):
                        deduplicated.remove(existing)
                        break
                    else:
                        overlaps = True
                        break
            
            if not overlaps:
                deduplicated.append(entity)
        
        # Reassign placeholder numbers sequentially by type
        entity_counts = {"COMPANY": 0, "GPE": 0, "PERSON": 0}
        
        for entity in deduplicated:
            if entity.entity_type == "COMPANY_NER":
                entity_counts["COMPANY"] += 1
                entity.placeholder = f"<COMPANY_{chr(64 + entity_counts['COMPANY'])}>"
            elif entity.entity_type == "GPE_NER":
                entity_counts["GPE"] += 1
                entity.placeholder = f"<GPE_{chr(64 + entity_counts['GPE'])}>"
            elif entity.entity_type == "PERSON_NER":
                entity_counts["PERSON"] += 1
                entity.placeholder = f"<PERSON_{chr(64 + entity_counts['PERSON'])}>"
        
        return deduplicated
    
    def normalize_text(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Normalize text by replacing detected entities with placeholders.
        If spaCy is not available, returns text as-is with no entity masking.
        
        Args:
            text: Input text
            
        Returns:
            Tuple of (normalized_text, entity_mapping)
        """
        # If no spaCy model available, return text as-is (no entity masking)
        if not self.nlp:
            return text.lower(), {}
        
        entities = self.detect_entities(text)
        
        if not entities:
            return text.lower(), {}
        
        # Sort entities by start position (reverse order for replacement)
        entities.sort(key=lambda x: x.start, reverse=True)
        
        normalized_text = text
        entity_mapping = {}
        
        # Replace entities with placeholders (reverse order to preserve positions)
        for entity in entities:
            normalized_text = (
                normalized_text[:entity.start] + 
                entity.placeholder.lower() + 
                normalized_text[entity.end:]
            )
            entity_mapping[entity.placeholder] = entity.text.lower()
        
        return normalized_text.lower(), entity_mapping


# Convenience functions
def detect_companies(text: str) -> List[EntityMatch]:
    """Detect company entities in text."""
    tagger = EntityTagger()
    return tagger.detect_entities(text)


def normalize_query(text: str) -> Tuple[str, Dict[str, str]]:
    """Normalize query by replacing companies with placeholders."""
    tagger = EntityTagger()
    return tagger.normalize_text(text)


if __name__ == "__main__":
    # Test the entity tagger
    tagger = EntityTagger()
    
    test_queries = [
        "What is the revenue for Apple and Microsoft?",
        "Get Tesla's stock price for Q3 2023",
        "Show me JPMorgan Chase's balance sheet in New York",
        "Compare Amazon and Alphabet Inc's market cap in the US",
        "What are Berkshire Hathaway's holdings in California?",
        "Get financial data for NVDA and AMD in Europe",
        "Show me Johnson & Johnson's earnings under CEO Alex Gorsky",
        "What is Procter & Gamble Company's debt ratio in Germany?",
        "Compare AAPL, MSFT, and GOOGL performance in Asia",
        "Get data for Samsung's business in China and Japan"
    ]
    
    print("ADVANCED ENTITY TAGGING TEST")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing Query:")
        print(f"   Original:   {query}")
        
        # Detect entities
        entities = tagger.detect_entities(query)
        print(f"   Entities:   {[(e.text, e.entity_type) for e in entities]}")
        
        # Normalize
        normalized, mapping = tagger.normalize_text(query)
        print(f"   Normalized: {normalized}")
        if mapping:
            print(f"   Mapping:    {mapping}")
