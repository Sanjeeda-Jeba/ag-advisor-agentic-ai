"""
Parameter Extractor
Extracts parameters (city, location, etc.) from natural language queries
"""

import re
import spacy
from typing import Optional, Dict, List

# Load spaCy model (en_core_web_sm)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("⚠️  spaCy model not found. Run: python -m spacy download en_core_web_sm")
    nlp = None


def extract_city_from_query(query: str) -> Optional[str]:
    """
    Extract city name from a natural language query
    
    Args:
        query: User's natural language question
    
    Returns:
        City name if found, None otherwise
    
    Examples:
        "What's the weather in London?" -> "London"
        "Show me weather for New York" -> "New York"
        "Temperature in Tokyo" -> "Tokyo"
    """
    if nlp is None:
        # Fallback to regex if spaCy not available
        return _extract_city_regex(query)
    
    # Method 1: Try spaCy NER (Named Entity Recognition)
    doc = nlp(query)
    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC"]:  # Geopolitical Entity or Location
            return ent.text
    
    # Method 2: Try regex patterns
    city = _extract_city_regex(query)
    if city:
        return city
    
    return None


def _extract_city_regex(query: str) -> Optional[str]:
    """
    Extract city using regex patterns
    
    Args:
        query: User query
    
    Returns:
        City name if found
    """
    # Common patterns for city extraction
    patterns = [
        r"(?:weather|temperature|forecast|climate)\s+(?:in|for|at|near)\s+([A-Z][a-zA-Z\s]+?)(?:\?|$|,)",
        r"(?:in|for|at|near)\s+([A-Z][a-zA-Z\s]+?)(?:\?|$|,)",
        r"([A-Z][a-zA-Z\s]+?)\s+(?:weather|temperature|forecast)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            city = match.group(1).strip()
            # Clean up common words
            exclude_words = {"weather", "temperature", "the", "show", "me", "get"}
            if city.lower() not in exclude_words:
                return city
    
    return None


def extract_location_from_soil_query(query: str, conversation_context: list = None) -> Optional[Dict]:
    """
    Extract location from soil-related queries, using conversation context for follow-ups
    
    Args:
        query: User's natural language question
        conversation_context: Optional list of previous messages for context
            Format: [{"role": "user/assistant", "content": "..."}, ...]
    
    Returns:
        Dict with location info, or None
        {"location": "California"} or {"lat": 40.7, "lon": -74.0}
    
    Examples:
        "soil data for Iowa" -> {"location": "Iowa"}
        "Show me soil in California" -> {"location": "California"}
        Previous: "soil data for ames" (failed), Current: "Ames iowa" -> {"location": "Ames, Iowa"}
    """
    # First, try to extract from current query
    location_info = None
    
    if nlp is None:
        location_info = _extract_location_regex(query)
    else:
        # Try spaCy NER
        doc = nlp(query)
        for ent in doc.ents:
            if ent.label_ in ["GPE", "LOC"]:
                location_info = {"location": ent.text}
                break
        
        # Fallback to regex if NER didn't find anything
        if not location_info:
            location_info = _extract_location_regex(query)
    
    # If location found in current query, return it
    if location_info:
        return location_info
    
    # If no location in current query, check conversation context
    if conversation_context:
        # Look for location mentions in previous messages
        # Start from most recent and work backwards
        for msg in reversed(conversation_context):
            content = msg.get("content", "")
            if not content:
                continue
            
            # Check if previous message was about soil
            content_lower = content.lower()
            is_soil_related = any(kw in content_lower for kw in ["soil", "dirt", "ground", "earth"])
            
            # Try to extract location from previous message
            if nlp is None:
                prev_location = _extract_location_regex(content)
            else:
                doc = nlp(content)
                prev_location = None
                for ent in doc.ents:
                    if ent.label_ in ["GPE", "LOC"]:
                        prev_location = {"location": ent.text}
                        break
                if not prev_location:
                    prev_location = _extract_location_regex(content)
            
            # If we found a location in a soil-related message, use it
            if prev_location and is_soil_related:
                # Combine with current query if it has additional location info
                # Example: Previous had "Ames", current has "Iowa" -> "Ames, Iowa"
                current_location = _extract_location_regex(query)
                if current_location:
                    # Combine locations
                    prev_loc = prev_location.get("location", "")
                    curr_loc = current_location.get("location", "")
                    if prev_loc and curr_loc and prev_loc.lower() != curr_loc.lower():
                        combined = f"{prev_loc}, {curr_loc}"
                        return {"location": combined}
                    elif curr_loc:
                        return current_location
                
                return prev_location
            
            # Also check if current query is just a location (follow-up)
            # Example: Previous: "soil data for ames" (failed), Current: "Ames iowa"
            if prev_location and len(query.split()) <= 3:
                # Current query looks like a follow-up location
                # Try to extract location from current query
                current_location = _extract_location_regex(query)
                if current_location:
                    # Combine with previous location
                    prev_loc = prev_location.get("location", "")
                    curr_loc = current_location.get("location", "")
                    if prev_loc and curr_loc:
                        # Check if they're different (e.g., "Ames" + "Iowa")
                        if prev_loc.lower() not in curr_loc.lower() and curr_loc.lower() not in prev_loc.lower():
                            combined = f"{prev_loc}, {curr_loc}"
                            return {"location": combined}
                        else:
                            # One contains the other, use the more complete one
                            return current_location if len(curr_loc) > len(prev_loc) else prev_location
                    return current_location
                else:
                    # Current query might be the location itself
                    # Check if it looks like a location (capitalized words)
                    words = query.split()
                    if len(words) <= 3 and all(w[0].isupper() if w else False for w in words):
                        return {"location": query}
    
    return None


def _extract_location_regex(query: str) -> Optional[Dict]:
    """Extract location using regex patterns"""
    patterns = [
        r"soil\s+(?:in|for|at|near)\s+([A-Z][a-zA-Z\s]+?)(?:\?|$|,)",
        r"(?:in|for|at|near)\s+([A-Z][a-zA-Z\s]+?)(?:\?|$|,)",
        r"([A-Z][a-zA-Z\s]+?)\s+soil",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            location = match.group(1).strip()
            return {"location": location}
    
    # Additional pattern: Check if query is just capitalized words (likely a location)
    # Example: "Ames iowa", "New York", "Los Angeles"
    words = query.strip().split()
    if len(words) >= 1 and len(words) <= 3:
        # Check if all words start with capital letters (likely a location)
        if all(word and word[0].isupper() for word in words):
            # Filter out common non-location words
            exclude_words = {"The", "A", "An", "And", "Or", "But", "For", "With"}
            location_words = [w for w in words if w not in exclude_words]
            if location_words:
                return {"location": " ".join(location_words)}
    
    return None


def detect_temperature_unit(query: str) -> str:
    """
    Detect if user wants Celsius or Fahrenheit
    
    Args:
        query: User query
    
    Returns:
        "metric" for Celsius, "imperial" for Fahrenheit
    """
    query_lower = query.lower()
    
    # Check for explicit mentions
    if any(word in query_lower for word in ["fahrenheit", "°f", "f"]):
        return "imperial"
    
    # Default to metric (Celsius)
    return "metric"


def extract_keywords_from_query(query: str) -> List[str]:
    """
    Extract important keywords from query
    
    Args:
        query: User query
    
    Returns:
        List of keywords
    """
    if nlp is None:
        # Fallback: simple word splitting
        words = re.findall(r'\b\w+\b', query.lower())
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or'}
        return [w for w in words if w not in stop_words]
    
    doc = nlp(query)
    
    # Extract meaningful keywords (nouns, verbs, adjectives)
    keywords = []
    for token in doc:
        if token.pos_ in ["NOUN", "VERB", "ADJ", "PROPN"]:
            if not token.is_stop and len(token.text) > 2:
                keywords.append(token.lemma_.lower())
    
    return keywords


# Test function
if __name__ == "__main__":
    print("Testing Parameter Extractor...")
    print("-" * 50)
    
    test_queries = [
        "What's the weather in London?",
        "Show me temperature in New York",
        "Is it raining in Tokyo?",
        "Weather in Paris in Fahrenheit",
        "How's the weather in San Francisco?",
        "soil data for California",
        "Show me soil in Iowa"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Extract city/location
        city = extract_city_from_query(query)
        print(f"  City: {city}")
        
        # Extract keywords
        keywords = extract_keywords_from_query(query)
        print(f"  Keywords: {keywords}")
        
        # Detect units
        units = detect_temperature_unit(query)
        print(f"  Units: {units}")
