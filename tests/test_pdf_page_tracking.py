"""
Test Enhanced PDF Processor with Page Number Tracking
Tests Phase 2: Accurate page number tracking
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.cdms.pdf_processor import PDFProcessor


def test_pdf_processing():
    """Test PDF processing with page tracking"""
    print("=" * 80)
    print("TEST: Enhanced PDF Processor with Page Tracking")
    print("=" * 80)
    
    processor = PDFProcessor(chunk_size=1000, chunk_overlap=200)
    
    # Check for downloaded PDFs from Phase 1
    pdf_folder = Path("data/pdfs/cdms")
    
    if not pdf_folder.exists():
        print(f"\n❌ PDF folder not found: {pdf_folder}")
        print("   Run Phase 1 tests first to download PDFs")
        return False
    
    pdf_files = list(pdf_folder.glob("*.pdf"))
    
    if not pdf_files:
        print(f"\n❌ No PDF files found in {pdf_folder}")
        print("   Run Phase 1 tests first to download PDFs")
        return False
    
    # Test with first PDF
    test_pdf = pdf_files[0]
    print(f"\n📄 Processing: {test_pdf.name}")
    print(f"   Path: {test_pdf}")
    print("-" * 80)
    
    result = processor.process_pdf(str(test_pdf))
    
    if not result.get("success"):
        print(f"❌ Processing failed: {result.get('error')}")
        return False
    
    print(f"✅ Processing successful!")
    print(f"   Total pages: {result['num_pages']}")
    print(f"   Total chunks: {result['num_chunks']}")
    
    # Check page tracking
    if "page_numbers" in result:
        page_numbers = result["page_numbers"]
        print(f"\n📊 Page Tracking:")
        print(f"   ✅ Page numbers tracked for all chunks")
        print(f"   Chunks with page numbers: {len(page_numbers)}")
        
        # Show page distribution
        from collections import Counter
        page_dist = Counter(page_numbers)
        print(f"\n   Page distribution (first 10 pages):")
        for page_num in sorted(page_dist.keys())[:10]:
            count = page_dist[page_num]
            print(f"      Page {page_num}: {count} chunk(s)")
        
        # Verify chunks match page numbers
        if len(result["chunks"]) == len(page_numbers):
            print(f"\n   ✅ All chunks have page numbers")
        else:
            print(f"\n   ⚠️  Mismatch: {len(result['chunks'])} chunks, {len(page_numbers)} page numbers")
        
        # Show sample chunks with page numbers
        print(f"\n   Sample chunks with page numbers:")
        for i in range(min(3, len(result["chunks"]))):
            chunk = result["chunks"][i]
            page = page_numbers[i]
            preview = chunk[:100].replace("\n", " ")
            print(f"      Chunk {i+1} (Page {page}): {preview}...")
    else:
        print(f"\n   ⚠️  Page numbers not found in result")
        return False
    
    return True


def test_chunks_with_pages():
    """Test get_chunks_with_pages method"""
    print("\n" + "=" * 80)
    print("TEST: get_chunks_with_pages() Method")
    print("=" * 80)
    
    processor = PDFProcessor()
    
    pdf_folder = Path("data/pdfs/cdms")
    pdf_files = list(pdf_folder.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found")
        return False
    
    test_pdf = pdf_files[0]
    print(f"\n📄 Testing with: {test_pdf.name}")
    
    chunks_with_pages = processor.get_chunks_with_pages(str(test_pdf))
    
    if not chunks_with_pages:
        print("❌ No chunks returned")
        return False
    
    print(f"✅ Retrieved {len(chunks_with_pages)} chunks with page numbers")
    
    # Show first few
    print(f"\n   First 3 chunks:")
    for i, (chunk, page) in enumerate(chunks_with_pages[:3], 1):
        preview = chunk[:80].replace("\n", " ")
        print(f"      {i}. Page {page}: {preview}...")
    
    # Verify format
    all_valid = all(
        isinstance(chunk, str) and isinstance(page, int) and page > 0
        for chunk, page in chunks_with_pages
    )
    
    if all_valid:
        print(f"\n   ✅ All chunks have valid (chunk_text, page_number) format")
    else:
        print(f"\n   ⚠️  Some chunks have invalid format")
        return False
    
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("PDF Page Tracking - Phase 2 Testing")
    print("=" * 80)
    
    results = []
    
    # Test 1: PDF Processing
    try:
        success = test_pdf_processing()
        results.append(("PDF Processing with Page Tracking", success))
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("PDF Processing with Page Tracking", False))
    
    # Test 2: get_chunks_with_pages
    try:
        success = test_chunks_with_pages()
        results.append(("get_chunks_with_pages() Method", success))
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("get_chunks_with_pages() Method", False))
    
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
        print("\n🎉 All tests passed! Phase 2 page tracking is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    main()






