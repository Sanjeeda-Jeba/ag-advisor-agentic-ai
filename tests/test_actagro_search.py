"""
Test Actagro 10% Boron search
Debug why CDMS search is not finding this product
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.api_clients.tavily_client import TavilyAPIClient
from src.tools.cdms_label_tool import CDMSLabelTool, execute_cdms_label_tool


def test_actagro_search():
    """Test different search approaches for Actagro 10% Boron"""
    print("=" * 80)
    print("TEST: Actagro 10% Boron CDMS Search")
    print("=" * 80)
    
    client = TavilyAPIClient()
    
    # Test different query formats
    test_queries = [
        # Current format (what the code uses)
        "Actagro 10% Boron site:cdms.net filetype:pdf",
        
        # Variations
        "Actagro 10% Boron site:cdms.net",
        "Actagro Boron site:cdms.net",
        "Actagro 10 Boron site:cdms.net",
        "Actagro site:cdms.net Boron",
        "Actagro label site:cdms.net",
        "Actagro product label site:cdms.net",
        "CDMS Actagro 10% Boron",
        "Actagro 10% Boron pesticide label",
        "Actagro 10% Boron CDMS label",
    ]
    
    print("\n🔍 Testing Different Query Formats")
    print("-" * 80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {query}")
        print("-" * 40)
        
        result = client.search(
            query=query,
            max_results=5,
            search_depth="advanced",
            include_domains=["cdms.net"],
            include_answer=True
        )
        
        if result.get("success"):
            count = result.get("result_count", 0)
            print(f"   ✅ Found {count} results")
            
            if count > 0:
                print(f"   📄 Results:")
                for j, res in enumerate(result.get("results", [])[:3], 1):
                    title = res.get("title", "No title")
                    url = res.get("url", "")
                    score = res.get("score", 0.0)
                    print(f"      {j}. {title[:60]}...")
                    print(f"         URL: {url[:80]}...")
                    print(f"         Score: {score:.2f}")
                    
                    # Check if it mentions Actagro
                    content = res.get("content", "").lower()
                    if "actagro" in content:
                        print(f"         ✅ Mentions 'Actagro'")
                    if "boron" in content:
                        print(f"         ✅ Mentions 'Boron'")
        else:
            print(f"   ❌ Error: {result.get('error')}")
    
    # Test with CDMS tool directly
    print("\n" + "=" * 80)
    print("TEST: Using CDMS Tool Directly")
    print("=" * 80)
    
    tool = CDMSLabelTool()
    
    # Test different product name formats
    product_names = [
        "Actagro 10% Boron",
        "Actagro",
        "Actagro Boron",
        "Actagro 10 Boron",
    ]
    
    for product_name in product_names:
        print(f"\n🔍 Product Name: '{product_name}'")
        print("-" * 80)
        
        result = tool.search(
            product_name=product_name,
            max_results=5
        )
        
        if result.get("success"):
            count = result.get("label_count", 0)
            print(f"   ✅ Found {count} labels")
            print(f"   Query used: {result.get('query_used', 'N/A')}")
            
            if count > 0:
                for j, label in enumerate(result.get("labels", [])[:3], 1):
                    print(f"      {j}. {label['title'][:60]}...")
                    print(f"         URL: {label['url'][:80]}...")
        else:
            print(f"   ❌ Error: {result.get('error')}")
    
    # Test with execute_cdms_label_tool (full pipeline)
    print("\n" + "=" * 80)
    print("TEST: Full Pipeline (execute_cdms_label_tool)")
    print("=" * 80)
    
    test_questions = [
        "Find Actagro 10% Boron label",
        "Actagro 10% Boron",
        "Actagro Boron label",
        "Show me Actagro label",
    ]
    
    for question in test_questions:
        print(f"\n🔍 Question: '{question}'")
        print("-" * 80)
        
        result = execute_cdms_label_tool(question)
        
        if result.get("success"):
            data = result.get("data", {})
            chunks = data.get("rag_chunks", [])
            tavily_labels = data.get("tavily_labels", [])
            
            print(f"   ✅ Success")
            print(f"   RAG chunks: {len(chunks)}")
            print(f"   Tavily labels: {len(tavily_labels)}")
            
            if tavily_labels:
                print(f"   📄 Tavily Results:")
                for j, label in enumerate(tavily_labels[:3], 1):
                    print(f"      {j}. {label.get('title', 'No title')[:60]}...")
        else:
            print(f"   ❌ Error: {result.get('error')}")
            if result.get("should_fallback"):
                print(f"   ⚠️  Should fallback to web search")


if __name__ == "__main__":
    try:
        test_actagro_search()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
