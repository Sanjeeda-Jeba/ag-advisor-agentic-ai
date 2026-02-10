"""
Test Enhanced Follow-up Questions with Context
Tests that the agent can understand follow-up questions using conversation context
for CDMS and agricultural tools
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.tools.tool_executor import ToolExecutor
from src.tools.tool_matcher import ToolMatcher
from src.utils.parameter_extractor import extract_location_from_soil_query


def test_soil_followup():
    """Test soil tool follow-up questions"""
    print("=" * 80)
    print("TEST: Soil Tool Follow-up Questions")
    print("=" * 80)
    
    # Simulate conversation
    conversation = [
        {
            "role": "user",
            "content": "soil data for ames"
        },
        {
            "role": "assistant",
            "content": "I couldn't find a complete location. Could you specify the state? (e.g., 'Ames, Iowa')"
        }
    ]
    
    # Test follow-up
    followup = "Ames iowa"
    print(f"\n📝 Initial Question: {conversation[0]['content']}")
    print(f"🔍 Follow-up Question: '{followup}'")
    print("-" * 80)
    
    # Test location extraction with context
    location_info = extract_location_from_soil_query(followup, conversation_context=conversation)
    
    if location_info:
        print(f"✅ Location extracted: {location_info.get('location')}")
        print("   ✅ Context was used successfully!")
    else:
        print("❌ Failed to extract location")
    
    print()


def test_cdms_followup():
    """Test CDMS tool follow-up questions"""
    print("=" * 80)
    print("TEST: CDMS Tool Follow-up Questions")
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
        ("What about safety?", "safety"),
        ("How do I mix it?", "mixing"),
        ("What's the re-entry interval?", "reentry"),
        ("Show me the label", "label")
    ]
    
    print(f"\n📝 Initial Question: {conversation[0]['content']}")
    print(f"🤖 Initial Response: {conversation[1]['content'][:100]}...")
    print("\n" + "=" * 80)
    
    for followup, expected_type in followup_questions:
        print(f"\n🔍 Follow-up: '{followup}' (expected type: {expected_type})")
        print("-" * 80)
        
        # Extract keywords
        from src.utils.parameter_extractor import extract_keywords_from_query
        keywords = extract_keywords_from_query(followup)
        print(f"   Keywords: {keywords}")
        
        # Match tool (with context)
        tool_match = matcher.match_tool(keywords, followup, conversation_context=conversation)
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


def test_agriculture_web_followup():
    """Test agriculture web tool follow-up questions"""
    print("=" * 80)
    print("TEST: Agriculture Web Tool Follow-up Questions")
    print("=" * 80)
    
    executor = ToolExecutor()
    matcher = ToolMatcher()
    
    # Simulate a conversation
    conversation = [
        {
            "role": "user",
            "content": "How to control aphids on tomato plants?"
        },
        {
            "role": "assistant",
            "content": "Here are some methods to control aphids on tomatoes..."
        }
    ]
    
    # Test follow-up
    followup = "What about organic methods?"
    print(f"\n📝 Initial Question: {conversation[0]['content']}")
    print(f"🔍 Follow-up Question: '{followup}'")
    print("-" * 80)
    
    # Extract keywords
    from src.utils.parameter_extractor import extract_keywords_from_query
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
            
            # Check if response mentions aphids or tomatoes (shows context was used)
            if "aphid" in response.lower() or "tomato" in response.lower():
                print(f"   ✅ Response mentions context (aphids/tomatoes) - context used!")
            else:
                print(f"   ⚠️  Response may not use context")
            
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


def main():
    """Run all follow-up question tests"""
    print("\n" + "=" * 80)
    print("ENHANCED FOLLOW-UP QUESTIONS TEST SUITE")
    print("=" * 80)
    print("\nTesting follow-up question handling for:")
    print("  1. Soil Tool (location extraction with context)")
    print("  2. CDMS Tool (product context for safety, application, etc.)")
    print("  3. Agriculture Web Tool (topic context)")
    print("\n" + "=" * 80)
    
    try:
        # Test 1: Soil follow-up
        test_soil_followup()
        
        # Test 2: CDMS follow-up
        test_cdms_followup()
        
        # Test 3: Agriculture web follow-up
        test_agriculture_web_followup()
        
        print("\n" + "=" * 80)
        print("✅ All follow-up question tests complete!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
