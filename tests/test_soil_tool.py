"""
Test script for Soil Tool
Run this to verify the soil tool is working correctly
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tools.soil_tool import execute_soil_tool
from tools.tool_executor import ToolExecutor


def test_soil_tool():
    """Test the soil tool with sample questions"""
    
    print("="* 70)
    print("🧪 TESTING SOIL TOOL")
    print("=" * 70)
    
    test_questions = [
        "Show me soil data for Iowa",
        "What's the soil composition in California?",
        "Tell me about soil in Texas",
        "Soil pH for New York"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'─' * 70}")
        print(f"Test {i}/4")
        print(f"{'─' * 70}")
        print(f"📝 Question: {question}")
        print()
        
        # Execute the soil tool
        result = execute_soil_tool(question)
        
        if result["success"]:
            print("✅ Tool execution: SUCCESS")
            print()
            
            # Display raw data
            data = result["data"]
            location = data["location"]
            print(f"📍 Location: Lat {location['lat']}, Lon {location['lon']}")
            print()
            print(f"🌱 Soil Properties:")
            for prop_name, prop_data in data["properties"].items():
                print(f"  • {prop_data['label']}: {prop_data['value']} {prop_data['unit']}")
            
        else:
            print("❌ Tool execution: FAILED")
            print(f"   Error: {result['error']}")
    
    print(f"\n{'=' * 70}")
    print("✅ Testing complete!")
    print("=" * 70)


def test_with_llm():
    """Test soil tool with LLM response generation"""
    
    print("\n" + "="* 70)
    print("🧪 TESTING SOIL TOOL WITH LLM RESPONSE")
    print("=" * 70)
    
    try:
        executor = ToolExecutor()
        
        test_questions = [
            "Show me soil data for Iowa",
            "What's the soil pH in California?",
        ]
        
        for question in test_questions:
            print(f"\n{'─' * 70}")
            print(f"📝 Question: {question}")
            print("─" * 70)
            
            result = executor.execute("soil", question)
            
            if result["success"]:
                print("✅ Success!")
                print(f"\n🤖 LLM Response:")
                print(f"   {result['llm_response']}")
                
                print(f"\n📊 Raw Data:")
                data = result["raw_data"]
                print(f"   Location: {data['location']}")
                print(f"   Properties: {len(data.get('properties', {}))} found")
            else:
                print(f"❌ Failed: {result['error']}")
        
        print("\n" + "=" * 70)
        print("✅ LLM Testing complete!")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure you have:")
        print("   1. OPENAI_API_KEY in .env")
        print("   2. OPENWEATHER_API_KEY in .env (for geocoding)")


if __name__ == "__main__":
    print("\n" + "🌱 SOIL TOOL TEST SUITE" + "\n")
    
    # Test 1: Basic soil tool
    test_soil_tool()
    
    # Test 2: With LLM (if OpenAI key is available)
    print("\n" + "─" * 70)
    response = input("\nTest with LLM response generation? (y/n): ").strip().lower()
    
    if response == 'y':
        test_with_llm()
    else:
        print("\n💡 To test LLM responses:")
        print("   1. Add OPENAI_API_KEY to .env")
        print("   2. Run: python src/tools/tool_executor.py")

