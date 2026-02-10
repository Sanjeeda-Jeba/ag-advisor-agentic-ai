import json
import spacy
from rapidfuzz import process, fuzz
from pathlib import Path

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent
CATALOG_PATH = SCRIPT_DIR / "api_catalog.json"

# Load the API catalog
with open(CATALOG_PATH, "r") as f:
    API_CATALOG = json.load(f)["apis"]

def extract_keywords(query: str):
    """
    Extracts keywords and phrases using a combination of spaCy's rule-based
    matching and phrase matching.
    """
    doc = nlp(query.lower())
    matched_keywords = set()

    # Rule-based matching (e.g., for "get customer details")
    matcher = spacy.matcher.Matcher(nlp.vocab)
    # Define a simple pattern for a phrase like "get customer"
    pattern = [{"LOWER": "get"}, {"LOWER": "customer"}]
    matcher.add("GET_CUSTOMER", [pattern])
    
    matches = matcher(doc)
    for match_id, start, end in matches:
        matched_keywords.add(doc[start:end].text)

    # Phrase matching for exact phrases
    phrase_matcher = spacy.matcher.PhraseMatcher(nlp.vocab)
    phrases = ["customer details", "product inventory"]
    phrase_patterns = [nlp.make_doc(text) for text in phrases]
    phrase_matcher.add("API_PHRASES", phrase_patterns)

    matches = phrase_matcher(doc)
    for match_id, start, end in matches:
        matched_keywords.add(doc[start:end].text)

    # Simple token-based keywords
    token_keywords = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct and len(token) > 2]
    matched_keywords.update(token_keywords)
    
    return list(matched_keywords)

def fuzzy_match_apis(query: str, apis: list):
    api_names = [api["name"] for api in apis]
    matches = process.extract(query, api_names, scorer=fuzz.WRatio, limit=5)

    ranked_apis = []
    for match, score, index in matches:
        # Only include matches with a score above the confidence threshold
        if score >= 70:  
            ranked_apis.append({
                "api_name": match,
                "score": score,
                "description": apis[index]["description"]
            })
    return ranked_apis

def parse_query(query: str):
    """
    Combines keyword extraction and fuzzy matching to parse the query.
    """
    keywords = extract_keywords(query)
    ranked_apis = fuzzy_match_apis(query, API_CATALOG)
    
    return {
        "original_query": query,
        "extracted_keywords": keywords,
        "ranked_api_matches": ranked_apis
    }

if __name__ == "__main__":
    test_query = "i need to get the details for a customer"
    result = parse_query(test_query)
    print(json.dumps(result, indent=2))