"""
Test CDMS RAG Search - Phase 3
Tests RAG search functionality with Qdrant
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.cdms.rag_search import CDMSRAGSearch
from src.cdms.document_loader import DocumentLoader


def check_qdrant_connection():
    """Check if Qdrant is available"""
    print("=" * 80)
    print("TEST 1: Qdrant Connection Check")
    print("=" * 80)
    
    try:
        searcher = CDMSRAGSearch()
        
        if not searcher.vector_store:
            print("❌ Vector store not initialized")
            return False
        
        if not searcher.embedding_service:
            print("❌ Embedding service not initialized")
            return False
        
        print("✅ Qdrant connection successful!")
        print("✅ Embedding service initialized!")
        
        # Check collection stats
        stats = searcher.get_collection_stats()
        if "error" not in stats:
            if "cdms_documents" in stats:
                doc_info = stats["cdms_documents"]
                points = doc_info.get("points_count", 0)
                print(f"\n📊 Collection Stats:")
                print(f"   Documents indexed: {points}")
                return points > 0
            else:
                print("\n⚠️  No documents indexed yet")
                return False
        else:
            print(f"\n⚠️  {stats['error']}")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def index_pdfs():
    """Index downloaded PDFs in Qdrant"""
    print("\n" + "=" * 80)
    print("TEST 2: Index PDFs in Qdrant")
    print("=" * 80)
    
    pdf_folder = Path("data/pdfs/cdms")
    
    if not pdf_folder.exists():
        print(f"❌ PDF folder not found: {pdf_folder}")
        print("   Run Phase 1 tests first to download PDFs")
        return False
    
    pdf_files = list(pdf_folder.glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ No PDF files found in {pdf_folder}")
        return False
    
    print(f"\n📚 Found {len(pdf_files)} PDF file(s)")
    print("   Processing and indexing PDFs...")
    print("-" * 80)
    
    try:
        loader = DocumentLoader(pdf_folder=str(pdf_folder))
        result = loader.load_all_pdfs(force_reprocess=False)
        
        if result.get("success"):
            print(f"\n✅ Indexing complete!")
            print(f"   Files processed: {result['successful']}/{result['total_files']}")
            print(f"   Total chunks: {result['total_chunks']}")
            print(f"   Embeddings generated: {result['total_embeddings']}")
            return True
        else:
            print(f"❌ Indexing failed: {result.get('error')}")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_search():
    """Test RAG search functionality"""
    print("\n" + "=" * 80)
    print("TEST 3: RAG Search Functionality")
    print("=" * 80)
    
    try:
        searcher = CDMSRAGSearch()
        
        # Test 1: General search
        print("\n🔍 Test 1: General search ('application rate')")
        results = searcher.search("application rate", limit=3)
        
        if results:
            print(f"   ✅ Found {len(results)} result(s)")
            for i, result in enumerate(results, 1):
                print(f"\n   {i}. Score: {result['score']:.3f}")
                print(f"      Page: {result['page_number']}")
                print(f"      File: {result['source_file']}")
                print(f"      Content: {result['content'][:150]}...")
        else:
            print("   ⚠️  No results found")
            return False
        
        # Test 2: Product-specific search
        print("\n🔍 Test 2: Product-specific search ('Roundup application rate')")
        results = searcher.search("application rate", product_name="Roundup", limit=3)
        
        if results:
            print(f"   ✅ Found {len(results)} result(s) for Roundup")
            for i, result in enumerate(results, 1):
                print(f"\n   {i}. Score: {result['score']:.3f}")
                print(f"      Page: {result['page_number']}")
                print(f"      File: {result['source_file']}")
                print(f"      Content: {result['content'][:150]}...")
        else:
            print("   ⚠️  No results found for Roundup")
        
        # Test 3: search_by_product method
        print("\n🔍 Test 3: search_by_product('Roundup', 'safety precautions')")
        results = searcher.search_by_product("Roundup", "safety precautions", limit=2)
        
        if results:
            print(f"   ✅ Found {len(results)} result(s)")
            for i, result in enumerate(results, 1):
                print(f"\n   {i}. Page {result['page_number']}: {result['content'][:100]}...")
        else:
            print("   ⚠️  No results found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_page_citations():
    """Test that page numbers are accurate"""
    print("\n" + "=" * 80)
    print("TEST 4: Page Number Citations")
    print("=" * 80)
    
    try:
        searcher = CDMSRAGSearch()
        
        print("\n🔍 Searching for 'mixing instructions'")
        results = searcher.search("mixing instructions", limit=5)
        
        if not results:
            print("   ⚠️  No results found")
            return False
        
        print(f"   ✅ Found {len(results)} result(s)")
        
        # Check that all results have page numbers
        all_have_pages = all(r.get("page_number", 0) > 0 for r in results)
        
        if all_have_pages:
            print(f"   ✅ All results have page numbers")
            
            # Show page distribution
            pages = [r["page_number"] for r in results]
            unique_pages = sorted(set(pages))
            print(f"\n   Page distribution:")
            print(f"      Pages cited: {unique_pages}")
            print(f"      Total unique pages: {len(unique_pages)}")
            
            # Show example with page citation
            print(f"\n   Example citation:")
            example = results[0]
            print(f"      Page {example['page_number']}: {example['content'][:100]}...")
            
            return True
        else:
            print(f"   ⚠️  Some results missing page numbers")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("CDMS RAG Search - Phase 3 Testing")
    print("=" * 80)
    print("\nThis will test:")
    print("1. Qdrant connection")
    print("2. PDF indexing (if needed)")
    print("3. RAG search functionality")
    print("4. Page number citations")
    print("\n" + "=" * 80)
    
    results = []
    
    # Test 1: Check Qdrant
    try:
        has_docs = check_qdrant_connection()
        results.append(("Qdrant Connection", True))
        
        # If no documents, try to index
        if not has_docs:
            print("\n⚠️  No documents in Qdrant. Indexing PDFs...")
            indexed = index_pdfs()
            results.append(("PDF Indexing", indexed))
        else:
            results.append(("PDF Indexing", True))  # Already indexed
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        results.append(("Qdrant Connection", False))
        results.append(("PDF Indexing", False))
    
    # Test 2: RAG Search
    try:
        success = test_rag_search()
        results.append(("RAG Search", success))
    except Exception as e:
        print(f"❌ Test failed: {e}")
        results.append(("RAG Search", False))
    
    # Test 3: Page Citations
    try:
        success = test_page_citations()
        results.append(("Page Citations", success))
    except Exception as e:
        print(f"❌ Test failed: {e}")
        results.append(("Page Citations", False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed")
    print("=" * 80)
    
    if passed == total:
        print("\n🎉 All tests passed! Phase 3 RAG search is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    main()






