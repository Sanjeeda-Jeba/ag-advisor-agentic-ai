"""
Agriculture Web Search Tool
General agriculture and farming information search with citations
"""

from typing import Dict, Any
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api_clients.tavily_client import TavilyAPIClient


class AgricultureWebTool:
    """
    Tool for searching general agriculture information on the web
    
    Uses Tavily for broad web searches about:
    - Farming practices
    - Crop management
    - Pest control strategies
    - Agricultural research
    - Best practices
    - And more
    
    Includes full citations for all sources
    """
    
    def __init__(self):
        """Initialize the agriculture web search tool"""
        self.client = TavilyAPIClient()
        self.tool_name = "agriculture_web_search"
        self.description = "Search the web for agriculture and farming information, best practices, and research"
    
    def search(
        self,
        query: str,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search for agriculture information on the web
        
        Args:
            query: Natural language search query (e.g., "How to control aphids on tomatoes?")
            max_results: Maximum number of results to return (1-5)
        
        Returns:
            Dict with:
                - success: bool
                - query: str (original query)
                - answer: str (AI-generated answer)
                - sources: List[Dict] with:
                    - title: str
                    - url: str
                    - snippet: str
                    - relevance: float (0-1)
                - source_count: int
                - citations: str (formatted citation text)
        """
        # Perform search via Tavily client
        raw_results = self.client.search_agriculture_web(
            query=query,
            max_results=max_results
        )
        
        if not raw_results.get("success"):
            return {
                "success": False,
                "error": raw_results.get("error", "Search failed"),
                "query": query,
                "sources": [],
                "source_count": 0
            }
        
        # Format results with full citation info
        sources = []
        for result in raw_results.get("results", []):
            source = {
                "title": result.get("title", "No title"),
                "url": result.get("url", ""),
                "snippet": result.get("content", "")[:400],  # First 400 chars
                "relevance": result.get("score", 0.0)
            }
            sources.append(source)
        
        # Generate formatted citations
        citations = self._format_citations(sources)
        
        # Build response
        return {
            "success": True,
            "query": query,
            "answer": raw_results.get("answer", ""),
            "sources": sources,
            "source_count": len(sources),
            "citations": citations,
            "search_metadata": raw_results.get("search_metadata", {})
        }
    
    def _format_citations(self, sources: list) -> str:
        """
        Format sources as citation text
        
        Args:
            sources: List of source results
        
        Returns:
            Formatted citation string
        """
        if not sources:
            return "No citations available."
        
        citation_parts = ["**Sources:**\n"]
        
        for i, source in enumerate(sources, 1):
            citation_parts.append(
                f"{i}. **{source['title']}**\n"
                f"   - URL: {source['url']}\n"
                f"   - Relevance: {source['relevance']:.2f}\n"
            )
        
        return "\n".join(citation_parts)
    
    def format_response_for_user(self, result: Dict[str, Any]) -> str:
        """
        Format search results for user-friendly display
        
        Args:
            result: Search result from search()
        
        Returns:
            Formatted string for display to user
        """
        if not result.get("success"):
            return f"❌ Search failed: {result.get('error', 'Unknown error')}"
        
        query = result.get("query", "Unknown query")
        answer = result.get("answer", "")
        sources = result.get("sources", [])
        
        # Build response
        response_parts = []
        
        # Header
        response_parts.append(f"**Web Search Results for:** {query}\n")
        
        # AI Answer
        if answer:
            response_parts.append(f"**Answer:** {answer}\n")
        
        # Sources found
        response_parts.append(f"**Found {len(sources)} source(s):**\n")
        
        for i, source in enumerate(sources, 1):
            response_parts.append(
                f"{i}. **{source['title']}**\n"
                f"   🔗 Link: {source['url']}\n"
                f"   📝 Snippet: {source['snippet'][:200]}...\n"
            )
        
        # Citations
        response_parts.append(f"\n{result.get('citations', '')}")
        
        return "\n".join(response_parts)


def execute_agriculture_web_tool(question: str, conversation_context: list = None) -> Dict:
    """
    Execute agriculture web search tool
    Uses conversation context for follow-up questions
    
    This is the interface for the tool executor.
    Searches the web for agriculture information based on the question.
    
    Args:
        question: User's natural language question
        conversation_context: Optional list of previous messages for context
            Format: [{"role": "user/assistant", "content": "..."}, ...]
    
    Returns:
        Dict with:
        {
            "success": True/False,
            "tool": "agriculture_web",
            "data": {...search results with citations...},
            "error": "error message" if failed
        }
    
    Examples:
        >>> # Follow-up example:
        >>> execute_agriculture_web_tool("What about organic methods?", 
        ...     [{"role": "user", "content": "How to control aphids?"}])
        # Uses context to search for "organic methods to control aphids"
    """
    try:
        # Enhance query with context if this looks like a follow-up
        enhanced_query = question
        
        if conversation_context:
            # Check if current question is vague/short (likely a follow-up)
            question_lower = question.lower()
            is_vague = len(question.split()) <= 5 or any(
                phrase in question_lower for phrase in [
                    "what about", "how about", "tell me more", "and", "also"
                ]
            )
            
            if is_vague:
                # Look for topic/product in previous messages
                for msg in reversed(conversation_context):
                    content = msg.get("content", "")
                    if not content:
                        continue
                    
                    content_lower = content.lower()
                    # Check if previous message was agriculture-related
                    is_ag_related = any(
                        kw in content_lower for kw in [
                            "agriculture", "farming", "crop", "pest", "soil", "fertilizer",
                            "aphid", "tomato", "corn", "wheat", "organic", "pesticide"
                        ]
                    )
                    
                    if is_ag_related:
                        # Enhance query with context
                        # Extract key terms from previous message
                        import re
                        # Get first few meaningful words from previous message
                        words = re.findall(r'\b\w+\b', content_lower)
                        # Filter out common words
                        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 
                                     'to', 'for', 'of', 'and', 'or', 'how', 'what', 'tell', 'me', 'about'}
                        key_terms = [w for w in words if w not in stop_words and len(w) > 3][:3]
                        
                        if key_terms:
                            # Combine: "organic methods" + "aphids" -> "organic methods to control aphids"
                            enhanced_query = f"{question} {', '.join(key_terms)}"
                        break
        
        # For web search, we can pass the enhanced query
        # Tavily will handle the search query optimization
        
        tool = AgricultureWebTool()
        result = tool.search(
            query=enhanced_query,
            max_results=3
        )
        
        if not result.get("success"):
            return {
                "success": False,
                "tool": "agriculture_web",
                "error": result.get("error", "Web search failed")
            }
        
        # Return successful result with citation data
        return {
            "success": True,
            "tool": "agriculture_web",
            "data": result
        }
    
    except Exception as e:
        return {
            "success": False,
            "tool": "agriculture_web",
            "error": f"Unexpected error: {str(e)}"
        }


# Test the tool
if __name__ == "__main__":
    print("=" * 80)
    print("Testing Agriculture Web Search Tool with Citations")
    print("=" * 80)
    
    tool = AgricultureWebTool()
    
    # Test 1: Pest control question
    print("\nTEST 1: Pest control question")
    print("-" * 80)
    
    result = tool.search(
        query="How to control aphids on tomato plants organically?",
        max_results=3
    )
    
    print(tool.format_response_for_user(result))
    
    # Test 2: Crop management question
    print("\n" + "=" * 80)
    print("TEST 2: Crop management question")
    print("-" * 80)
    
    result = tool.search(
        query="Best practices for corn fertilization timing",
        max_results=3
    )
    
    print(tool.format_response_for_user(result))
    
    # Test 3: Soil health question
    print("\n" + "=" * 80)
    print("TEST 3: Soil health question")
    print("-" * 80)
    
    result = tool.search(
        query="How to improve soil organic matter in sandy soils?",
        max_results=3
    )
    
    print(tool.format_response_for_user(result))
    
    print("\n" + "=" * 80)
    print("✅ All tests complete!")
    print("=" * 80)

