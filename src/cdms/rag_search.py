"""
CDMS RAG Search Module
Searches Qdrant vector database for CDMS label information with page citations
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.rag.vector_store import QdrantVectorStore
from src.rag.embeddings import OpenAIEmbeddingService
from src.config.credentials import CredentialsManager
from qdrant_client.models import Filter, FieldCondition, MatchValue


class CDMSRAGSearch:
    """
    RAG search for CDMS pesticide labels
    
    Searches Qdrant vector database for relevant label information
    with accurate page number tracking
    
    Usage:
        searcher = CDMSRAGSearch()
        results = searcher.search("What's the application rate for Roundup?", product_name="Roundup")
    """
    
    def __init__(self, vector_store: "QdrantVectorStore | None" = None):
        """
        Initialize RAG search components
        
        Args:
            vector_store: Optional shared QdrantVectorStore instance.
                          If None, a new instance is created.
        """
        # Use shared vector store if provided, otherwise create a new one
        if vector_store is not None:
            self.vector_store = vector_store
            print(f"✅ CDMSRAGSearch: using shared vector store")
        else:
            try:
                self.vector_store = QdrantVectorStore()
            except Exception as e:
                print(f"⚠️  Warning: Could not initialize Qdrant: {e}")
                self.vector_store = None
        
        # Initialize embedding service
        try:
            creds = CredentialsManager()
            openai_key = creds.get_api_key("openai")
            self.embedding_service = OpenAIEmbeddingService(api_key=openai_key)
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize OpenAI embeddings: {e}")
            self.embedding_service = None
    
    def search(
        self,
        query: str,
        product_name: Optional[str] = None,
        limit: int = 5,
        score_threshold: float = 0.3
    ) -> List[Dict]:
        """
        Search CDMS documents in Qdrant
        
        Args:
            query: User's question or search query
            product_name: Optional product name to filter results (e.g., "Roundup")
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score (0-1)
        
        Returns:
            List of dicts with:
            {
                "content": str (chunk text),
                "page_number": int (exact page number),
                "source_file": str (PDF filename),
                "score": float (similarity score 0-1),
                "document_id": str,
                "chunk_index": int
            }
        """
        if not self.vector_store or not self.embedding_service:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.generate_embedding(query)
            
            if not query_embedding:
                print("⚠️  Warning: Failed to generate query embedding")
                return []
            
            # ── Primary search: product-scoped via Qdrant native filter ──
            # product_name is passed to Qdrant so only that product's chunks
            # are considered — no cross-product contamination.
            results = self.vector_store.search_documents(
                query_embedding=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                product_name=product_name  # Qdrant-level filter
            )
            
            print(f"   🔍 Found {len(results)} result(s) for product '{product_name or 'all'}'")
            
            # If native filter returned nothing, fall back to unfiltered search
            # (handles legacy chunks indexed without product_name field)
            if len(results) == 0 and product_name:
                print(f"   ⚠️  No results with native filter — trying unfiltered search + post-filter")
                unfiltered = self.vector_store.search_documents(
                    query_embedding=query_embedding,
                    limit=limit * 3,
                    score_threshold=score_threshold * 0.8
                )
                product_lower = product_name.lower()
                for r in unfiltered:
                    source = r.get("source_file", "").lower()
                    doc_name = r.get("metadata", {}).get("document_name", "").lower()
                    content = r.get("content", "").lower()
                    if (product_lower in source or
                        product_lower in doc_name or
                        product_lower in content[:500]):
                        results.append(r)
                results = results[:limit]
                print(f"   🔍 Post-filter fallback: {len(results)} result(s)")
            
            # ── REI keyword boost (product-scoped) ──
            rei_keywords = ["rei", "re-entry", "reentry", "restricted entry"]
            query_lower = query.lower()
            if any(kw in query_lower for kw in rei_keywords):
                has_rei = any(
                    any(kw in r.get("content", "").lower() for kw in rei_keywords)
                    for r in results
                )
                if not has_rei and self.vector_store and self.embedding_service:
                    rei_query = f"{product_name or ''} re-entry interval restricted entry agricultural use requirements"
                    rei_embedding = self.embedding_service.generate_embedding(rei_query)
                    if rei_embedding:
                        # Search with product filter so only this product's REI is returned
                        rei_results = self.vector_store.search_documents(
                            query_embedding=rei_embedding,
                            limit=10,
                            score_threshold=0.2,
                            product_name=product_name
                        )
                        rei_hits = [
                            r for r in rei_results
                            if any(kw in r.get("content", "").lower() for kw in rei_keywords)
                        ]
                        
                        if rei_hits:
                            # Put REI chunks FIRST, then fill remaining slots
                            seen_ids = set()
                            merged = []
                            for r in rei_hits:
                                rid = r.get("id")
                                if rid not in seen_ids:
                                    seen_ids.add(rid)
                                    merged.append(r)
                            for r in results:
                                rid = r.get("id")
                                if rid not in seen_ids:
                                    seen_ids.add(rid)
                                    merged.append(r)
                            results = merged[:limit]
                            print(f"   🔍 REI boost: {len(rei_hits)} REI chunk(s) for '{product_name}' prioritized, {len(results)} total")
                        else:
                            print(f"   ⚠️  REI boost: no REI chunks found for '{product_name}'")
            
            # Format results with page numbers and PDF URLs
            formatted_results = []
            for result in results:
                # PHASE 1 FIX: Extract pdf_url from result with multiple fallback strategies
                metadata = result.get("metadata", {})
                
                # Strategy 1: Direct pdf_url field (preferred - from vector_store extraction)
                pdf_url = result.get("pdf_url", "")
                
                # Strategy 2: From metadata dict
                if not pdf_url:
                    pdf_url = metadata.get("pdf_url", "")
                
                # Strategy 3: From payload directly (if metadata is the payload)
                if not pdf_url and isinstance(metadata, dict):
                    pdf_url = metadata.get("pdf_url", "")
                
                # Also extract url_hash for matching
                url_hash = result.get("url_hash", "") or metadata.get("url_hash", "")
                
                # PHASE 2 FIX: Extract page_number with multiple fallback strategies
                page_number = result.get("page_number", 0)
                
                # Strategy 1: Direct page_number field (preferred - from vector_store extraction)
                if page_number <= 0:
                    # Strategy 2: From metadata dict
                    page_number = metadata.get("page_number", 0)
                
                # Strategy 3: Validate and fix if still invalid
                if page_number <= 0:
                    # Fallback: Estimate page number based on chunk_index
                    chunk_index = metadata.get("chunk_index", 0)
                    if chunk_index > 0:
                        # Rough estimate: 3 chunks per page
                        page_number = (chunk_index // 3) + 1
                    else:
                        # Last resort: use page 1
                        page_number = 1
                    print(f"⚠️  Warning: Invalid or missing page_number for chunk, using estimated value: {page_number}")
                
                formatted_results.append({
                    "content": result.get("content", ""),
                    "page_number": page_number,  # PHASE 2 FIX: Validated page number
                    "source_file": result.get("source_file", "Unknown"),
                    "score": result.get("score", 0.0),
                    "document_id": result.get("document_id", ""),
                    "chunk_index": metadata.get("chunk_index", 0),
                    "document_name": metadata.get("document_name", ""),
                    "pdf_url": pdf_url,  # PHASE 1 FIX: Include PDF URL from metadata
                    "url_hash": url_hash  # PHASE 1 FIX: Include URL hash for matching
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"⚠️  Warning: RAG search failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def search_by_product(
        self,
        product_name: str,
        query: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Search for specific product information
        
        Args:
            product_name: Product name (e.g., "Roundup")
            query: Optional specific question (if None, returns general product info)
            limit: Maximum results
        
        Returns:
            List of relevant chunks with page numbers
        """
        if query:
            return self.search(query=query, product_name=product_name, limit=limit)
        else:
            # General product search
            return self.search(
                query=f"{product_name} pesticide label information",
                product_name=product_name,
                limit=limit
            )
    
    def get_collection_stats(self) -> Dict:
        """
        Get statistics about the CDMS documents collection
        
        Returns:
            Dict with collection information
        """
        if not self.vector_store:
            return {"error": "Vector store not initialized"}
        
        try:
            info = self.vector_store.get_collection_info()
            return info
        except Exception as e:
            return {"error": str(e)}


