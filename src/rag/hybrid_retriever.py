"""
Hybrid Retriever
Combines traditional keyword matching with vector semantic search
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import List, Dict
from rapidfuzz import fuzz
from src.rag.vector_store import QdrantVectorStore
from src.rag.embeddings import OpenAIEmbeddingService
from src.config.credentials import CredentialsManager
import json


class HybridRetriever:
    """
    Hybrid retrieval system combining:
    1. Traditional fuzzy keyword matching (for API catalog)
    2. Vector semantic search (for PDF documents)
    
    Usage:
        retriever = HybridRetriever()
        results = retriever.retrieve("How do I use the weather API?", top_k=5)
    """
    
    def __init__(self):
        """Initialize hybrid retriever"""
        # Initialize components
        try:
            self.vector_store = QdrantVectorStore()
        except Exception:
            self.vector_store = None
        
        try:
            creds = CredentialsManager()
            openai_key = creds.get_api_key("openai")
            self.embedding_service = OpenAIEmbeddingService(api_key=openai_key)
        except Exception:
            self.embedding_service = None
        
        # Load API catalog
        self.api_catalog = self._load_api_catalog()
        
        # Weights for hybrid scoring
        self.fuzzy_weight = 0.4
        self.semantic_weight = 0.6
    
    def _load_api_catalog(self) -> List[Dict]:
        """Load API catalog from JSON file"""
        try:
            catalog_path = Path(__file__).parent.parent / "api_catalog.json"
            with open(catalog_path, 'r') as f:
                data = json.load(f)
                return data.get("apis", [])
        except Exception:
            return []
    
    def retrieve(self, query: str, top_k: int = 10) -> Dict:
        """
        Perform hybrid retrieval
        
        Args:
            query: User's question
            top_k: Number of results to return
        
        Returns:
            Dict with:
            {
                "results": [matched APIs with scores],
                "document_context": [relevant PDF chunks]
            }
        """
        # 1. Traditional fuzzy matching for API catalog
        api_matches = self._fuzzy_match_apis(query)
        
        # 2. Vector semantic search for PDF documents
        document_context = []
        if self.embedding_service and self.vector_store:
            try:
                query_embedding = self.embedding_service.generate_embedding(query)
                if query_embedding:
                    document_context = self.vector_store.search_documents(
                        query_embedding, 
                        limit=10  # Increased from 5 to get more results
                    )
                else:
                    print("⚠️  Warning: Failed to generate embedding")
            except Exception as e:
                import traceback
                print(f"⚠️  Warning: Vector search failed: {e}")
                traceback.print_exc()
        
        return {
            "results": api_matches[:top_k],
            "document_context": document_context
        }
    
    def _fuzzy_match_apis(self, query: str) -> List[Dict]:
        """
        Match query against API catalog using fuzzy matching
        
        Args:
            query: User's question
        
        Returns:
            List of matched APIs with scores
        """
        matches = []
        query_lower = query.lower()
        
        for api in self.api_catalog:
            if not api.get("enabled", False):
                continue
            
            # Calculate match score
            score = 0
            matches_found = 0
            
            # Check keywords
            keywords = api.get("keywords", [])
            for keyword in keywords:
                similarity = fuzz.partial_ratio(query_lower, keyword.lower())
                if similarity > 70:
                    score += similarity
                    matches_found += 1
            
            # Check description
            description = api.get("description", "")
            desc_similarity = fuzz.partial_ratio(query_lower, description.lower())
            if desc_similarity > 60:
                score += desc_similarity * 0.5
                matches_found += 1
            
            # Check name
            name = api.get("name", "")
            name_similarity = fuzz.ratio(query_lower, name.lower())
            if name_similarity > 50:
                score += name_similarity * 0.3
                matches_found += 1
            
            # Normalize score
            if matches_found > 0:
                final_score = min(score / (matches_found * 2), 100)
                if final_score > 50:  # Minimum threshold
                    matches.append({
                        "api_name": api.get("name", ""),
                        "description": description,
                        "score": round(final_score, 2),
                        "api_type": api.get("api_type", ""),
                        "tags": api.get("tags", [])
                    })
        
        # Sort by score (descending)
        matches.sort(key=lambda x: x["score"], reverse=True)
        
        return matches


# Test function
if __name__ == "__main__":
    print("Testing Hybrid Retriever...")
    print("-" * 70)
    
    retriever = HybridRetriever()
    
    test_queries = [
        "How do I use the weather API?",
        "What's the weather API?",
        "Show me API documentation"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 70)
        
        results = retriever.retrieve(query)
        
        print(f"✅ Found {len(results['results'])} API matches")
        for api in results['results'][:3]:
            print(f"   • {api['api_name']}: {api['score']}% match")
        
        print(f"✅ Found {len(results['document_context'])} document chunks")
        for doc in results['document_context'][:2]:
            print(f"   • {doc['source_file']}: {doc['score']:.2f} similarity")

