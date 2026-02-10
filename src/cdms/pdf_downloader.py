"""
CDMS PDF Downloader
Downloads PDFs from CDMS URLs found via Tavily with URL hash-based caching
"""

import sys
from pathlib import Path
from typing import Dict, Optional, List
import hashlib
import requests
from urllib.parse import urlparse

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class CDMSPDFDownloader:
    """
    Downloads PDFs from CDMS URLs found via Tavily
    
    Features:
    - URL hash-based caching (avoid re-downloading)
    - Automatic re-download if URL changes
    - Error handling for network issues
    - Filename sanitization
    """
    
    def __init__(self, download_folder: str = "data/pdfs/cdms"):
        """
        Initialize PDF downloader
        
        Args:
            download_folder: Folder to store downloaded PDFs
        """
        self.download_folder = Path(download_folder)
        self.download_folder.mkdir(parents=True, exist_ok=True)
        
        # Download settings
        self.timeout = 30  # seconds
        self.max_file_size = 50 * 1024 * 1024  # 50 MB max
    
    def _generate_url_hash(self, url: str) -> str:
        """
        Generate a hash from URL for filename
        
        Args:
            url: PDF URL
            
        Returns:
            Short hash string (first 12 characters of MD5)
        """
        return hashlib.md5(url.encode()).hexdigest()[:12]
    
    def _sanitize_filename(self, product_name: str) -> str:
        """
        Sanitize product name for use in filename
        
        Args:
            product_name: Product name (e.g., "Roundup", "2,4-D")
            
        Returns:
            Sanitized string safe for filenames
        """
        # Replace problematic characters
        sanitized = product_name.replace(" ", "_").replace(",", "").replace("/", "_")
        sanitized = "".join(c for c in sanitized if c.isalnum() or c in ("_", "-"))
        return sanitized.lower()
    
    def _get_expected_filename(self, url: str, product_name: str) -> Path:
        """
        Get expected filename for a URL
        
        Args:
            url: PDF URL
            product_name: Product name
            
        Returns:
            Path to expected file
        """
        url_hash = self._generate_url_hash(url)
        sanitized_name = self._sanitize_filename(product_name)
        filename = f"{sanitized_name}_{url_hash}.pdf"
        return self.download_folder / filename
    
    def _is_pdf_url(self, url: str) -> bool:
        """
        Check if URL points to a PDF
        
        Args:
            url: URL to check
            
        Returns:
            True if URL appears to be a PDF
        """
        url_lower = url.lower()
        # Check extension
        if url_lower.endswith('.pdf'):
            return True
        # Check content-type hint in URL
        if '.pdf' in url_lower or 'pdf' in url_lower:
            return True
        return False
    
    def _download_file(self, url: str, filepath: Path) -> bool:
        """
        Download file from URL
        
        Args:
            url: URL to download from
            filepath: Path to save file
            
        Returns:
            True if download successful, False otherwise
        """
        try:
            print(f"      📡 Fetching: {url[:60]}...")
            response = requests.get(
                url,
                timeout=self.timeout,
                stream=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('Content-Type', '').lower()
            if 'pdf' not in content_type and not self._is_pdf_url(url):
                print(f"      ⚠️  Warning: Content-Type is {content_type}, not PDF (but proceeding)")
            
            # Download with size limit
            total_size = 0
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        total_size += len(chunk)
                        if total_size > self.max_file_size:
                            filepath.unlink(missing_ok=True)  # Delete partial file
                            raise ValueError(f"File too large (>{self.max_file_size / 1024 / 1024} MB)")
                        f.write(chunk)
            
            # Verify file was written
            if not filepath.exists():
                raise ValueError("File was not created after download")
            
            # Verify file is not empty
            file_size = filepath.stat().st_size
            if file_size == 0:
                filepath.unlink(missing_ok=True)
                raise ValueError("Downloaded file is empty (0 bytes)")
            
            print(f"      ✅ Downloaded {file_size:,} bytes")
            return True
            
        except requests.exceptions.Timeout:
            filepath.unlink(missing_ok=True)
            raise Exception(f"Download timeout after {self.timeout}s")
        except requests.exceptions.HTTPError as e:
            filepath.unlink(missing_ok=True)
            raise Exception(f"HTTP error {e.response.status_code}: {str(e)}")
        except requests.exceptions.RequestException as e:
            filepath.unlink(missing_ok=True)
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            filepath.unlink(missing_ok=True)
            raise
    
    def download_pdf(self, url: str, product_name: str) -> Dict:
        """
        Download PDF from URL with caching
        
        Args:
            url: PDF URL
            product_name: Product name (for filename)
            
        Returns:
            Dict with:
                - success: bool
                - filepath: str (path to downloaded file)
                - filename: str (just filename)
                - cached: bool (True if file already existed)
                - url_hash: str (hash of URL)
        """
        if not self._is_pdf_url(url):
            return {
                "success": False,
                "error": f"URL does not appear to be a PDF: {url}",
                "url": url
            }
        
        # Generate expected filename
        expected_file = self._get_expected_filename(url, product_name)
        url_hash = self._generate_url_hash(url)
        
        # Check if file already exists (cached)
        if expected_file.exists():
            return {
                "success": True,
                "filepath": str(expected_file),
                "filename": expected_file.name,
                "cached": True,
                "url_hash": url_hash,
                "url": url
            }
        
        # File doesn't exist or URL changed - download
        try:
            # Ensure download folder exists
            self.download_folder.mkdir(parents=True, exist_ok=True)
            
            # Attempt download
            self._download_file(url, expected_file)
            
            # Verify file was actually created
            if not expected_file.exists():
                return {
                    "success": False,
                    "error": f"Download completed but file not found at {expected_file}",
                    "url": url,
                    "url_hash": url_hash
                }
            
            # Verify file is not empty
            file_size = expected_file.stat().st_size
            if file_size == 0:
                expected_file.unlink()  # Delete empty file
                return {
                    "success": False,
                    "error": "Downloaded file is empty (0 bytes)",
                    "url": url,
                    "url_hash": url_hash
                }
            
            return {
                "success": True,
                "filepath": str(expected_file),
                "filename": expected_file.name,
                "cached": False,
                "url_hash": url_hash,
                "url": url,
                "file_size": file_size  # Include file size for verification
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Network error: {str(e)}",
                "url": url,
                "url_hash": url_hash
            }
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Download exception for {url}:")
            print(error_details)
            return {
                "success": False,
                "error": f"Download failed: {str(e)}",
                "url": url,
                "url_hash": url_hash
            }
    
    def extract_pdf_urls(self, tavily_results: Dict) -> List[str]:
        """
        Extract PDF URLs from Tavily search results
        
        Args:
            tavily_results: Results from TavilyAPIClient.search() or search_cdms_labels()
            
        Returns:
            List of PDF URLs (top 3 most relevant)
        """
        if not tavily_results.get("success"):
            return []
        
        pdf_urls = []
        
        # First, check labels field (from CDMS tool formatting)
        labels = tavily_results.get("labels", [])
        if labels:
            # Labels are already formatted, use them
            for label in labels:
                url = label.get("url", "")
                if url and self._is_pdf_url(url):
                    pdf_urls.append(url)
                    if len(pdf_urls) >= 3:
                        break
            if pdf_urls:
                return pdf_urls
        
        # Fallback: check raw results
        # Get all results (not just sorted by score, but filter for PDFs first)
        results = tavily_results.get("results", [])
        
        # First pass: collect all PDF URLs
        all_pdf_urls = []
        for result in results:
            url = result.get("url", "")
            if url and self._is_pdf_url(url):
                score = result.get("score", 0.0)
                all_pdf_urls.append((url, score))
        
        # Sort PDF URLs by score (relevance) descending
        all_pdf_urls.sort(key=lambda x: x[1], reverse=True)
        
        # Take top 3 PDFs
        for url, _ in all_pdf_urls[:3]:
            pdf_urls.append(url)
        
        return pdf_urls
    
    def get_downloaded_pdfs(self, product_name: Optional[str] = None) -> List[Dict]:
        """
        Get list of already downloaded PDFs
        
        Args:
            product_name: Optional filter by product name
            
        Returns:
            List of dicts with file info
        """
        pdf_files = list(self.download_folder.glob("*.pdf"))
        
        downloaded = []
        for pdf_file in pdf_files:
            if product_name:
                sanitized = self._sanitize_filename(product_name)
                if sanitized not in pdf_file.name:
                    continue
            
            downloaded.append({
                "filepath": str(pdf_file),
                "filename": pdf_file.name,
                "size": pdf_file.stat().st_size,
                "modified": pdf_file.stat().st_mtime
            })
        
        return downloaded


# Test function
if __name__ == "__main__":
    print("=" * 80)
    print("Testing CDMS PDF Downloader")
    print("=" * 80)
    
    downloader = CDMSPDFDownloader()
    
    # Test URL hash generation
    test_url = "https://cdms.net/labels/roundup.pdf"
    url_hash = downloader._generate_url_hash(test_url)
    print(f"\n✅ URL Hash Test:")
    print(f"   URL: {test_url}")
    print(f"   Hash: {url_hash}")
    
    # Test filename generation
    expected_file = downloader._get_expected_filename(test_url, "Roundup")
    print(f"\n✅ Filename Test:")
    print(f"   Expected: {expected_file.name}")
    
    # Test PDF URL detection
    print(f"\n✅ PDF URL Detection:")
    print(f"   {test_url}: {downloader._is_pdf_url(test_url)}")
    print(f"   https://example.com/page: {downloader._is_pdf_url('https://example.com/page')}")
    
    # Test downloaded PDFs
    downloaded = downloader.get_downloaded_pdfs()
    print(f"\n✅ Downloaded PDFs: {len(downloaded)}")
    for pdf in downloaded[:5]:  # Show first 5
        print(f"   - {pdf['filename']} ({pdf['size']} bytes)")
    
    print("\n" + "=" * 80)
    print("✅ Tests complete!")
    print("=" * 80)

