# -*- coding: utf-8 -*-
"""Unified entity processing system combining NER detection and normalization."""

from dataclasses import dataclass
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple


logger = logging.getLogger(__name__)

# Try to import spaCy for NER, with fallback
try:
    import spacy

    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available - entity normalization disabled")


@dataclass
class EntityMatch:
    """Represents a detected entity match."""

    text: str
    start: int
    end: int
    entity_type: str
    placeholder: str


class EntityProcessor:
    """Unified entity detection and normalization processor."""

    def __init__(self) -> None:
        """Initialize the entity processor."""
        # Initialize spaCy NER
        self.nlp: Optional[Any] = None
        self._init_spacy_model()

        # Initialize legacy patterns for backward compatibility
        self._init_legacy_patterns()

    def _init_spacy_model(self) -> None:
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
                logger.warning("No spaCy English model found - entity normalization disabled")
                self.nlp = None

    def _init_legacy_patterns(self) -> None:
        """Initialize legacy company patterns for backward compatibility."""
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
            "jpmorgan": ["jpmorgan", "jpm", "jpmorgan chase", "jp morgan"],
            "goldman_sachs": ["goldman sachs", "gs", "goldman sachs group"],
            "morgan_stanley": ["morgan stanley", "ms", "morgan stanley & co"],
            "bank_of_america": ["bank of america", "bac", "bofa"],
            "wells_fargo": ["wells fargo", "wfc", "wells fargo & company"],
            "citigroup": ["citigroup", "c", "citi", "citicorp"],
            # Other major companies
            "berkshire_hathaway": ["berkshire hathaway", "brk.a", "brk.b", "berkshire"],
            "coca_cola": ["coca cola", "ko", "coca-cola", "coke"],
            "walmart": ["walmart", "wmt", "wal-mart"],
            "disney": ["disney", "dis", "walt disney"],
            "general_electric": ["general electric", "ge", "ge company"],
            "exxon": ["exxon", "xom", "exxon mobil", "exxonmobil"],
            "pfizer": ["pfizer", "pfe", "pfizer inc"],
            # International companies
            "toyota": ["toyota", "tm", "toyota motor"],
            "samsung": ["samsung", "005930.ks", "samsung electronics"],
            "nestle": ["nestle", "nsrgy", "nestle sa"],
        }

        # Create reverse mapping for legacy patterns
        self.legacy_entity_to_placeholder = {}
        self.legacy_placeholder_to_entities = {}

        # Create generic placeholders (COMPANY_A, COMPANY_B, etc.) for legacy patterns
        placeholder_letters = [
            "A",
            "B",
            "C",
            "D",
            "E",
            "F",
            "G",
            "H",
            "I",
            "J",
            "K",
            "L",
            "M",
            "N",
            "O",
            "P",
            "Q",
            "R",
            "S",
            "T",
        ]

        for i, (placeholder, variations) in enumerate(self.legacy_company_patterns.items()):
            if i < len(placeholder_letters):
                placeholder_key = f"<COMPANY_{placeholder_letters[i]}>"
                self.legacy_placeholder_to_entities[placeholder_key] = variations
                for variation in variations:
                    self.legacy_entity_to_placeholder[variation.lower()] = placeholder_key

    def process_query(self, query: str) -> Tuple[str, Dict[str, str]]:
        """Main entry point: detect and normalize entities in query.

        Args:
            query: Original query string

        Returns:
            Tuple of (normalized_query, entity_mapping)
        """
        # First, handle existing old-style placeholders (convert them to new format)
        normalized_query = query.lower()
        entity_mapping = {}

        old_placeholder_pattern = r"<company_(\w+)>"
        old_placeholders = re.findall(old_placeholder_pattern, normalized_query)
        for old_company_name in old_placeholders:
            # Find the new placeholder for this company using legacy patterns
            if old_company_name in self.legacy_entity_to_placeholder:
                new_placeholder = self.legacy_entity_to_placeholder[old_company_name]
                old_pattern = f"<company_{old_company_name}>"
                normalized_query = normalized_query.replace(old_pattern, new_placeholder.lower())
                entity_mapping[new_placeholder] = old_company_name

        # If no old placeholders found, use the advanced entity detection
        if not old_placeholders:
            try:
                normalized_query, entity_mapping = self._detect_and_normalize(query)
            except (RuntimeError, ValueError, AttributeError) as e:
                logger.error("Error in entity detection, falling back to legacy method: %s", e)
                # Fallback to legacy method
                return self._normalize_query_legacy(query)

        return normalized_query, entity_mapping

    def normalize_query_for_search(self, query: str) -> Tuple[str, Dict[str, str]]:
        """Normalize a query for search by replacing entities with placeholders.

        This is an alias for process_query to maintain API compatibility.

        Args:
            query: Input query text

        Returns:
            Tuple of (normalized_query, entity_mapping)
        """
        return self.process_query(query)

    def _detect_and_normalize(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Detect and normalize entities using spaCy NER.

        If spaCy is not available, returns text as-is with no entity masking.

        Args:
            text: Input text

        Returns:
            Tuple of (normalized_text, entity_mapping)
        """
        # If no spaCy model available, return text as-is (no entity masking)
        if not self.nlp:
            return text.lower(), {}

        entities = self._detect_entities(text)

        if not entities:
            return text.lower(), {}

        # Sort entities by start position (reverse order for replacement)
        entities.sort(key=lambda x: x.start, reverse=True)

        normalized_text = text
        entity_mapping = {}

        # Replace entities with placeholders (reverse order to preserve positions)
        for entity in entities:
            normalized_text = (
                normalized_text[: entity.start]
                + entity.placeholder.lower()
                + normalized_text[entity.end :]
            )
            entity_mapping[entity.placeholder] = entity.text.lower()

        return normalized_text.lower(), entity_mapping

    def _detect_entities(self, text: str) -> List[EntityMatch]:
        """Detect entities using spaCy NER.

        Args:
            text: Input text to analyze

        Returns:
            List of detected entity matches (empty if spaCy not available)
        """
        entities: List[EntityMatch] = []

        # Only use spaCy NER if available
        if self.nlp:
            entities = self._detect_with_spacy(text)
            # Remove duplicates and overlaps
            entities = self._deduplicate_entities(entities)

        return entities

    def _detect_with_spacy(self, text: str) -> List[EntityMatch]:
        """Detect entities using spaCy NER."""
        entities: List[EntityMatch] = []

        if not self.nlp:
            return entities

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
                    if self._is_likely_company(cleaned_text) and not self._is_geographic_entity(
                        cleaned_text
                    ):
                        entity_counts["COMPANY"] += 1
                        placeholder = (
                            f"<COMPANY_{chr(64 + entity_counts['COMPANY'])}>"  # A, B, C, etc.
                        )
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
                    entities.append(
                        EntityMatch(
                            text=cleaned_text,
                            start=ent.start_char,
                            end=ent.end_char,
                            entity_type=entity_type,
                            placeholder=placeholder,
                        )
                    )
        except (RuntimeError, ValueError, AttributeError) as e:
            logger.error("Error in spaCy NER: %s", e)

        return entities

    def _clean_entity_text(self, text: str) -> str:
        """Clean entity text by removing common prefixes and normalizing."""
        cleaned = text.strip()

        # Remove common prefixes that shouldn't be part of company names
        prefixes_to_remove = [
            "compare ",
            "get ",
            "show ",
            "what ",
            "how ",
            "when ",
            "where ",
            "why ",
            "find ",
            "search ",
            "look ",
            "see ",
            "view ",
            "display ",
            "list ",
            "tell ",
            "give ",
            "provide ",
            "fetch ",
            "retrieve ",
            "obtain ",
        ]

        cleaned_lower = cleaned.lower()
        for prefix in prefixes_to_remove:
            if cleaned_lower.startswith(prefix):
                cleaned = cleaned[len(prefix) :].strip()
                break

        # Remove trailing punctuation
        cleaned = cleaned.rstrip(".,!?;:")

        return cleaned

    def _is_likely_company(self, text: str) -> bool:
        """Determine if detected entity is likely a company."""
        text_lower = text.lower()

        # Company indicators
        company_indicators = [
            "inc",
            "corp",
            "corporation",
            "company",
            "ltd",
            "limited",
            "llc",
            "plc",
            "technologies",
            "systems",
            "solutions",
            "services",
            "group",
            "holdings",
            "bank",
            "financial",
            "capital",
            "investment",
            "fund",
            "insurance",
            "pharmaceutical",
            "biotech",
            "energy",
            "oil",
            "gas",
            "mining",
            "automotive",
            "motors",
            "airlines",
            "airways",
            "communications",
            "media",
            "entertainment",
            "studios",
            "networks",
            "broadcasting",
        ]

        # Check if contains company indicators
        for indicator in company_indicators:
            if indicator in text_lower:
                return True

        # Check if it's a known ticker pattern (2-5 uppercase letters)
        if re.match(r"^[A-Z]{2,5}$", text):
            return True

        # Check if it's a well-known company name (expanded list)
        known_companies = {
            # Tech companies
            "apple",
            "microsoft",
            "google",
            "alphabet",
            "amazon",
            "meta",
            "facebook",
            "tesla",
            "netflix",
            "nvidia",
            "intel",
            "cisco",
            "oracle",
            "salesforce",
            "adobe",
            "paypal",
            "uber",
            "lyft",
            "airbnb",
            "zoom",
            "slack",
            "shopify",
            "spotify",
            "twitter",
            "snap",
            "pinterest",
            "reddit",
            "palantir",
            "snowflake",
            # Traditional companies
            "walmart",
            "disney",
            "nike",
            "mcdonald",
            "starbucks",
            "boeing",
            "caterpillar",
            "ford",
            "general motors",
            "general electric",
            "ibm",
            "hp",
            "dell",
            "xerox",
            # Financial companies
            "jpmorgan",
            "goldman sachs",
            "morgan stanley",
            "bank of america",
            "wells fargo",
            "citigroup",
            "visa",
            "mastercard",
            "american express",
            "berkshire hathaway",
            # International companies
            "samsung",
            "toyota",
            "sony",
            "nintendo",
            "softbank",
            "alibaba",
            "tencent",
            "tsmc",
            "asml",
            "nestle",
            "unilever",
            "lvmh",
            "sap",
            "siemens",
            "volkswagen",
            # Healthcare & Pharma
            "johnson & johnson",
            "pfizer",
            "merck",
            "abbott",
            "bristol myers squibb",
            "eli lilly",
            "novartis",
            "roche",
            "astrazeneca",
            "glaxosmithkline",
            # Energy & Commodities
            "exxon mobil",
            "chevron",
            "conocophillips",
            "bp",
            "shell",
            "total",
            "saudi aramco",
            "gazprom",
            "petrobras",
        }

        return any(company in text_lower for company in known_companies)

    def _is_geographic_entity(self, text: str) -> bool:
        """Determine if detected entity is a geographic location, not a company."""
        text_lower = text.lower().strip()

        # Common geographic terms that should not be treated as companies
        geographic_terms = {
            # Countries
            "us",
            "usa",
            "united states",
            "america",
            "uk",
            "united kingdom",
            "canada",
            "china",
            "japan",
            "germany",
            "france",
            "italy",
            "spain",
            "russia",
            "india",
            "brazil",
            "mexico",
            "australia",
            "south korea",
            "netherlands",
            "switzerland",
            # US States
            "california",
            "new york",
            "texas",
            "florida",
            "illinois",
            "pennsylvania",
            "ohio",
            "georgia",
            "north carolina",
            "michigan",
            "new jersey",
            "virginia",
            "washington",
            "arizona",
            "massachusetts",
            "tennessee",
            "indiana",
            "missouri",
            "maryland",
            "wisconsin",
            "colorado",
            "minnesota",
            "south carolina",
            "alabama",
            # Major cities
            "new york city",
            "los angeles",
            "chicago",
            "houston",
            "phoenix",
            "philadelphia",
            "san antonio",
            "san diego",
            "dallas",
            "san jose",
            "austin",
            "jacksonville",
            "san francisco",
            "columbus",
            "charlotte",
            "fort worth",
            "detroit",
            "el paso",
            "memphis",
            "seattle",
            "denver",
            "washington dc",
            "boston",
            "nashville",
            "baltimore",
            "oklahoma city",
            "portland",
            "las vegas",
            "milwaukee",
            "albuquerque",
            # International cities
            "london",
            "paris",
            "tokyo",
            "beijing",
            "shanghai",
            "mumbai",
            "delhi",
            "sydney",
            "toronto",
            "vancouver",
            "berlin",
            "munich",
            "zurich",
            "geneva",
            "amsterdam",
            "stockholm",
            "copenhagen",
            "oslo",
            "helsinki",
            "dublin",
            "madrid",
            "barcelona",
            "rome",
            "milan",
            "moscow",
            "st petersburg",
            "hong kong",
            "singapore",
            "seoul",
            # Regions/Continents
            "europe",
            "asia",
            "north america",
            "south america",
            "africa",
            "oceania",
            "middle east",
            "latin america",
            "caribbean",
            "scandinavia",
            "balkans",
            "eastern europe",
            "western europe",
            "southeast asia",
            "east asia",
            "south asia",
        }

        # Check exact matches and common variations
        if text_lower in geographic_terms:
            return True

        # Check for possessive forms (e.g., "US's" -> "us")
        if text_lower.endswith("'s") and text_lower[:-2] in geographic_terms:
            return True

        # Check for common geographic suffixes that indicate places, not companies
        geographic_suffixes = ["city", "state", "country", "region", "province", "territory"]
        for suffix in geographic_suffixes:
            if text_lower.endswith(f" {suffix}"):
                return True

        return False

    def _deduplicate_entities(self, entities: List[EntityMatch]) -> List[EntityMatch]:
        """Remove duplicate and overlapping entities."""
        if not entities:
            return entities

        # Sort by start position
        entities.sort(key=lambda x: x.start)

        deduplicated: List[EntityMatch] = []
        for entity in entities:
            # Check for overlap with existing entities
            overlaps = False
            for existing in deduplicated:
                if entity.start < existing.end and entity.end > existing.start:
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

    def _normalize_query_legacy(self, query: str) -> Tuple[str, Dict[str, str]]:
        """Legacy normalization method as fallback."""
        normalized_query = query.lower()
        entity_mapping = {}

        # Use legacy entity patterns
        sorted_entities = sorted(
            self.legacy_entity_to_placeholder.items(), key=lambda x: len(x[0]), reverse=True
        )

        for entity, placeholder in sorted_entities:
            pattern = r"\b" + re.escape(entity) + r"\b"
            if re.search(pattern, normalized_query, re.IGNORECASE):
                normalized_query = re.sub(
                    pattern, placeholder.lower(), normalized_query, flags=re.IGNORECASE
                )
                entity_mapping[placeholder] = entity

        return normalized_query, entity_mapping

    def denormalize_query(self, normalized_query: str, entity_mapping: Dict[str, str]) -> str:
        """Convert normalized query back to original entities.

        Args:
            normalized_query: Query with placeholders
            entity_mapping: Mapping from placeholders to original entities

        Returns:
            Query with original entity names
        """
        denormalized = normalized_query
        for placeholder, entity in entity_mapping.items():
            denormalized = denormalized.replace(placeholder.lower(), entity)
        return denormalized

    def get_common_entities(self) -> Set[str]:
        """Get set of all common entity variations for testing."""
        entities = set()
        for variations in self.legacy_company_patterns.values():
            entities.update(variations)
        return entities

    def get_placeholders(self) -> Set[str]:
        """Get set of all placeholders."""
        return set(self.legacy_placeholder_to_entities.keys())


# Convenience functions for backward compatibility
def detect_companies(text: str) -> List[EntityMatch]:
    """Detect company entities in text."""
    processor = EntityProcessor()
    # Use the public API by processing the query and extracting entities
    _, entity_mapping = processor.process_query(text)
    # Convert entity mapping back to EntityMatch objects for backward compatibility
    entities = []
    for placeholder, original_text in entity_mapping.items():
        # This is a simplified conversion - in practice you might want more detailed info
        entities.append(
            EntityMatch(
                text=original_text,
                start=0,  # Position info not available from mapping
                end=len(original_text),
                entity_type="COMPANY",
                placeholder=placeholder,
            )
        )
    return entities


def normalize_query(text: str) -> Tuple[str, Dict[str, str]]:
    """Normalize query by replacing entities with placeholders."""
    processor = EntityProcessor()
    return processor.process_query(text)
