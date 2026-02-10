"""
Integration Test: Tavily Tools with Citations
Tests the complete pipeline from question to answer with full citations
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.tools.tool_executor import ToolExecutor


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_cdms_label_search():
    """Test CDMS label search with citations"""
    print_section("TEST 1: CDMS Label Search")
    
    executor = ToolExecutor()
    
    # Test question
    question = "Find me the Roundup pesticide label"
    
    print(f"\n📝 Question: {question}")
    print(f"🔧 Tool: cdms_label")
    print("-" * 80)
    
    # Execute
    result = executor.execute("cdms_label", question)
    
    if result["success"]:
        print("\n✅ Success!")
        print(f"\n🤖 LLM Response:")
        print(f"{result['llm_response']}")
        
        print(f"\n📊 Raw Data Check:")
        raw_data = result["raw_data"]
        print(f"   Product: {raw_data.get('product_name', 'N/A')}")
        print(f"   Labels Found: {raw_data.get('label_count', 0)}")
        print(f"   Has Citations: {'Yes' if raw_data.get('citations') else 'No'}")
        
        # Show citations
        if raw_data.get('labels'):
            print(f"\n📚 Direct Citations:")
            for i, label in enumerate(raw_data['labels'][:3], 1):
                print(f"   {i}. {label['title']}")
                print(f"      URL: {label['url']}")
    else:
        print(f"\n❌ Failed: {result['error']}")
    
    return result["success"]


def test_agriculture_web_search():
    """Test agriculture web search with citations"""
    print_section("TEST 2: Agriculture Web Search")
    
    executor = ToolExecutor()
    
    # Test question
    question = "How to control aphids on tomato plants?"
    
    print(f"\n📝 Question: {question}")
    print(f"🔧 Tool: agriculture_web")
    print("-" * 80)
    
    # Execute
    result = executor.execute("agriculture_web", question)
    
    if result["success"]:
        print("\n✅ Success!")
        print(f"\n🤖 LLM Response:")
        print(f"{result['llm_response']}")
        
        print(f"\n📊 Raw Data Check:")
        raw_data = result["raw_data"]
        print(f"   Query: {raw_data.get('query', 'N/A')}")
        print(f"   Sources Found: {raw_data.get('source_count', 0)}")
        print(f"   Has AI Answer: {'Yes' if raw_data.get('answer') else 'No'}")
        print(f"   Has Citations: {'Yes' if raw_data.get('citations') else 'No'}")
        
        # Show citations
        if raw_data.get('sources'):
            print(f"\n📚 Direct Citations:")
            for i, source in enumerate(raw_data['sources'][:3], 1):
                print(f"   {i}. {source['title']}")
                print(f"      URL: {source['url']}")
    else:
        print(f"\n❌ Failed: {result['error']}")
    
    return result["success"]


def test_multiple_cdms_products():
    """Test CDMS search with different products"""
    print_section("TEST 3: Multiple CDMS Products")
    
    executor = ToolExecutor()
    
    products = [
        "Sevin label",
        "2,4-D pesticide label",
        "Atrazine label"
    ]
    
    results = []
    
    for product_question in products:
        print(f"\n📝 Question: {product_question}")
        print("-" * 40)
        
        result = executor.execute("cdms_label", product_question)
        
        if result["success"]:
            raw_data = result["raw_data"]
            label_count = raw_data.get('label_count', 0)
            has_citations = bool(raw_data.get('citations'))
            
            print(f"   ✅ Found {label_count} label(s), Citations: {'Yes' if has_citations else 'No'}")
            results.append(True)
        else:
            print(f"   ❌ Failed: {result.get('error')}")
            results.append(False)
    
    success_rate = (sum(results) / len(results)) * 100
    print(f"\n📊 Success Rate: {success_rate:.0f}% ({sum(results)}/{len(results)})")
    
    return all(results)


def test_citation_format():
    """Test that citations are properly formatted"""
    print_section("TEST 4: Citation Format Validation")
    
    executor = ToolExecutor()
    
    # Test CDMS citations
    print("\n🔍 Testing CDMS Citation Format...")
    result = executor.execute("cdms_label", "Roundup label")
    
    if result["success"]:
        raw_data = result["raw_data"]
        citations = raw_data.get('citations', '')
        labels = raw_data.get('labels', [])
        
        # Check citation structure
        checks = {
            "Has citations field": bool(citations),
            "Citations not empty": len(citations) > 0,
            "Has labels": len(labels) > 0,
            "Labels have URLs": all('url' in label for label in labels),
            "Labels have titles": all('title' in label for label in labels),
            "URLs are from CDMS": all('cdms.net' in label.get('url', '') for label in labels)
        }
        
        print("\n✅ CDMS Citation Checks:")
        for check, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"   [{status}] {check}")
        
        cdms_passed = all(checks.values())
    else:
        print(f"   ❌ CDMS search failed: {result.get('error')}")
        cdms_passed = False
    
    # Test web search citations
    print("\n🔍 Testing Web Search Citation Format...")
    result = executor.execute("agriculture_web", "Best fertilizer for corn")
    
    if result["success"]:
        raw_data = result["raw_data"]
        citations = raw_data.get('citations', '')
        sources = raw_data.get('sources', [])
        
        # Check citation structure
        checks = {
            "Has citations field": bool(citations),
            "Citations not empty": len(citations) > 0,
            "Has sources": len(sources) > 0,
            "Sources have URLs": all('url' in source for source in sources),
            "Sources have titles": all('title' in source for source in sources),
        }
        
        print("\n✅ Web Search Citation Checks:")
        for check, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"   [{status}] {check}")
        
        web_passed = all(checks.values())
    else:
        print(f"   ❌ Web search failed: {result.get('error')}")
        web_passed = False
    
    return cdms_passed and web_passed


def main():
    """Run all integration tests"""
    print("=" * 80)
    print("  TAVILY INTEGRATION TEST SUITE")
    print("  Testing: CDMS Labels + Agriculture Web Search with Citations")
    print("=" * 80)
    
    results = {}
    
    try:
        # Run tests
        results['cdms_basic'] = test_cdms_label_search()
        results['web_basic'] = test_agriculture_web_search()
        results['cdms_multiple'] = test_multiple_cdms_products()
        results['citations'] = test_citation_format()
        
        # Summary
        print_section("TEST SUMMARY")
        
        print("\n📊 Results:")
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {status} - {test_name}")
        
        total = len(results)
        passed = sum(results.values())
        success_rate = (passed / total) * 100
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed ({success_rate:.0f}%)")
        
        if all(results.values()):
            print("\n🎉 ALL TESTS PASSED!")
            print("\n✅ Tavily integration is working correctly:")
            print("   - CDMS label search with citations ✓")
            print("   - Agriculture web search with citations ✓")
            print("   - Multiple products supported ✓")
            print("   - Citation formats validated ✓")
            print("\n🚀 Ready for production use!")
        else:
            print("\n⚠️  SOME TESTS FAILED - Review output above")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()





