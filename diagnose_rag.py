#!/usr/bin/env python3
"""
RAG System Diagnostic Tool
Checks all components of the RAG system and identifies issues
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_database():
    """Check if PDFs are processed and stored in database"""
    print("\n" + "="*70)
    print("1. DATABASE CHECK (SQLite)")
    print("="*70)
    
    try:
        from src.cdms.schema import DatabaseManager, Document, DocumentChunk
        from sqlalchemy.orm import sessionmaker
        
        db = DatabaseManager()
        Session = sessionmaker(bind=db.engine)
        session = Session()
        
        docs = session.query(Document).all()
        chunks = session.query(DocumentChunk).all()
        
        print(f"✅ Database connection: OK")
        print(f"📄 Documents in database: {len(docs)}")
        print(f"📝 Chunks in database: {len(chunks)}")
        
        if docs:
            print("\n📚 Documents:")
            for d in docs:
                print(f"   • {d.filename}")
                print(f"     - Processed: {d.processed}")
                print(f"     - Chunks: {d.num_chunks}")
                print(f"     - Pages: {d.num_pages}")
        else:
            print("⚠️  No documents found! Run: python src/cdms/document_loader.py")
        
        session.close()
        return len(docs) > 0, len(chunks)
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False, 0


def check_qdrant():
    """Check Qdrant connection and collections"""
    print("\n" + "="*70)
    print("2. QDRANT VECTOR STORE CHECK")
    print("="*70)
    
    try:
        from src.rag.vector_store import QdrantVectorStore
        
        store = QdrantVectorStore()
        
        # Check if using in-memory or Docker
        if hasattr(store.client, 'host') and store.client.host == ":memory:":
            print("⚠️  Using IN-MEMORY mode (data lost on restart)")
            print("   💡 Tip: Start Qdrant Docker for persistent storage:")
            print("      docker run -d -p 6333:6333 qdrant/qdrant")
        else:
            print("✅ Qdrant Docker connection: OK")
        
        # Check collections
        try:
            collections = store.client.get_collections().collections
            print(f"📦 Collections found: {len(collections)}")
            
            for coll in collections:
                if coll.name == "cdms_documents":
                    coll_info = store.client.get_collection(coll.name)
                    print(f"   • {coll.name}: {coll_info.points_count} points")
                else:
                    print(f"   • {coll.name}")
            
            if not any(c.name == "cdms_documents" for c in collections):
                print("⚠️  'cdms_documents' collection not found!")
                return False, 0
            
            # Get count
            coll_info = store.client.get_collection("cdms_documents")
            return True, coll_info.points_count
            
        except Exception as e:
            print(f"⚠️  Error checking collections: {e}")
            return False, 0
            
    except Exception as e:
        print(f"❌ Qdrant error: {e}")
        print("   💡 Tip: This is OK if using in-memory mode")
        return False, 0


def check_embeddings():
    """Check if OpenAI embeddings work"""
    print("\n" + "="*70)
    print("3. EMBEDDINGS CHECK (OpenAI)")
    print("="*70)
    
    try:
        from src.rag.embeddings import OpenAIEmbeddingService
        from src.config.credentials import CredentialsManager
        
        creds = CredentialsManager()
        api_key = creds.get_api_key("openai")
        
        if not api_key:
            print("❌ OpenAI API key not found!")
            print("   💡 Add OPENAI_API_KEY to .env file")
            return False
        
        print("✅ OpenAI API key: Found")
        
        # Test embedding generation
        embedding_service = OpenAIEmbeddingService(api_key=api_key)
        test_embedding = embedding_service.generate_embedding("test query")
        
        if test_embedding and len(test_embedding) == 1536:
            print(f"✅ Embedding generation: OK (dimension: {len(test_embedding)})")
            return True
        else:
            print("❌ Embedding generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Embeddings error: {e}")
        return False


def test_rag_search():
    """Test RAG search functionality"""
    print("\n" + "="*70)
    print("4. RAG SEARCH TEST")
    print("="*70)
    
    try:
        from src.tools.rag_tool import execute_rag_tool
        
        test_queries = [
            "Tell me about pesticides",
            "What are insecticides?",
            "Agricultural information"
        ]
        
        for query in test_queries:
            print(f"\n📝 Testing: '{query}'")
            result = execute_rag_tool(query)
            
            if result["success"]:
                data = result["data"]
                api_count = len(data.get("api_matches", []))
                doc_count = len(data.get("document_context", []))
                
                print(f"   ✅ Found {api_count} API matches, {doc_count} document chunks")
                
                if doc_count > 0:
                    print(f"   📄 Sample result:")
                    sample = data["document_context"][0]
                    print(f"      - File: {sample['source_file']}")
                    print(f"      - Score: {sample['score']:.2f}")
                    print(f"      - Preview: {sample['content'][:80]}...")
                elif api_count == 0:
                    print(f"   ⚠️  No results found")
            else:
                print(f"   ❌ Error: {result['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG search test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_pdf_files():
    """Check if PDF files exist"""
    print("\n" + "="*70)
    print("5. PDF FILES CHECK")
    print("="*70)
    
    pdf_dir = Path("data/pdfs")
    
    if not pdf_dir.exists():
        print(f"❌ PDF directory not found: {pdf_dir}")
        print("   💡 Create the directory and add PDF files")
        return False
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"⚠️  No PDF files found in {pdf_dir}")
        print("   💡 Add PDF files to this directory")
        return False
    
    print(f"✅ Found {len(pdf_files)} PDF file(s):")
    for pdf in pdf_files:
        size_kb = pdf.stat().st_size / 1024
        print(f"   • {pdf.name} ({size_kb:.1f} KB)")
    
    return True


def main():
    """Run all diagnostic checks"""
    print("\n" + "="*70)
    print("🔍 RAG SYSTEM DIAGNOSTIC")
    print("="*70)
    
    results = {}
    
    # Run checks
    results["pdfs_exist"] = check_pdf_files()
    results["database_ok"], results["db_chunks"] = check_database()
    results["qdrant_ok"], results["qdrant_points"] = check_qdrant()
    results["embeddings_ok"] = check_embeddings()
    results["rag_works"] = test_rag_search()
    
    # Summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    
    print(f"PDFs exist: {'✅' if results['pdfs_exist'] else '❌'}")
    print(f"Database: {'✅' if results['database_ok'] else '❌'} ({results['db_chunks']} chunks)")
    print(f"Qdrant: {'✅' if results['qdrant_ok'] else '⚠️ '} ({results['qdrant_points']} points)")
    print(f"Embeddings: {'✅' if results['embeddings_ok'] else '❌'}")
    print(f"RAG search: {'✅' if results['rag_works'] else '❌'}")
    
    # Recommendations
    print("\n" + "="*70)
    print("💡 RECOMMENDATIONS")
    print("="*70)
    
    if not results["pdfs_exist"]:
        print("1. Add PDF files to data/pdfs/ folder")
    
    if not results["database_ok"] or results["db_chunks"] == 0:
        print("2. Run PDF processor: python src/cdms/document_loader.py")
    
    if not results["qdrant_ok"] or results["qdrant_points"] == 0:
        print("3. Process PDFs and generate embeddings:")
        print("   python src/cdms/document_loader.py")
        print("   (Or start Qdrant Docker for persistent storage)")
    
    if not results["embeddings_ok"]:
        print("4. Check OPENAI_API_KEY in .env file")
    
    if all([results["pdfs_exist"], results["database_ok"], results["qdrant_ok"], 
            results["embeddings_ok"], results["rag_works"]]):
        print("✅ All checks passed! RAG system should be working.")
    else:
        print("\n⚠️  Some issues found. Fix them above and re-run this diagnostic.")


if __name__ == "__main__":
    main()

