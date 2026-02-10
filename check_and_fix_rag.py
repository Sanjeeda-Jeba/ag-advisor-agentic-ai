#!/usr/bin/env python3
"""
Check and Fix RAG System
Diagnoses why search isn't finding documents and fixes it
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_qdrant():
    """Check if Qdrant has data"""
    print("\n" + "="*70)
    print("1. CHECKING QDRANT")
    print("="*70)
    
    try:
        from src.rag.vector_store import QdrantVectorStore
        vs = QdrantVectorStore()
        info = vs.get_collection_info()
        
        print(f"Connection: {'✅ Docker' if info.get('using_docker') else '⚠️  In-memory'}")
        print(f"Host: {info.get('host', 'unknown')}")
        
        if 'cdms_documents' in info:
            points = info['cdms_documents']['points_count']
            vectors = info['cdms_documents']['vectors_count']
            print(f"Points in Qdrant: {points}")
            print(f"Vectors: {vectors}")
            
            if points == 0:
                print("\n❌ Qdrant is EMPTY! PDFs need to be re-processed.")
                return False, vs
            else:
                print(f"\n✅ Qdrant has {points} document chunks stored")
                return True, vs
        else:
            print("\n❌ cdms_documents collection doesn't exist or is empty")
            return False, vs
            
    except Exception as e:
        print(f"❌ Error checking Qdrant: {e}")
        return False, None


def check_database():
    """Check database for processed PDFs"""
    print("\n" + "="*70)
    print("2. CHECKING DATABASE")
    print("="*70)
    
    try:
        from src.cdms.schema import DatabaseManager, Document, DocumentChunk
        from sqlalchemy.orm import sessionmaker
        
        db = DatabaseManager()
        Session = sessionmaker(bind=db.engine)
        session = Session()
        
        docs = session.query(Document).all()
        chunks = session.query(DocumentChunk).all()
        
        print(f"Documents in DB: {len(docs)}")
        print(f"Chunks in DB: {len(chunks)}")
        
        if docs:
            print("\nProcessed PDFs:")
            for d in docs:
                print(f"  - {d.filename}: {d.num_chunks} chunks")
        
        session.close()
        return len(docs) > 0, len(chunks)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, 0


def test_search():
    """Test if search actually works"""
    print("\n" + "="*70)
    print("3. TESTING SEARCH")
    print("="*70)
    
    try:
        from src.tools.rag_tool import execute_rag_tool
        
        test_query = "Tell me about pesticides"
        print(f"Query: '{test_query}'")
        
        result = execute_rag_tool(test_query)
        
        if result["success"]:
            data = result["data"]
            api_count = len(data.get("api_matches", []))
            doc_count = len(data.get("document_context", []))
            
            print(f"\n✅ Search successful!")
            print(f"   API matches: {api_count}")
            print(f"   Document chunks: {doc_count}")
            
            if doc_count > 0:
                print(f"\n📄 Sample results:")
                for i, doc in enumerate(data["document_context"][:3], 1):
                    print(f"   {i}. {doc['source_file']} (score: {doc['score']:.2f})")
                    print(f"      Preview: {doc['content'][:100]}...")
                return True
            else:
                print("\n⚠️  No document chunks found (even though search succeeded)")
                return False
        else:
            print(f"\n❌ Search failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing search: {e}")
        import traceback
        traceback.print_exc()
        return False


def reprocess_pdfs():
    """Re-process PDFs to store embeddings in Qdrant"""
    print("\n" + "="*70)
    print("4. RE-PROCESSING PDFs")
    print("="*70)
    
    print("⚠️  This will re-process all PDFs and store embeddings in Qdrant.")
    print("    This may take a few minutes and use OpenAI API credits.")
    
    response = input("\nContinue? (y/n): ")
    if response.lower() != 'y':
        print("❌ Cancelled")
        return False
    
    try:
        from src.cdms.document_loader import DocumentLoader
        
        loader = DocumentLoader()
        result = loader.load_all_pdfs()
        
        if result.get("success"):
            print(f"\n✅ Processing complete!")
            print(f"   Files: {result['successful']}/{result['total_files']}")
            print(f"   Chunks: {result['total_chunks']}")
            print(f"   Embeddings: {result['total_embeddings']}")
            return True
        else:
            print(f"\n❌ Error: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main diagnostic and fix routine"""
    print("\n" + "="*70)
    print("🔍 RAG SYSTEM DIAGNOSTIC & FIX")
    print("="*70)
    
    # Check database
    db_ok, db_chunks = check_database()
    
    # Check Qdrant
    qdrant_ok, vs = check_qdrant()
    
    # Test search
    search_ok = test_search()
    
    # Summary and recommendations
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    
    print(f"Database: {'✅' if db_ok else '❌'} ({db_chunks} chunks)")
    print(f"Qdrant: {'✅' if qdrant_ok else '❌'}")
    print(f"Search: {'✅' if search_ok else '❌'}")
    
    # Recommendations
    print("\n" + "="*70)
    print("💡 RECOMMENDATIONS")
    print("="*70)
    
    if not qdrant_ok:
        print("\n❌ Qdrant is empty!")
        print("   PDFs were processed in SQLite but embeddings weren't stored in Qdrant.")
        print("   This happens if Qdrant wasn't running when PDFs were processed.")
        print("\n   Solution: Re-process PDFs with Qdrant running")
        
        if db_ok:
            print("\n   Steps:")
            print("   1. Make sure Qdrant Docker is running:")
            print("      ./start_qdrant.sh")
            print("   2. Re-process PDFs:")
            print("      python src/cdms/document_loader.py")
            print("\n   Or run this script's auto-fix:")
            reprocess_pdfs()
    elif not search_ok:
        print("\n⚠️  Search isn't working properly")
        print("   Possible issues:")
        print("   - Score threshold too high")
        print("   - Query doesn't match content")
        print("   - Embeddings not matching")
        print("\n   Try different queries or check vector search")
    else:
        print("\n✅ Everything looks good!")
        print("   If you're still not getting results, try:")
        print("   - More specific questions about your PDF content")
        print("   - Different keywords")
        print("   - Check if your questions match the PDF topics")


if __name__ == "__main__":
    main()

