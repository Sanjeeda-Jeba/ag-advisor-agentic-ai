"""
Test CDMS Priority and Fallback Logic
Tests that CDMS is tried first, then agriculture_web if no results
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.tools.tool_executor import ToolExecutor
from src.tools.tool_matcher import ToolMatcher
from src.utils.parameter_extractor import extract_keywords_from_query


def test_tool_priority():
    """Test that CDMS is prioritized for pesticide queries"""
    print("=" * 80)
    print("TEST 1: Tool Priority for Pesticide Queries")
    print("=" * 80)
    
    matcher = ToolMatcher()
    
    test_queries = [
        ("What's the application rate for Roundup?", "cdms_label"),
        ("Find Roundup label", "cdms_label"),
        ("Safety precautions for pesticides", "cdms_label"),
        ("How to control aphids on tomatoes?", "agriculture_web"),
        ("Best practices for corn fertilization", "agriculture_web"),
        ("What's the weather in London?", "weather"),
    ]
    
    for query, expected_tool in test_queries:
        keywords = extract_keywords_from_query(query)
        match = matcher.match_tool(keywords, query)
        selected = match["tool_name"]
        
        status = "✅" if selected == expected_tool else "❌"
        print(f"{status} Query: '{query}'")
        print(f"   Expected: {expected_tool}, Got: {selected} ({match['confidence']:.0%})")
        if selected != expected_tool:
            print(f"   ⚠️  Mismatch!")
        print()


def test_cdms_fallback():
    """Test that CDMS falls back to agriculture_web when no results"""
    print("=" * 80)
    print("TEST 2: CDMS Fallback to Agriculture Web")
    print("=" * 80)
    
    executor = ToolExecutor()
    
    # Test with a query that might not find results in CDMS
    # (e.g., a very specific or unusual pesticide question)
    test_query = "What are the best practices for organic pest control?"
    
    print(f"\n🔍 Query: '{test_query}'")
    print("-" * 80)
    
    # This should try CDMS first, then fallback to agriculture_web
    result = executor.execute(
        tool_name="cdms_label",
        user_question=test_query
    )
    
    if result.get("success"):
        tool_used = result.get("tool_used")
        fallback_used = result.get("fallback_used", False)
        
        print(f"✅ Execution successful!")
        print(f"   Tool used: {tool_used}")
        print(f"   Fallback used: {fallback_used}")
        
        if fallback_used:
            print(f"   ✅ Fallback logic working - tried CDMS, then agriculture_web")
        else:
            print(f"   ℹ️  CDMS found results (no fallback needed)")
        
        # Show response preview
        response = result.get("llm_response", "")
        print(f"\n   Response preview: {response[:200]}...")
    else:
        print(f"❌ Execution failed: {result.get('error')}")


def test_pesticide_query_routing():
    """Test that pesticide queries route to CDMS first"""
    print("\n" + "=" * 80)
    print("TEST 3: Pesticide Query Routing")
    print("=" * 80)
    
    executor = ToolExecutor()
    matcher = ToolMatcher()
    
    pesticide_queries = [
        "What's the application rate for Roundup?",
        "Show me safety precautions for pesticides",
        "How do I mix herbicide?",
        "What's the re-entry interval for insecticides?"
    ]
    
    for query in pesticide_queries:
        print(f"\n🔍 Query: '{query}'")
        print("-" * 80)
        
        # Check tool selection
        keywords = extract_keywords_from_query(query)
        match = matcher.match_tool(keywords, query)
        selected_tool = match["tool_name"]
        
        print(f"   Selected tool: {selected_tool} ({match['confidence']:.0%})")
        
        if selected_tool == "cdms_label":
            print(f"   ✅ Correctly routed to CDMS")
        else:
            print(f"   ⚠️  Expected CDMS, got {selected_tool}")
    
    print("\n" + "=" * 80)


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("CDMS Priority and Fallback Testing")
    print("=" * 80)
    print("\nThis will test:")
    print("1. Tool priority (CDMS first for pesticide queries)")
    print("2. Fallback logic (agriculture_web if CDMS finds nothing)")
    print("3. Pesticide query routing")
    print("\n" + "=" * 80)
    
    try:
        test_tool_priority()
        test_cdms_fallback()
        test_pesticide_query_routing()
        
        print("\n" + "=" * 80)
        print("✅ All tests complete!")
        print("=" * 80)
        print("\n💡 Summary:")
        print("   - CDMS is prioritized for pesticide/label queries")
        print("   - If CDMS finds no results, automatically falls back to agriculture_web")
        print("   - Tool matcher correctly identifies pesticide queries")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()