# Test function
if __name__ == "__main__":
    print("=" * 80)
    print("Testing CDMS RAG Search")
    print("=" * 80)
    
    try:
        searcher = CDMSRAGSearch()
        
        # Check collection stats
        print("\n📊 Collection Stats:")
        stats = searcher.get_collection_stats()
        if "error" not in stats:
            if "cdms_documents" in stats:
                doc_info = stats["cdms_documents"]
                print(f"   Documents in Qdrant: {doc_info.get('points_count', 0)}")
                print(f"   Vectors: {doc_info.get('vectors_count', 0)}")
            else:
                print("   ⚠️  No documents indexed yet")
        else:
            print(f"   ⚠️  {stats['error']}")
        
        # Test search (if documents exist)
        if stats.get("cdms_documents", {}).get("points_count", 0) > 0:
            print("\n🔍 Testing search: 'application rate'")
            results = searcher.search("application rate", limit=3)
            
            if results:
                print(f"   ✅ Found {len(results)} result(s)")
                for i, result in enumerate(results, 1):
                    print(f"\n   {i}. Score: {result['score']:.3f}")
                    print(f"      Page: {result['page_number']}")
                    print(f"      File: {result['source_file']}")
                    print(f"      Content: {result['content'][:100]}...")
            else:
                print("   ⚠️  No results found")
        else:
            print("\n💡 To test search:")
            print("   1. Download PDFs (Phase 1)")
            print("   2. Process and index PDFs in Qdrant")
            print("   3. Run this test again")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

