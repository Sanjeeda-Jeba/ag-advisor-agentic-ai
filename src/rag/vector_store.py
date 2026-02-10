"""
Qdrant Vector Store
Manages vector embeddings in Qdrant database
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Optional


class QdrantVectorStore:
    """
    Qdrant Vector Store Manager
    
    Handles storage and retrieval of document embeddings
    
    Usage:
        store = QdrantVectorStore()
        store.add_document_chunk("chunk_id", embedding, metadata)
        results = store.search_documents(query_embedding)
    """
    
    def __init__(self, host: str = "localhost", port: int = 6333):
        """
        Initialize Qdrant client
        
        Args:
            host: Qdrant host (default: localhost)
            port: Qdrant port (default: 6333)
        """
        self.host = host
        self.port = port
        self.embedding_dim = 1536  # OpenAI text-embedding-3-small
        self.using_docker = False
        
        # Try to connect to Docker Qdrant first
        try:
            self.client = QdrantClient(host=host, port=port, timeout=5)
            # Test connection by getting collections
            _ = self.client.get_collections()
            self.using_docker = True
            print(f"✅ Connected to Qdrant Docker at {host}:{port}")
            self.initialize_collections()
        except Exception as e:
            # If Qdrant not available, use in-memory mode
            print(f"⚠️  Qdrant Docker not available at {host}:{port}")
            print(f"   Error: {str(e)}")
            print(f"   💡 Starting Qdrant: docker run -d -p 6333:6333 qdrant/qdrant")
            print(f"   📦 Using in-memory mode (data lost on restart)")
            print(f"   ⚠️  WARNING: In-memory mode creates separate databases per instance!")
            print(f"   ⚠️  Data stored in one instance won't be visible to another instance.")
            self.client = QdrantClient(":memory:")
            self.initialize_collections()
    
    def initialize_collections(self):
        """Create collections for APIs and PDF documents"""
        # Collection for API descriptions (for future use)
        if not self.client.collection_exists("api_catalog"):
            try:
                self.client.create_collection(
                    collection_name="api_catalog",
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
            except Exception:
                pass  # Collection might already exist
        
        # Collection for PDF document chunks (CDMS)
        if not self.client.collection_exists("cdms_documents"):
            try:
                self.client.create_collection(
                    collection_name="cdms_documents",
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
            except Exception:
                pass  # Collection might already exist
    
    def add_document_chunk(
        self, 
        chunk_id: str, 
        embedding: List[float], 
        metadata: Dict
    ):
        """
        Add PDF chunk to vector store
        
        Args:
            chunk_id: Unique identifier for the chunk (string, will be converted to int)
            embedding: Vector embedding (1536 dimensions)
            metadata: Dict with chunk metadata
        """
        try:
            # Validate embedding
            if not embedding:
                print(f"⚠️  Warning: Empty embedding for chunk {chunk_id}, skipping")
                return False
            
            if len(embedding) != self.embedding_dim:
                print(f"⚠️  Warning: Invalid embedding dimension {len(embedding)} (expected {self.embedding_dim}) for chunk {chunk_id}")
                return False
            
            # Convert string ID to integer hash for Qdrant (Qdrant requires int or UUID)
            import hashlib
            int_id = int(hashlib.md5(chunk_id.encode()).hexdigest()[:15], 16)  # Use first 15 hex chars as int
            
            self.client.upsert(
                collection_name="cdms_documents",
                points=[PointStruct(
                    id=int_id,  # Qdrant requires integer or UUID
                    vector=embedding,
                    payload=metadata
                )]
            )
            return True
        except Exception as e:
            print(f"⚠️  Warning: Could not add chunk to Qdrant: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def search_documents(
        self, 
        query_embedding: List[float], 
        limit: int = 10,
        score_threshold: float = 0.3  # Lowered from 0.5 to get more results
    ) -> List[Dict]:
        """
        Search for similar document chunks
        
        Args:
            query_embedding: Query vector embedding
            limit: Maximum number of results
            score_threshold: Minimum similarity score (0-1)
        
        Returns:
            List of search results with metadata and scores
        """
        try:
            # Use query_points instead of search (correct Qdrant API)
            response = self.client.query_points(
                collection_name="cdms_documents",
                query=query_embedding,  # Changed from query_vector to query
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True
            )
            
            # Access points from QueryResponse
            results = response.points
            
            # Format results
            formatted_results = []
            for result in results:
                payload = result.payload or {}  # Handle None payload
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    "content": payload.get("content", ""),
                    "source_file": payload.get("source_file", "Unknown"),
                    "page_number": payload.get("page_number", 0),
                    "document_id": payload.get("document_id", ""),
                    "pdf_url": payload.get("pdf_url", ""),  # PHASE 1 FIX: Extract PDF URL from payload
                    "url_hash": payload.get("url_hash", ""),  # PHASE 1 FIX: Extract URL hash from payload
                    "metadata": payload
                })
            
            return formatted_results
        
        except Exception as e:
            print(f"⚠️  Warning: Could not search Qdrant: {e}")
            return []
    
    def get_collection_info(self) -> Dict:
        """Get information about collections"""
        try:
            info = {
                "using_docker": self.using_docker,
                "host": self.host if self.using_docker else "in-memory",
                "port": self.port if self.using_docker else None
            }
            if self.client.collection_exists("cdms_documents"):
                collection_info = self.client.get_collection("cdms_documents")
                info["cdms_documents"] = {
                    "points_count": collection_info.points_count,
                    "vectors_count": collection_info.vectors_count
                }
            return info
        except Exception as e:
            return {"error": str(e)}


# Test function
if __name__ == "__main__":
    print("Testing Qdrant Vector Store...")
    print("-" * 70)
    
    try:
        store = QdrantVectorStore()
        
        print("✅ Qdrant connection successful!")
        
        info = store.get_collection_info()
        if info:
            print(f"\n📊 Collection Info:")
            for collection, data in info.items():
                print(f"   {collection}: {data.get('points_count', 0)} points")
        else:
            print("\n📊 Collections initialized (empty)")
        
        print("\n💡 To use:")
        print("   1. Make sure Qdrant is running:")
        print("      docker run -d -p 6333:6333 qdrant/qdrant")
        print("   2. Or it will use in-memory mode automatically")
        
    except Exception as e:
        print(f"❌ Error: {e}")

