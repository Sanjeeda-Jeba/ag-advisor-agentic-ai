"""
RAG Tool
Searches documentation and knowledge base for answers
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Dict
from src.rag.hybrid_retriever import HybridRetriever


def execute_rag_tool(question: str) -> Dict:
    """
    Execute RAG tool - search documentation and knowledge base
    
    Args:
        question: User's natural language question
    
    Returns:
        Dict with tool execution result:
        {
            "success": True/False,
            "tool": "rag",
            "data": {
                "api_matches": [...],
                "document_context": [...]
            } or None,
            "error": "error message" if failed
        }
    
    Examples:
        >>> execute_rag_tool("How do I use the weather API?")
        {
            "success": True,
            "tool": "rag",
            "data": {
                "api_matches": [...],
                "document_context": [...]
            }
        }
    """
    try:
        # Initialize hybrid retriever
        retriever = HybridRetriever()
        
        # Search for relevant content
        results = retriever.retrieve(question, top_k=5)
        
        # Check if we found anything
        if not results["results"] and not results["document_context"]:
            return {
                "success": False,
                "tool": "rag",
                "error": "No relevant documentation found. Make sure PDFs are processed: python src/cdms/document_loader.py",
                "data": {
                    "api_matches": [],
                    "document_context": []
                }
            }
        
        # Return successful result
        return {
            "success": True,
            "tool": "rag",
            "data": {
                "api_matches": results["results"],
                "document_context": results["document_context"]
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "tool": "rag",
            "error": f"Unexpected error: {str(e)}"
        }


# Test function
if __name__ == "__main__":
    print("Testing RAG Tool...")
    print("-" * 70)
    
    test_questions = [
        "How do I use the weather API?",
        "What's the weather API?",
        "Show me documentation about APIs",
        "How can I get weather data?"
    ]
    
    for question in test_questions:
        print(f"\n📝 Question: {question}")
        print("-" * 70)
        
        result = execute_rag_tool(question)
        
        if result["success"]:
            print("✅ Success!")
            data = result["data"]
            
            if data["api_matches"]:
                print(f"\n🎯 API Matches ({len(data['api_matches'])}):")
                for api in data["api_matches"][:3]:
                    print(f"   • {api['api_name']}: {api['score']}% match")
            
            if data["document_context"]:
                print(f"\n📚 Document Context ({len(data['document_context'])}):")
                for doc in data["document_context"][:2]:
                    print(f"   • {doc['source_file']}: {doc['score']:.2f} similarity")
                    print(f"     Preview: {doc['content'][:100]}...")
        else:
            print(f"❌ Error: {result['error']}")

