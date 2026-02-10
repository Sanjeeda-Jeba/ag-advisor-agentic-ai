"""
PDF Processor
Extracts text from PDF files and chunks them for RAG
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import List, Dict, Tuple
import pdfplumber
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except ImportError:
    # Fallback for newer langchain versions
    from langchain_text_splitters import RecursiveCharacterTextSplitter


class PDFProcessor:
    """
    Processes PDF files: extracts text and chunks them
    
    Usage:
        processor = PDFProcessor()
        result = processor.process_pdf("path/to/document.pdf")
        chunks = result["chunks"]
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize PDF processor
        
        Args:
            chunk_size: Size of each text chunk in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len
        )
    
    def extract_text(self, pdf_path: str) -> Dict:
        """
        Extract text from PDF file
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Dict with extracted text and metadata:
            {
                "text": "full text content",
                "num_pages": 25,
                "pages": ["page 1 text", "page 2 text", ...]
            }
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_by_page = []
                full_text = []
                
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_by_page.append(page_text)
                        full_text.append(page_text)
                
                return {
                    "text": "\n\n".join(full_text),
                    "num_pages": len(pdf.pages),
                    "pages": text_by_page,
                    "success": True
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to extract text from PDF: {str(e)}",
                "text": "",
                "num_pages": 0,
                "pages": []
            }
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks
        
        Args:
            text: Text to chunk
        
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        chunks = self.text_splitter.split_text(text)
        return chunks
    
    def get_chunks_with_pages(self, pdf_path: str) -> List[Tuple[str, int]]:
        """
        Get chunks with their page numbers
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            List of tuples: (chunk_text, page_number)
        """
        result = self.process_pdf(pdf_path)
        
        if not result.get("success"):
            return []
        
        chunks = result.get("chunks", [])
        page_numbers = result.get("page_numbers", [])
        
        # Pair chunks with page numbers
        return list(zip(chunks, page_numbers))
    
    def process_pdf(self, pdf_path: str) -> Dict:
        """
        Complete PDF processing: extract and chunk with accurate page tracking
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Dict with chunks and metadata:
            {
                "success": True,
                "chunks": ["chunk 1", "chunk 2", ...],
                "page_numbers": [1, 1, 2, 2, ...],  # Exact page for each chunk
                "num_chunks": 15,
                "num_pages": 25,
                "file_path": "path/to/file.pdf"
            }
        """
        # Extract text page-by-page
        extraction_result = self.extract_text(pdf_path)
        
        if not extraction_result.get("success"):
            return extraction_result
        
        # Chunk within pages (don't split across pages)
        chunks = []
        page_numbers = []
        
        pages = extraction_result.get("pages", [])
        
        for page_num, page_text in enumerate(pages, 1):
            if not page_text or not page_text.strip():
                continue
            
            # PHASE 2 FIX: Validate page number is positive
            if page_num <= 0:
                print(f"⚠️  Warning: Invalid page number {page_num} in PDF {pdf_path}, skipping")
                continue
            
            # Chunk this page's text
            page_chunks = self.text_splitter.split_text(page_text)
            
            # Add chunks with page number
            for chunk in page_chunks:
                if chunk.strip():  # Only add non-empty chunks
                    chunks.append(chunk)
                    page_numbers.append(page_num)
        
        # PHASE 2 FIX: Validate that page_numbers list matches chunks list
        if len(page_numbers) != len(chunks):
            print(f"⚠️  Warning: Page numbers count ({len(page_numbers)}) doesn't match chunks count ({len(chunks)}) for {pdf_path}")
            # Fix by padding or truncating to match
            if len(page_numbers) < len(chunks):
                # Pad with last known page number or estimate
                last_page = page_numbers[-1] if page_numbers else 1
                page_numbers.extend([last_page] * (len(chunks) - len(page_numbers)))
            else:
                # Truncate to match chunks
                page_numbers = page_numbers[:len(chunks)]
        
        # PHASE 2 FIX: Validate all page numbers are positive
        invalid_pages = [i for i, pn in enumerate(page_numbers) if pn <= 0]
        if invalid_pages:
            print(f"⚠️  Warning: Found {len(invalid_pages)} invalid page numbers (<= 0) in {pdf_path}")
            # Fix invalid page numbers by using estimated values
            for idx in invalid_pages:
                # Estimate based on chunk index (rough: 3 chunks per page)
                estimated_page = (idx // 3) + 1
                page_numbers[idx] = estimated_page
                print(f"   Fixed chunk {idx}: page_number set to {estimated_page}")
        
        return {
            "success": True,
            "chunks": chunks,
            "page_numbers": page_numbers,  # PHASE 2 FIX: Validated page numbers
            "num_chunks": len(chunks),
            "num_pages": extraction_result["num_pages"],
            "file_path": pdf_path,
            "full_text": extraction_result["text"]
        }


# Test function
if __name__ == "__main__":
    print("Testing PDF Processor...")
    print("-" * 70)
    
    processor = PDFProcessor()
    
    # Test with a sample PDF (if available)
    pdf_path = Path(__file__).parent.parent.parent / "data" / "pdfs"
    
    if pdf_path.exists() and any(pdf_path.glob("*.pdf")):
        pdf_files = list(pdf_path.glob("*.pdf"))
        test_file = pdf_files[0]
        
        print(f"📄 Processing: {test_file.name}")
        result = processor.process_pdf(str(test_file))
        
        if result["success"]:
            print(f"✅ Success!")
            print(f"   Pages: {result['num_pages']}")
            print(f"   Chunks: {result['num_chunks']}")
            
            # Show page numbers if available
            if "page_numbers" in result:
                print(f"\n   Page tracking: ✅ Enabled")
                if result["page_numbers"]:
                    unique_pages = sorted(set(result["page_numbers"]))
                    print(f"   Pages with chunks: {unique_pages[:10]}{'...' if len(unique_pages) > 10 else ''}")
            
            print(f"\n   First chunk preview:")
            if result["chunks"]:
                page_info = ""
                if "page_numbers" in result and result["page_numbers"]:
                    page_info = f" (Page {result['page_numbers'][0]})"
                print(f"   {result['chunks'][0][:200]}...{page_info}")
        else:
            print(f"❌ Error: {result.get('error')}")
    else:
        print("⚠️  No PDF files found in data/pdfs/")
        print("\n💡 To test:")
        print("   1. Create data/pdfs/ folder")
        print("   2. Add some PDF files")
        print("   3. Run this script again")

