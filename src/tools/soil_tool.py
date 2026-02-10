"""
Soil Tool
Wrapper for soil API client to work with conversational system

Flow:
1. Extract location from question
2. Call Soil API (SoilGrids)
3. Return structured data (LLM will generate final response)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api_clients.usda_soil_client import USDASoilClient
from src.utils.parameter_extractor import extract_location_from_soil_query
from typing import Dict


def execute_soil_tool(question: str, conversation_context: list = None) -> Dict:
    """
    Execute soil tool - get soil data for a location
    Uses conversation context for follow-up questions
    
    Args:
        question: User's natural language question
        conversation_context: Optional list of previous messages for context
            Format: [{"role": "user/assistant", "content": "..."}, ...]
    
    Returns:
        Dict with tool execution result:
        {
            "success": True/False,
            "tool": "soil",
            "data": {...soil data...} or None,
            "error": "error message" if failed
        }
    
    Examples:
        >>> execute_soil_tool("Show me soil data for Iowa")
        {
            "success": True,
            "tool": "soil",
            "data": {
                "location": {"lat": 41.8781, "lon": -93.0977},
                "properties": {
                    "phh2o": {"value": 6.8, "label": "pH Level"},
                    ...
                }
            }
        }
        
        >>> # Follow-up example:
        >>> execute_soil_tool("Ames iowa", [{"role": "user", "content": "soil data for ames"}])
        # Uses context to understand this is about soil data for Ames, Iowa
    """
    try:
        # Extract location from question (with context for follow-ups)
        location_info = extract_location_from_soil_query(question, conversation_context=conversation_context)
        
        if not location_info:
            return {
                "success": False,
                "tool": "soil",
                "error": "Could not extract location from your question. Please specify a location (e.g., 'soil data for Iowa')."
            }
        
        # Create USDA soil client (reliable for US locations)
        client = USDASoilClient()
        
        # Call API with location info
        if "location" in location_info:
            soil_data = client.get_soil_data(location=location_info["location"])
        else:
            soil_data = client.get_soil_data(
                lat=location_info["lat"],
                lon=location_info["lon"]
            )
        
        # Check if API call was successful
        if not soil_data.get("success"):
            return {
                "success": False,
                "tool": "soil",
                "error": soil_data.get("error", "Failed to fetch soil data")
            }
        
        # Return successful result
        return {
            "success": True,
            "tool": "soil",
            "data": soil_data
        }
    
    except Exception as e:
        return {
            "success": False,
            "tool": "soil",
            "error": f"Unexpected error: {str(e)}"
        }


# Test function
if __name__ == "__main__":
    print("Testing Soil Tool...")
    print("-" * 70)
    
    test_questions = [
        "Show me soil data for Iowa",
        "What's the soil composition in California?",
        "Tell me about soil in Texas",
        "Soil pH for New York"
    ]
    
    for question in test_questions:
        print(f"\n📝 Question: {question}")
        print("-" * 70)
        
        result = execute_soil_tool(question)
        
        if result["success"]:
            print("✅ Success!")
            data = result["data"]
            print(f"\n📍 Location: {data['location']}")
            print(f"\n🌱 Soil Properties:")
            for prop_name, prop_data in data["properties"].items():
                print(f"  • {prop_data['label']}: {prop_data['value']} {prop_data['unit']}")
        else:
            print(f"❌ Error: {result['error']}")

