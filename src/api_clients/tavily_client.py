"""
Tavily API Client
Handles web searches with citation tracking for CDMS labels and agriculture information
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api_clients.base_client import BaseAPIClient
from src.config.credentials import CredentialsManager

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None


class TavilyAPIClient(BaseAPIClient):
    """
    Client for Tavily Search API
    Supports domain-filtered searches with full citation tracking
    """
    
    def __init__(self):
        super().__init__()
        
        if TavilyClient is None:
            raise ImportError(
                "tavily-python not installed. Run: pip install tavily-python"
            )
        
        # Get API key
        creds = CredentialsManager()
        api_key = creds.get_api_key("tavily")
        
        if not api_key:
            raise ValueError(
                "Tavily API key not found. Please add TAVILY_API_KEY to .env file"
            )
        
        # Initialize Tavily client
        self.client = TavilyClient(api_key=api_key)
    
    def _validate_params(self, **kwargs) -> bool:
        """
        Validate Tavily search parameters
        
        Args:
            query: Search query (required)
            max_results: Maximum results (optional, 1-10)
            search_depth: "basic" or "advanced" (optional)
        
        Returns:
            bool: True if valid, False otherwise
        """
        # Require query
        if "query" not in kwargs or not kwargs["query"]:
            return False
        
        # Validate max_results if provided
        if "max_results" in kwargs:
            max_results = kwargs["max_results"]
            if not isinstance(max_results, int) or max_results < 1 or max_results > 10:
                return False
        
        # Validate search_depth if provided
        if "search_depth" in kwargs:
            depth = kwargs["search_depth"]
            if depth not in ["basic", "advanced"]:
                return False
        
        return True
    
    def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "advanced",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        include_answer: bool = True,
        include_raw_content: bool = False
    ) -> Dict[str, Any]:
        """
        Perform a web search with Tavily
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return (1-10)
            search_depth: "basic" or "advanced" (more thorough)
            include_domains: List of domains to limit search to (e.g., ["cdms.net"])
            exclude_domains: List of domains to exclude from search
            include_answer: Whether to include Tavily's AI-generated answer
            include_raw_content: Whether to include full page content
        
        Returns:
            Dict with:
                - success: bool
                - query: str (original query)
                - answer: str (AI summary, if requested)
                - results: List[Dict] with citations:
                    - title: str
                    - url: str
                    - content: str (snippet)
                    - score: float (relevance score)
                    - raw_content: str (full content, if requested)
                - result_count: int
                - search_metadata: Dict (search parameters used)
        """
        try:
            # Prepare search parameters
            search_params = {
                "query": query,
                "max_results": max_results,
                "search_depth": search_depth,
                "include_answer": include_answer,
                "include_raw_content": include_raw_content
            }
            
            # Add domain filters if specified
            if include_domains:
                search_params["include_domains"] = include_domains
            
            if exclude_domains:
                search_params["exclude_domains"] = exclude_domains
            
            # Perform search
            response = self.client.search(**search_params)
            
            # Extract results with full citation info
            results = response.get("results", [])
            formatted_results = []
            
            for result in results:
                citation = {
                    "title": result.get("title", "No title"),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0),
                }
                
                # Add raw content if available
                if include_raw_content and "raw_content" in result:
                    citation["raw_content"] = result.get("raw_content", "")
                
                formatted_results.append(citation)
            
            # Build response
            return {
                "success": True,
                "query": query,
                "answer": response.get("answer", ""),
                "results": formatted_results,
                "result_count": len(formatted_results),
                "search_metadata": {
                    "search_depth": search_depth,
                    "include_domains": include_domains,
                    "exclude_domains": exclude_domains,
                    "max_results": max_results
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Tavily search failed: {str(e)}",
                "query": query,
                "results": [],
                "result_count": 0
            }
    
    def search_cdms_labels(
        self,
        product_name: str,
        active_ingredient: Optional[str] = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search specifically for CDMS pesticide labels
        Uses domain filtering to ensure results are from cdms.net
        
        Args:
            product_name: Product/brand name (e.g., "Roundup")
            active_ingredient: Optional active ingredient (e.g., "glyphosate")
            max_results: Maximum number of results
        
        Returns:
            Search results with CDMS-specific formatting and citations
        """
        # Build query - optimize for CDMS search
        # Tavily doesn't support Google-style operators like "site:" or "filetype:"
        # Instead, we use domain filtering via include_domains parameter
        # Build natural language query that works well with Tavily
        
        # Clean product name (remove special characters that might confuse search)
        # But keep important ones like "%" for products like "Actagro 10% Boron"
        clean_product_name = product_name.strip()
        
        # Build query with CDMS context
        if active_ingredient:
            # Include both product name and ingredient
            query = f"{clean_product_name} {active_ingredient} pesticide label CDMS"
        else:
            # Just product name with CDMS context
            query = f"{clean_product_name} pesticide label CDMS"
        
        # Search with domain filter (this is how Tavily restricts to cdms.net)
        results = self.search(
            query=query,
            max_results=max_results * 2,  # Get more results to filter for PDFs
            search_depth="advanced",
            include_domains=["cdms.net"],  # Only CDMS results!
            include_answer=True,
            include_raw_content=False  # Can enable if needed
        )
        
        # Filter results to prioritize PDFs
        if results.get("success"):
            all_results = results.get("results", [])
            pdf_results = []
            html_results = []
            
            # Separate PDFs from HTML pages
            for result in all_results:
                url = result.get("url", "")
                if url.lower().endswith('.pdf') or '/ldat/' in url.lower():
                    pdf_results.append(result)
                else:
                    html_results.append(result)
            
            # Prioritize PDFs: take PDFs first, then HTML pages if needed
            prioritized_results = pdf_results[:max_results]
            if len(prioritized_results) < max_results:
                # Add HTML pages if we don't have enough PDFs
                remaining = max_results - len(prioritized_results)
                prioritized_results.extend(html_results[:remaining])
            
            # Update results with prioritized list
            results["results"] = prioritized_results
            results["result_count"] = len(prioritized_results)
        
        # Add CDMS-specific metadata
        if results.get("success"):
            results["search_type"] = "cdms_label"
            results["product_name"] = product_name
            results["active_ingredient"] = active_ingredient
        
        return results
    
    def search_agriculture_web(
        self,
        query: str,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        General agriculture web search (no domain filtering)
        For broader agriculture questions and information
        
        Args:
            query: Natural language query
            max_results: Maximum number of results
        
        Returns:
            Search results with citations
        """
        results = self.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=False
        )
        
        # Add metadata
        if results.get("success"):
            results["search_type"] = "agriculture_web"
        
        return results


# Test functionality
if __name__ == "__main__":
    print("=" * 80)
    print("Testing Tavily API Client with Citations")
    print("=" * 80)
    
    try:
        client = TavilyAPIClient()
        print("✅ Tavily client initialized\n")
        
        # Test 1: CDMS Label Search
        print("-" * 80)
        print("TEST 1: CDMS Label Search (Roundup)")
        print("-" * 80)
        
        result = client.search_cdms_labels(
            product_name="Roundup",
            active_ingredient="glyphosate",
            max_results=3
        )
        
        if result["success"]:
            print(f"✅ Query: {result['query']}")
            print(f"📊 Found {result['result_count']} results\n")
            
            # Show AI Answer
            if result.get("answer"):
                print(f"🤖 AI Summary:\n{result['answer']}\n")
            
            # Show citations
            print("📚 CITATIONS:")
            for i, citation in enumerate(result["results"], 1):
                print(f"\n{i}. {citation['title']}")
                print(f"   URL: {citation['url']}")
                print(f"   Relevance: {citation['score']:.2f}")
                print(f"   Snippet: {citation['content'][:150]}...")
        else:
            print(f"❌ Error: {result.get('error')}")
        
        # Test 2: General Agriculture Search
        print("\n" + "=" * 80)
        print("TEST 2: General Agriculture Web Search")
        print("=" * 80)
        
        result = client.search_agriculture_web(
            query="best practices for nitrogen fertilizer application in corn",
            max_results=3
        )
        
        if result["success"]:
            print(f"✅ Query: {result['query']}")
            print(f"📊 Found {result['result_count']} results\n")
            
            if result.get("answer"):
                print(f"🤖 AI Summary:\n{result['answer']}\n")
            
            print("📚 CITATIONS:")
            for i, citation in enumerate(result["results"], 1):
                print(f"\n{i}. {citation['title']}")
                print(f"   URL: {citation['url']}")
                print(f"   Relevance: {citation['score']:.2f}")
        else:
            print(f"❌ Error: {result.get('error')}")
        
        print("\n" + "=" * 80)
        print("✅ All tests complete!")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

