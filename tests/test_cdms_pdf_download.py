"""
Test CDMS PDF Download Functionality
Tests Phase 1: PDF downloader and CDMS tool integration
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.cdms.pdf_downloader import CDMSPDFDownloader
from src.tools.cdms_label_tool import CDMSLabelTool, execute_cdms_label_tool


def test_pdf_downloader():
    """Test PDF downloader directly"""
    print("=" * 80)
    print("TEST 1: PDF Downloader Direct Test")
    print("=" * 80)
    
    downloader = CDMSPDFDownloader()
    
    # Test URL hash generation
    test_url = "https://cdms.net/labels/roundup.pdf"
    url_hash = downloader._generate_url_hash(test_url)
    print(f"\n✅ URL Hash Generation:")
    print(f"   URL: {test_url}")
    print(f"   Hash: {url_hash}")
    
    # Test filename generation
    expected_file = downloader._get_expected_filename(test_url, "Roundup")
    print(f"\n✅ Filename Generation:")
    print(f"   Expected: {expected_file.name}")
    print(f"   Full path: {expected_file}")
    
    # Test PDF URL detection
    print(f"\n✅ PDF URL Detection:")
    test_urls = [
        "https://cdms.net/labels/roundup.pdf",
        "https://example.com/page",
        "https://cdms.net/labels/sevin.PDF",
        "https://cdms.net/labels/24d_label.pdf"
    ]
    for url in test_urls:
        is_pdf = downloader._is_pdf_url(url)
        print(f"   {url}: {'✅ PDF' if is_pdf else '❌ Not PDF'}")
    
    # Check existing downloads
    downloaded = downloader.get_downloaded_pdfs()
    print(f"\n✅ Existing Downloads:")
    print(f"   Found {len(downloaded)} PDF file(s)")
    for pdf in downloaded[:5]:
        size_mb = pdf['size'] / (1024 * 1024)
        print(f"   - {pdf['filename']} ({size_mb:.2f} MB)")
    
    print("\n" + "=" * 80)


def test_cdms_tool_search():
    """Test CDMS tool search (without download)"""
    print("=" * 80)
    print("TEST 2: CDMS Tool Search (Tavily)")
    print("=" * 80)
    
    try:
        tool = CDMSLabelTool()
        
        print("\n🔍 Searching for Roundup labels...")
        result = tool.search(
            product_name="Roundup",
            active_ingredient="glyphosate",
            max_results=3
        )
        
        if result.get("success"):
            print(f"✅ Search successful!")
            print(f"   Found {result['label_count']} label(s)")
            print(f"   Query used: {result.get('query_used', 'N/A')}")
            
            # Show labels found
            print(f"\n📄 Labels Found:")
            for i, label in enumerate(result.get("labels", []), 1):
                print(f"\n   {i}. {label['title']}")
                print(f"      URL: {label['url']}")
                print(f"      Relevance: {label['relevance']:.2f}")
                is_pdf = tool.pdf_downloader._is_pdf_url(label['url'])
                print(f"      Is PDF: {'✅' if is_pdf else '❌'}")
        else:
            print(f"❌ Search failed: {result.get('error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pdf_extraction():
    """Test PDF URL extraction from Tavily results"""
    print("\n" + "=" * 80)
    print("TEST 3: PDF URL Extraction from Tavily Results")
    print("=" * 80)
    
    try:
        tool = CDMSLabelTool()
        
        print("\n🔍 Searching for Roundup labels...")
        result = tool.search(
            product_name="Roundup",
            max_results=5
        )
        
        if not result.get("success"):
            print(f"❌ Search failed: {result.get('error')}")
            return False
        
        # Extract PDF URLs
        raw_results = result.get("raw_tavily_results", result)
        pdf_urls = tool.pdf_downloader.extract_pdf_urls(raw_results)
        
        print(f"\n✅ PDF URL Extraction:")
        print(f"   Found {len(pdf_urls)} PDF URL(s)")
        
        for i, url in enumerate(pdf_urls, 1):
            print(f"   {i}. {url}")
        
        if len(pdf_urls) == 0:
            print("   ⚠️  No PDF URLs found in results")
            print("   This might be normal if Tavily returns HTML pages instead of direct PDF links")
        
        return len(pdf_urls) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pdf_download():
    """Test actual PDF download (if PDFs are found)"""
    print("\n" + "=" * 80)
    print("TEST 4: PDF Download Test")
    print("=" * 80)
    
    try:
        tool = CDMSLabelTool()
        
        print("\n🔍 Searching for Roundup labels...")
        result = tool.search(
            product_name="Roundup",
            max_results=5
        )
        
        if not result.get("success"):
            print(f"❌ Search failed: {result.get('error')}")
            return False
        
        # Try to download PDFs
        print("\n📥 Attempting to download PDFs...")
        download_result = tool.download_pdfs(result, "Roundup")
        
        if download_result.get("success"):
            print(f"✅ Download successful!")
            print(f"   Downloaded {download_result['pdf_count']} PDF(s)")
            
            for pdf in download_result.get("downloaded_pdfs", []):
                status = "📦 Cached" if pdf.get("cached") else "⬇️  Downloaded"
                print(f"\n   {status}: {pdf['filename']}")
                print(f"      Path: {pdf['filepath']}")
                print(f"      URL: {pdf['url']}")
        else:
            print(f"⚠️  Download result: {download_result.get('error', 'No PDFs found')}")
            if download_result.get("errors"):
                print("   Errors:")
                for error in download_result["errors"]:
                    print(f"      - {error}")
        
        return download_result.get("success", False)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_integration():
    """Test full integration via execute_cdms_label_tool"""
    print("\n" + "=" * 80)
    print("TEST 5: Full Integration Test (execute_cdms_label_tool)")
    print("=" * 80)
    
    try:
        print("\n🔍 Testing with question: 'Find Roundup label'")
        result = execute_cdms_label_tool("Find Roundup label")
        
        if result.get("success"):
            print("✅ Tool execution successful!")
            
            data = result.get("data", {})
            print(f"\n📊 Results:")
            print(f"   Product: {data.get('product_name')}")
            print(f"   Labels found: {data.get('label_count', 0)}")
            
            # Check PDF downloads
            pdf_downloads = data.get("pdf_downloads", {})
            if pdf_downloads.get("success"):
                print(f"   PDFs downloaded: {pdf_downloads.get('pdf_count', 0)}")
            else:
                print(f"   PDF downloads: {pdf_downloads.get('error', 'No PDFs found')}")
            
            return True
        else:
            print(f"❌ Tool execution failed: {result.get('error')}")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("CDMS PDF Download - Phase 1 Testing")
    print("=" * 80)
    print("\nThis will test:")
    print("1. PDF Downloader functionality")
    print("2. CDMS Tool search")
    print("3. PDF URL extraction")
    print("4. PDF download")
    print("5. Full integration")
    print("\n" + "=" * 80)
    
    results = []
    
    # Test 1: PDF Downloader
    try:
        test_pdf_downloader()
        results.append(("PDF Downloader", True))
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        results.append(("PDF Downloader", False))
    
    # Test 2: CDMS Tool Search
    try:
        success = test_cdms_tool_search()
        results.append(("CDMS Tool Search", success))
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        results.append(("CDMS Tool Search", False))
    
    # Test 3: PDF Extraction
    try:
        success = test_pdf_extraction()
        results.append(("PDF URL Extraction", success))
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        results.append(("PDF URL Extraction", False))
    
    # Test 4: PDF Download
    try:
        success = test_pdf_download()
        results.append(("PDF Download", success))
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
        results.append(("PDF Download", False))
    
    # Test 5: Full Integration
    try:
        success = test_full_integration()
        results.append(("Full Integration", success))
    except Exception as e:
        print(f"❌ Test 5 failed: {e}")
        results.append(("Full Integration", False))
    
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
        print("\n🎉 All tests passed! Phase 1 is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    main()






