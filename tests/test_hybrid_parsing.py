"""
Test Hybrid Parsing System
Tests the hybrid approach combining fast keyword matching with LLM classification
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.tools.tool_matcher import ToolMatcher
from src.utils.parameter_extractor import extract_keywords_from_query


def test_hybrid_parsing():
    """Test hybrid parsing with various query types"""
    print("=" * 80)
    print("TEST: Hybrid Parsing System")
    print("=" * 80)
    
    matcher = ToolMatcher(
        use_llm_fallback=True,
        confidence_threshold=0.85,
        llm_threshold=0.6
    )
    
    test_queries = [
        # High confidence (should use fast path)
        ("What's the weather in London?", "weather"),
        ("Show me soil data for Iowa", "soil"),
        ("Find the Roundup pesticide label", "cdms_label"),
        
        # Medium confidence (should use hybrid)
        ("Tell me about temperature", "weather"),
        ("What's the soil like?", "soil"),
        
        # Low confidence (should use LLM)
        ("What's it like outside?", "weather"),
        ("How do I use this?", "ambiguous"),
        ("What about safety?", "cdms_label"),  # Follow-up
    ]
    
    print("\n📝 Testing Hybrid Parsing")
    print("-" * 80)
    
    for query, expected_tool in test_queries:
        print(f"\n🔍 Query: {query}")
        print(f"   Expected: {expected_tool}")
        print("-" * 80)
        
        # Extract keywords
        keywords = extract_keywords_from_query(query)
        print(f"   Keywords: {keywords}")
        
        # Match tool
        result = matcher.match_tool(keywords, query)
        
        print(f"   ✅ Tool: {result['tool_name']}")
        print(f"   📊 Confidence: {result['confidence']:.0%}")
        print(f"   🔧 Method: {result.get('method', 'unknown')}")
        print(f"   🧠 LLM Used: {result.get('llm_used', False)}")
        
        if result.get('llm_reasoning'):
            print(f"   💭 LLM Reasoning: {result['llm_reasoning'][:100]}...")
        
        if result.get('method') == 'hybrid':
            fast = result.get('fast_path_result', {})
            llm = result.get('llm_result', {})
            print(f"   ⚡ Fast Path: {fast.get('tool')} ({fast.get('confidence', 0):.0%})")
            print(f"   🧠 LLM Path: {llm.get('tool')} ({llm.get('confidence', 0):.0%})")
    
    print("\n" + "=" * 80)
    print("✅ Hybrid parsing test complete!")
    print("=" * 80)


def test_followup_with_hybrid():
    """Test follow-up questions with hybrid parsing"""
    print("\n" + "=" * 80)
    print("TEST: Follow-up Questions with Hybrid Parsing")
    print("=" * 80)
    
    matcher = ToolMatcher(use_llm_fallback=True)
    
    # Simulate conversation
    conversation = [
        {
            "role": "user",
            "content": "What's the application rate for Roundup?"
        },
        {
            "role": "assistant",
            "content": "The application rate for Roundup is 1.5-2.5 quarts per acre..."
        }
    ]
    
    followup = "How do I mix it?"
    print(f"\n📝 Initial: {conversation[0]['content']}")
    print(f"🔍 Follow-up: {followup}")
    print("-" * 80)
    
    keywords = extract_keywords_from_query(followup)
    result = matcher.match_tool(keywords, followup, conversation_context=conversation)
    
    print(f"   ✅ Tool: {result['tool_name']}")
    print(f"   📊 Confidence: {result['confidence']:.0%}")
    print(f"   🔧 Method: {result.get('method', 'unknown')}")
    print(f"   🧠 LLM Used: {result.get('llm_used', False)}")
    
    if result.get('llm_reasoning'):
        print(f"   💭 LLM Reasoning: {result['llm_reasoning']}")
    
    # Should select CDMS because of context
    if result['tool_name'] == 'cdms_label':
        print("   ✅ Correctly used context to select CDMS!")
    else:
        print(f"   ⚠️  Expected CDMS but got {result['tool_name']}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        test_hybrid_parsing()
        test_followup_with_hybrid()
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
