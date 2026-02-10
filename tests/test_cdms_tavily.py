"""
Test Script: CDMS Label Search via Tavily
Tests different query formats to find the best approach for finding CDMS pesticide labels
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tavily import TavilyClient
from src.config.credentials import CredentialsManager


def test_cdms_search():
    """Test different query formats for CDMS label searches"""
    
    print("=" * 80)
    print("🧪 Testing CDMS Label Search via Tavily")
    print("=" * 80)
    
    # Get API key
    try:
        creds = CredentialsManager()
        api_key = creds.get_api_key("tavily")
        
        if not api_key:
            print("\n❌ ERROR: Tavily API key not found!")
            print("Please add TAVILY_API_KEY to your .env file")
            print("See TAVILY_SETUP_GUIDE.md for instructions")
            return
        
        print(f"\n✅ Tavily API key loaded")
        
    except Exception as e:
        print(f"\n❌ Error loading API key: {e}")
        return
    
    # Initialize Tavily client
    try:
        client = TavilyClient(api_key=api_key)
        print("✅ Tavily client initialized\n")
    except Exception as e:
        print(f"❌ Failed to initialize Tavily: {e}")
        return
    
    # Test product: Roundup (very common, should be easy to find)
    test_product = "Roundup"
    test_ingredient = "glyphosate"
    
    print(f"🎯 Test Product: {test_product} ({test_ingredient})")
    print("-" * 80)
    
    # Test different query formats
    query_formats = [
        {
            "name": "Format 1: Simple",
            "query": f"{test_product} label",
            "description": "Just product + label",
            "domains": None
        },
        {
            "name": "Format 2: Add Ingredient",
            "query": f"{test_product} {test_ingredient} label",
            "description": "Product + ingredient + label",
            "domains": None
        },
        {
            "name": "Format 3: Add CDMS",
            "query": f"CDMS {test_product} {test_ingredient} label",
            "description": "CDMS + product + ingredient + label",
            "domains": None
        },
        {
            "name": "Format 4: Full Context",
            "query": f"CDMS California {test_product} {test_ingredient} pesticide product label EPA",
            "description": "Full context with CDMS, California, EPA",
            "domains": None
        },
        {
            "name": "Format 5: CDMS Domain Filter (Tavily Parameter)",
            "query": f"{test_product} {test_ingredient} pesticide label",
            "description": "Using Tavily's include_domains parameter to target CDMS",
            "domains": ["cdms.net"]
        },
        {
            "name": "Format 6: Domain Filter + Keywords",
            "query": f"{test_product} {test_ingredient} product label EPA registration",
            "description": "Domain filter + comprehensive keywords",
            "domains": ["cdms.net"]
        },
        {
            "name": "Format 7: CDMS.net + Simple Query",
            "query": f"{test_product} label",
            "description": "Simple query with cdms.net domain filter",
            "domains": ["cdms.net"]
        }
    ]
    
    results_summary = []
    
    for i, query_format in enumerate(query_formats, 1):
        print(f"\n{'=' * 80}")
        print(f"Test {i}/{len(query_formats)}: {query_format['name']}")
        print(f"Description: {query_format['description']}")
        print(f"Query: \"{query_format['query']}\"")
        print("-" * 80)
        
        try:
            # Search
            search_params = {
                "query": query_format['query'],
                "max_results": 5,
                "search_depth": "advanced",
                "include_answer": True
            }
            
            # Add domain filter if specified
            if query_format.get('domains'):
                search_params["include_domains"] = query_format['domains']
                print(f"🔍 Filtering to domains: {query_format['domains']}")
            
            response = client.search(**search_params)
            
            results = response.get("results", [])
            answer = response.get("answer", "")
            
            print(f"\n📊 Results: {len(results)} found")
            
            # Check if any results are from CDMS
            cdms_results = []
            other_results = []
            
            for result in results:
                url = result.get("url", "").lower()
                title = result.get("title", "")
                
                # Check for cdms.net (the actual CDMS database)
                if "cdms.net" in url or "cdpr.ca.gov" in url:
                    cdms_results.append(result)
                else:
                    other_results.append(result)
            
            print(f"   ✅ CDMS Results: {len(cdms_results)}")
            print(f"   ⚠️  Other Results: {len(other_results)}")
            
            # Show CDMS results
            if cdms_results:
                print(f"\n✅ CDMS Results Found:")
                for idx, result in enumerate(cdms_results[:3], 1):
                    print(f"   {idx}. {result.get('title', 'No title')}")
                    print(f"      URL: {result.get('url', 'No URL')}")
                    print(f"      Snippet: {result.get('content', '')[:150]}...")
                    print()
            else:
                print(f"\n⚠️  No CDMS results found")
            
            # Show Tavily's AI answer if available
            if answer:
                print(f"🤖 Tavily AI Answer:")
                print(f"   {answer[:300]}...")
                print()
            
            # Store summary
            results_summary.append({
                "format": query_format['name'],
                "query": query_format['query'],
                "total_results": len(results),
                "cdms_results": len(cdms_results),
                "has_answer": bool(answer),
                "score": len(cdms_results) * 10 + len(results)  # Simple scoring
            })
            
        except Exception as e:
            print(f"❌ Error: {e}")
            results_summary.append({
                "format": query_format['name'],
                "query": query_format['query'],
                "error": str(e),
                "score": 0
            })
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY: Which Query Format Works Best?")
    print("=" * 80)
    
    # Sort by score
    results_summary.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    for i, summary in enumerate(results_summary, 1):
        if 'error' in summary:
            print(f"\n{i}. {summary['format']}")
            print(f"   ❌ Error: {summary['error']}")
        else:
            print(f"\n{i}. {summary['format']}")
            print(f"   Query: \"{summary['query']}\"")
            print(f"   CDMS Results: {summary['cdms_results']}")
            print(f"   Total Results: {summary['total_results']}")
            print(f"   Has AI Answer: {'Yes' if summary['has_answer'] else 'No'}")
            print(f"   Score: {summary['score']}")
    
    # Recommendation
    best = results_summary[0]
    print(f"\n{'=' * 80}")
    print(f"🏆 RECOMMENDED FORMAT:")
    print(f"   {best['format']}")
    print(f"   Query: \"{best['query']}\"")
    print(f"   Reason: Found {best.get('cdms_results', 0)} CDMS results")
    print("=" * 80)
    
    print(f"\n✅ Testing complete!")
    print(f"\n💡 Next Steps:")
    print(f"   1. Use the recommended format in your CDMS tool")
    print(f"   2. Proceed with full implementation (Phase 2)")
    print(f"   3. Test with more products to validate")


if __name__ == "__main__":
    test_cdms_search()

