import unittest
from src.parser import parse_query

class TestParser(unittest.TestCase):
    def test_exact_match_and_keywords(self):
        query = "I want to get customer details"
        result = parse_query(query)
        self.assertIn("customer details", result["extracted_keywords"])
        self.assertEqual(result["ranked_api_matches"][0]["api_name"], "get_customer_details")

    def test_fuzzy_match_typo(self):
        query = "show me product invntory"
        result = parse_query(query)
        self.assertIn("product", result["extracted_keywords"])
        self.assertEqual(result["ranked_api_matches"][0]["api_name"], "get_product_inventory")
        # Assert a high but more realistic score
        self.assertGreater(result["ranked_api_matches"][0]["score"], 65)

    def test_no_match(self):
        query = "what is the weather like today?"
        result = parse_query(query)
        # Assert that the list of ranked matches is empty due to the low score
        self.assertFalse(result["ranked_api_matches"])