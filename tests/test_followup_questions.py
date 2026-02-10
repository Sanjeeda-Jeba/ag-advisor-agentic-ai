"""
Test Follow-up Questions with Context
Tests that the agent can understand follow-up questions using conversation context
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.tools.tool_executor import ToolExecutor
from src.tools.tool_matcher import ToolMatcher
from src.utils.parameter_extractor import extract_keywords_from_query


def test_followup_questions():
    """Test follow-up questions with conversation context"""
    print("=" * 80)
    print("TEST: Follow-up Questions with Context")
    print("=" * 80)
    
    executor = ToolExecutor()
    matcher = ToolMatcher()
    
    # Simulate a conversation
    conversation = [
        {
            "role": "user",
            "content": "What's the application rate for Roundup?"
        },
        {
            "role": "assistant",
            "content": "The application rate for Roundup is 1.5-2.5 quarts per acre (see page 5)..."
        }
    ]
    
    # Test follow-up questions
    followup_questions = [
        "What about safety precautions?",
        "How do I mix it?",
        "What's the re-entry interval?",
        "Show me the label"
    ]
    
    print(f"\n📝 Initial Question: {conversation[0]['content']}")
    print(f"🤖 Initial Response: {conversation[1]['content'][:100]}...")
    print("\n" + "=" * 80)
    
    for i, followup in enumerate(followup_questions, 1):
        print(f"\n🔍 Follow-up {i}: '{followup}'")
        print("-" * 80)
        
        # Extract keywords
        keywords = extract_keywords_from_query(followup)
        print(f"   Keywords: {keywords}")
        
        # Match tool
        tool_match = matcher.match_tool(keywords, followup)
        selected_tool = tool_match["tool_name"]
        print(f"   Selected tool: {selected_tool} ({tool_match['confidence']:.0%})")
        
        # Execute with context
        try:
            result = executor.execute(
                tool_name=selected_tool,
                user_question=followup,
                conversation_context=conversation
            )
            
            if result.get("success"):
                response = result.get("llm_response", "")
                print(f"   ✅ Response generated ({len(response)} chars)")
                
                # Check if response mentions Roundup (shows context was used)
                if "roundup" in response.lower():
                    print(f"   ✅ Response mentions 'Roundup' (context used!)")
                else:
                    print(f"   ⚠️  Response doesn't mention 'Roundup' (may need better context)")
                
                # Show preview
                preview = response[:200].replace("\n", " ")
                print(f"   Preview: {preview}...")
            else:
                print(f"   ❌ Failed: {result.get('error')}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✅ Follow-up question test complete!")
    print("=" * 80)


def test_product_extraction_from_context():
    """Test that product name is extracted from conversation context"""
    print("\n" + "=" * 80)
    print("TEST: Product Extraction from Context")
    print("=" * 80)
    
    from src.tools.cdms_label_tool import execute_cdms_label_tool
    
    # Test 1: Direct question (should work)
    print("\n📝 Test 1: Direct question with product name")
    print("   Question: 'What's the application rate for Roundup?'")
    
    result1 = execute_cdms_label_tool("What's the application rate for Roundup?")
    if result1.get("success"):
        product1 = result1.get("data", {}).get("product_name", "Unknown")
        print(f"   ✅ Product extracted: {product1}")
    else:
        print(f"   ❌ Failed: {result1.get('error')}")
    
    # Test 2: Follow-up without product name (should use context)
    print("\n📝 Test 2: Follow-up question without product name")
    print("   Question: 'What about safety precautions?'")
    
    conversation_context = [
        {"role": "user", "content": "What's the application rate for Roundup?"},
        {"role": "assistant", "content": "The application rate is..."}
    ]
    
    result2 = execute_cdms_label_tool(
        "What about safety precautions?",
        conversation_context=conversation_context
    )
    
    if result2.get("success"):
        product2 = result2.get("data", {}).get("product_name", "Unknown")
        print(f"   ✅ Product extracted from context: {product2}")
        if product2.lower() == "roundup":
            print(f"   ✅ Correctly identified Roundup from context!")
        else:
            print(f"   ⚠️  Expected 'Roundup', got '{product2}'")
    else:
        print(f"   ❌ Failed: {result2.get('error')}")
    
    print("\n" + "=" * 80)


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("Follow-up Questions Testing")
    print("=" * 80)
    print("\nThis will test:")
    print("1. Follow-up questions with conversation context")
    print("2. Product name extraction from context")
    print("\n" + "=" * 80)
    
    try:
        test_followup_questions()
        test_product_extraction_from_context()
        
        print("\n" + "=" * 80)
        print("✅ All tests complete!")
        print("=" * 80)
        print("\n💡 The agent should now be able to:")
        print("   - Understand follow-up questions using conversation context")
        print("   - Extract product names from previous messages")
        print("   - Provide relevant answers based on context")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()






