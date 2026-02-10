"""
Test Full RAG Pipeline - Phase 4
Tests the complete CDMS tool with full RAG pipeline integration
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.tools.cdms_label_tool import CDMSLabelTool, execute_cdms_label_tool


def test_full_rag_pipeline():
    """Test the full RAG pipeline method"""
    print("=" * 80)
    print("TEST 1: Full RAG Pipeline (search_with_rag)")
    print("=" * 80)
    
    try:
        tool = CDMSLabelTool()
        
        print("\n🔍 Testing: 'What's the application rate for Roundup?'")
        print("-" * 80)
        
        result = tool.search_with_rag(
            product_name="Roundup",
            user_question="What's the application rate for Roundup?",
            active_ingredient="glyphosate"
        )
        
        if not result.get("success"):
            print(f"❌ Pipeline failed: {result.get('error')}")
            return False
        
        print(f"✅ Pipeline successful!")
        print(f"\n📊 Results:")
        print(f"   Product: {result['product_name']}")
        print(f"   PDFs downloaded: {result['pdfs_downloaded']}")
        print(f"   PDFs indexed: {result['pdfs_indexed']}")
        print(f"   RAG chunks found: {result['total_chunks_found']}")
        
        # Show RAG chunks with page numbers
        rag_chunks = result.get("rag_chunks", [])
        if rag_chunks:
            print(f"\n📄 RAG Chunks with Page Citations:")
            for i, chunk in enumerate(rag_chunks[:3], 1):  # Show first 3
                print(f"\n   {i}. Score: {chunk['score']:.3f}")
                print(f"      Page: {chunk['page_number']}")
                print(f"      File: {chunk['source_file']}")
                print(f"      Content: {chunk['content'][:150]}...")
        else:
            print(f"\n   ⚠️  No RAG chunks found (PDFs may need indexing)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_execute_function():
    """Test the execute_cdms_label_tool function"""
    print("\n" + "=" * 80)
    print("TEST 2: execute_cdms_label_tool Function")
    print("=" * 80)
    
    try:
        print("\n🔍 Testing with: 'What's the application rate for Roundup?'")
        print("-" * 80)
        
        result = execute_cdms_label_tool("What's the application rate for Roundup?")
        
        if not result.get("success"):
            print(f"❌ Execution failed: {result.get('error')}")
            return False
        
        print(f"✅ Execution successful!")
        
        data = result.get("data", {})
        print(f"\n📊 Results:")
        print(f"   Product: {data.get('product_name')}")
        print(f"   PDFs downloaded: {data.get('pdfs_downloaded', 0)}")
        print(f"   PDFs indexed: {data.get('pdfs_indexed', 0)}")
        print(f"   RAG chunks: {data.get('total_chunks_found', 0)}")
        
        # Show RAG chunks
        rag_chunks = data.get("rag_chunks", [])
        if rag_chunks:
            print(f"\n📄 Top RAG Chunks:")
            for i, chunk in enumerate(rag_chunks[:2], 1):
                print(f"   {i}. Page {chunk['page_number']}: {chunk['content'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_different_questions():
    """Test with different question types"""
    print("\n" + "=" * 80)
    print("TEST 3: Different Question Types")
    print("=" * 80)
    
    questions = [
        ("Find Roundup label", "Roundup"),
        ("What are the safety precautions for Roundup?", "Roundup"),
        ("Show me mixing instructions for Roundup", "Roundup")
    ]
    
    results = []
    
    for question, expected_product in questions:
        print(f"\n🔍 Question: '{question}'")
        print("-" * 80)
        
        try:
            result = execute_cdms_label_tool(question)
            
            if result.get("success"):
                data = result.get("data", {})
                chunks = data.get("rag_chunks", [])
                print(f"   ✅ Found {len(chunks)} RAG chunk(s)")
                if chunks:
                    print(f"   📄 Example: Page {chunks[0]['page_number']}")
                results.append(True)
            else:
                print(f"   ⚠️  {result.get('error')}")
                results.append(False)
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append(False)
    
    passed = sum(1 for r in results if r)
    print(f"\n   Results: {passed}/{len(results)} questions successful")
    
    return passed == len(results)


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("Full RAG Pipeline - Phase 4 Testing")
    print("=" * 80)
    print("\nThis will test:")
    print("1. Full RAG pipeline method (search_with_rag)")
    print("2. execute_cdms_label_tool function")
    print("3. Different question types")
    print("\n" + "=" * 80)
    
    test_results = []
    
    # Test 1: Full RAG Pipeline
    try:
        success = test_full_rag_pipeline()
        test_results.append(("Full RAG Pipeline", success))
    except Exception as e:
        print(f"❌ Test failed: {e}")
        test_results.append(("Full RAG Pipeline", False))
    
    # Test 2: Execute Function
    try:
        success = test_execute_function()
        test_results.append(("execute_cdms_label_tool", success))
    except Exception as e:
        print(f"❌ Test failed: {e}")
        test_results.append(("execute_cdms_label_tool", False))
    
    # Test 3: Different Questions
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
        print("\n🎉 All tests passed! Phase 4 full RAG pipeline is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    main()






