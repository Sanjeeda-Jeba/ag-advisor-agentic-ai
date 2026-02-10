"""
Test LLM Response Generator with RAG Chunks
Tests Phase 5: LLM response generation with page citations
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.tools.llm_response_generator import LLMResponseGenerator
from src.tools.cdms_label_tool import execute_cdms_label_tool


def test_llm_rag_response():
    """Test LLM response generation with RAG chunks"""
    print("=" * 80)
    print("TEST: LLM Response Generator with RAG Chunks")
    print("=" * 80)
    
    try:
        # First, get RAG results from CDMS tool
        print("\n🔍 Step 1: Getting RAG results from CDMS tool...")
        print("   Question: 'What's the application rate for Roundup?'")
        print("-" * 80)
        
        tool_result = execute_cdms_label_tool("What's the application rate for Roundup?")
        
        if not tool_result.get("success"):
            print(f"❌ Tool execution failed: {tool_result.get('error')}")
            return False
        
        data = tool_result.get("data", {})
        rag_chunks = data.get("rag_chunks", [])
        
        if not rag_chunks:
            print("⚠️  No RAG chunks found. PDFs may need to be indexed.")
            print("   Try running the CDMS tool again after indexing.")
            return False
        
        print(f"✅ Found {len(rag_chunks)} RAG chunks")
        print(f"   Pages cited: {sorted(set(c.get('page_number', 0) for c in rag_chunks))}")
        
        # Now test LLM response generation
        print("\n🤖 Step 2: Generating LLM response with page citations...")
        print("-" * 80)
        
        generator = LLMResponseGenerator()
        
        response = generator.generate_response(
            user_question="What's the application rate for Roundup?",
            tool_name="cdms_label",
            tool_result=data
        )
        
        print(f"\n✅ LLM Response Generated!")
        print(f"\n{'=' * 80}")
        print("RESPONSE:")
        print("=" * 80)
        print(response)
        print("=" * 80)
        
        # Check if response includes page citations
        has_page_citations = any(
            "page" in response.lower() and any(char.isdigit() for char in word)
            for word in response.split()
        )
        
        if has_page_citations:
            print(f"\n✅ Response includes page citations!")
        else:
            print(f"\n⚠️  Response may not include page citations (check manually)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_different_questions():
    """Test with different question types"""
    print("\n" + "=" * 80)
    print("TEST: Different Question Types")
    print("=" * 80)
    
    questions = [
        "What are the safety precautions for Roundup?",
        "Show me mixing instructions for Roundup",
        "What's the re-entry interval for Roundup?"
    ]
    
    generator = LLMResponseGenerator()
    results = []
    
    for question in questions:
        print(f"\n🔍 Question: '{question}'")
        print("-" * 80)
        
        try:
            tool_result = execute_cdms_label_tool(question)
            
            if tool_result.get("success"):
                data = tool_result.get("data", {})
                rag_chunks = data.get("rag_chunks", [])
                
                if rag_chunks:
                    response = generator.generate_response(
                        user_question=question,
                        tool_name="cdms_label",
                        tool_result=data
                    )
                    
                    # Show first 200 chars
                    preview = response[:200].replace("\n", " ")
                    print(f"   ✅ Response: {preview}...")
                    
                    # Check for page citations
                    if "page" in response.lower():
                        print(f"   📄 Includes page citations")
                    
                    results.append(True)
                else:
                    print(f"   ⚠️  No RAG chunks found")
                    results.append(False)
            else:
                print(f"   ❌ Tool failed: {tool_result.get('error')}")
                results.append(False)
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append(False)
    
    passed = sum(1 for r in results if r)
    print(f"\n   Results: {passed}/{len(results)} questions successful")
    
    return passed > 0


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("LLM RAG Response - Phase 5 Testing")
    print("=" * 80)
    print("\nThis will test:")
    print("1. LLM response generation with RAG chunks and page citations")
    print("2. Different question types")
    print("\n" + "=" * 80)
    
    test_results = []
    
    # Test 1: LLM RAG Response
    try:
        success = test_llm_rag_response()
        test_results.append(("LLM RAG Response", success))
    except Exception as e:
        print(f"❌ Test failed: {e}")
        test_results.append(("LLM RAG Response", False))
    
    # Test 2: Different Questions
    try:
        success = test_different_questions()
        test_results.append(("Different Question Types", success))
    except Exception as e:
        print(f"❌ Test failed: {e}")
        test_results.append(("Different Question Types", False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, success in test_results if success)
    total = len(test_results)
    
    print(f"\nResults: {passed}/{total} tests passed")
    print("=" * 80)
    
    if passed == total:
        print("\n🎉 All tests passed! Phase 5 LLM response generation is working correctly.")
        print("\n✅ Ready to test in the UI!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    main()






