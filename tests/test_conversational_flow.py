"""
Test the conversational flow end-to-end
This helps debug why the app might not be responding
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.parser import parse_query
from src.utils.parameter_extractor import extract_keywords_from_query
from src.tools.tool_matcher import ToolMatcher
from src.tools.tool_executor import ToolExecutor


def test_full_flow(question: str):
    """Test the complete flow from question to response"""
    
    print("=" * 70)
    print(f"Testing: {question}")
    print("=" * 70)
    
    try:
        # Step 1: Parse query
        print("\n1️⃣ Parsing query...")
        parsed = parse_query(question)
        keywords = parsed.get("extracted_keywords", [])
        print(f"   ✅ Keywords extracted: {keywords}")
        
        # Step 2: Match tool
        print("\n2️⃣ Matching tool...")
        matcher = ToolMatcher()
        tool_match = matcher.match_tool(keywords, question)
        selected_tool = tool_match["tool_name"]
        confidence = tool_match["confidence"]
        print(f"   ✅ Selected tool: {selected_tool} ({confidence:.0%} confidence)")
        print(f"   Matched keywords: {tool_match['matched_keywords'][:3]}")
        
        # Step 3: Execute tool
        print(f"\n3️⃣ Executing {selected_tool} tool...")
        executor = ToolExecutor()
        result = executor.execute(selected_tool, question)
        
        print(f"   Success: {result.get('success', False)}")
        
        if result.get("success"):
            print(f"\n✅ SUCCESS!")
            print(f"\n🤖 LLM Response:")
            print(f"   {result['llm_response']}")
            print(f"\n📊 Raw Data Available: {bool(result.get('raw_data'))}")
        else:
            print(f"\n❌ FAILED!")
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n" + "🧪 TESTING CONVERSATIONAL FLOW" + "\n")
    
    test_questions = [
        "What's the weather in London?",
        "Show me soil data for Iowa",
        "How do I use the weather API?",
    ]
    
    for question in test_questions:
        result = test_full_flow(question)
        print("\n" + "─" * 70 + "\n")
        
        if result and not result.get("success"):
            print("⚠️  This might be why the app isn't responding!")
            print(f"   Error: {result.get('error')}")
            print("\n💡 Check:")
            print("   1. API keys in .env file")
            print("   2. Internet connection")
            print("   3. Tool execution errors")

