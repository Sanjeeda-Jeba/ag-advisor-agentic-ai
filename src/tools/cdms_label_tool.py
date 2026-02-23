"""
CDMS Label Search Tool
Search for pesticide product labels from the CDMS database with full citations
"""

from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api_clients.tavily_client import TavilyAPIClient
from src.cdms.pdf_downloader import CDMSPDFDownloader
from src.cdms.rag_search import CDMSRAGSearch
from src.cdms.document_loader import DocumentLoader
from src.rag.vector_store import QdrantVectorStore


class CDMSLabelTool:
    """
    Tool for searching CDMS pesticide labels
    
    Uses Tavily with domain filtering (cdms.net) to find accurate label information
    with full citations and source URLs.
    
    Creates a single shared QdrantVectorStore and passes it to both
    DocumentLoader (writes) and CDMSRAGSearch (reads) so they always
    see the same data — even on in-memory or local-disk fallback.
    """
    
    def __init__(self):
        """Initialize the CDMS label search tool with a shared vector store"""
        self.client = TavilyAPIClient()
        self.pdf_downloader = CDMSPDFDownloader()
        
        # Create ONE shared QdrantVectorStore for all components
        self._shared_vector_store = QdrantVectorStore()
        
        # Pass the shared instance to both readers and writers
        self.rag_search = CDMSRAGSearch(vector_store=self._shared_vector_store)
        self.document_loader = DocumentLoader(
            pdf_folder="data/pdfs/cdms",
            vector_store=self._shared_vector_store,
        )
        
        self.tool_name = "cdms_label_search"
        self.description = "Search for pesticide product labels and safety data sheets from the CDMS database"
    
    def search(
        self,
        product_name: str,
        active_ingredient: Optional[str] = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search for CDMS pesticide labels
        
        Args:
            product_name: Product or brand name (e.g., "Roundup", "Sevin")
            active_ingredient: Optional active ingredient (e.g., "glyphosate")
            max_results: Maximum number of label results to return (1-5)
        
        Returns:
            Dict with:
                - success: bool
                - product_name: str
                - active_ingredient: str or None
                - summary: str (AI-generated summary)
                - labels: List[Dict] with:
                    - title: str (label name)
                    - url: str (direct PDF link)
                    - snippet: str (preview text)
                    - relevance: float (0-1)
                - label_count: int
                - citations: str (formatted citation text)
        """
        # Perform search via Tavily client
        raw_results = self.client.search_cdms_labels(
            product_name=product_name,
            active_ingredient=active_ingredient,
            max_results=max_results
        )
        
        if not raw_results.get("success"):
            return {
                "success": False,
                "error": raw_results.get("error", "Search failed"),
                "product_name": product_name,
                "labels": [],
                "label_count": 0
            }
        
        # Format results with full citation info
        labels = []
        for result in raw_results.get("results", []):
            label = {
                "title": result.get("title", "No title"),
                "url": result.get("url", ""),
                "snippet": result.get("content", "")[:300],  # First 300 chars
                "relevance": result.get("score", 0.0)
            }
            labels.append(label)
        
        # Generate formatted citations
        citations = self._format_citations(labels)
        
        # Build response
        return {
            "success": True,
            "product_name": product_name,
            "active_ingredient": active_ingredient,
            "summary": raw_results.get("answer", ""),
            "labels": labels,
            "label_count": len(labels),
            "citations": citations,
            "query_used": raw_results.get("query", ""),
            "search_metadata": raw_results.get("search_metadata", {}),
            "raw_tavily_results": raw_results,  # Keep for PDF extraction
            # Pass through multi-source metadata from Tavily client
            "source": raw_results.get("source", "unknown"),
            "sources_tried": raw_results.get("sources_tried", []),
        }
    
    def _format_citations(self, labels: list) -> str:
        """
        Format label results as citation text
        
        Args:
            labels: List of label results
        
        Returns:
            Formatted citation string
        """
        if not labels:
            return "No citations available."
        
        citation_parts = ["**Sources:**\n"]
        
        for i, label in enumerate(labels, 1):
            citation_parts.append(
                f"{i}. **{label['title']}**\n"
                f"   - URL: {label['url']}\n"
                f"   - Relevance: {label['relevance']:.2f}\n"
            )
        
        return "\n".join(citation_parts)
    
    def format_response_for_user(self, result: Dict[str, Any]) -> str:
        """
        Format search results for user-friendly display
        
        Args:
            result: Search result from search()
        
        Returns:
            Formatted string for display to user
        """
        if not result.get("success"):
            return f"❌ Could not find labels: {result.get('error', 'Unknown error')}"
        
        product = result.get("product_name", "Unknown product")
        ingredient = result.get("active_ingredient")
        summary = result.get("summary", "")
        labels = result.get("labels", [])
        
        # Build response
        response_parts = []
        
        # Header
        if ingredient:
            response_parts.append(f"**CDMS Labels for {product} ({ingredient})**\n")
        else:
            response_parts.append(f"**CDMS Labels for {product}**\n")
        
        # Summary
        if summary:
            response_parts.append(f"**Summary:** {summary}\n")
        
        # Labels found
        response_parts.append(f"**Found {len(labels)} label(s):**\n")
        
        for i, label in enumerate(labels, 1):
            response_parts.append(
                f"{i}. **{label['title']}**\n"
                f"   📄 Download: {label['url']}\n"
                f"   📝 Preview: {label['snippet'][:150]}...\n"
            )
        
        # Citations
        response_parts.append(f"\n{result.get('citations', '')}")
        
        return "\n".join(response_parts)
    
    def download_pdfs(self, tavily_results: Dict[str, Any], product_name: str) -> Dict[str, Any]:
        """
        Download PDFs from Tavily search results
        
        Args:
            tavily_results: Results from search() method (includes raw_tavily_results)
            product_name: Product name for filename
        
        Returns:
            Dict with:
                - success: bool
                - downloaded_pdfs: List[Dict] with filepath, filename, cached status
                - pdf_count: int
                - errors: List[str] (any download errors)
        """
        # Extract PDF URLs from Tavily results
        raw_results = tavily_results.get("raw_tavily_results", tavily_results)
        pdf_urls = self.pdf_downloader.extract_pdf_urls(raw_results)
        
        if not pdf_urls:
            print(f"⚠️  No PDF URLs found in Tavily results for {product_name}")
            # Also check labels directly
            labels = tavily_results.get("labels", [])
            for label in labels:
                url = label.get("url", "")
                if url and (url.lower().endswith('.pdf') or 'pdf' in url.lower()):
                    pdf_urls.append(url)
                    print(f"   Found PDF URL in labels: {url}")
            
            if not pdf_urls:
                return {
                    "success": False,
                    "error": "No PDF URLs found in search results",
                    "downloaded_pdfs": [],
                    "pdf_count": 0
                }
        
        print(f"📥 Found {len(pdf_urls)} PDF URL(s) to download for {product_name}")
        
        # Download top 3 PDFs
        downloaded_pdfs = []
        errors = []
        
        for i, url in enumerate(pdf_urls[:3], 1):  # Top 3
            print(f"   Downloading PDF {i}/{min(len(pdf_urls), 3)}: {url[:60]}...")
            result = self.pdf_downloader.download_pdf(url, product_name)
            if result.get("success"):
                cached_status = "cached" if result.get("cached") else "downloaded"
                print(f"   ✅ {cached_status}: {result.get('filename')}")
                downloaded_pdfs.append({
                    "filepath": result["filepath"],
                    "filename": result["filename"],
                    "cached": result["cached"],
                    "url": result["url"],
                    "url_hash": result["url_hash"]
                })
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"   ❌ Failed: {error_msg}")
                errors.append(f"Failed to download {url}: {error_msg}")
        
        if downloaded_pdfs:
            print(f"✅ Successfully downloaded {len(downloaded_pdfs)} PDF(s)")
        else:
            print(f"❌ No PDFs were downloaded")
        
        return {
            "success": len(downloaded_pdfs) > 0,
            "downloaded_pdfs": downloaded_pdfs,
            "pdf_count": len(downloaded_pdfs),
            "errors": errors if errors else None
        }
    
    def _is_pdf_indexed(self, pdf_path: str) -> bool:
        """
        Check if PDF is already indexed in both database AND Qdrant
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if PDF is indexed in both DB and Qdrant, False otherwise
        """
        try:
            from src.cdms.schema import Document
            # Reuse the document_loader's db_manager to avoid competing SQLite connections
            session = self.document_loader.db_manager.get_session()
            
            try:
                pdf_path_obj = Path(pdf_path)
                doc_id = Document.generate_id(str(pdf_path_obj))
                existing_doc = session.query(Document).filter_by(id=doc_id).first()
                
                # Check if marked as processed in database
                if existing_doc and existing_doc.processed == 1:
                    # Also verify chunks actually exist in Qdrant
                    if self.rag_search.vector_store:
                        try:
                            if self.rag_search.vector_store.client.collection_exists("cdms_documents"):
                                # Check if there are any chunks for this document
                                collection_info = self.rag_search.vector_store.client.get_collection("cdms_documents")
                                if collection_info.points_count > 0:
                                    return True
                                else:
                                    # Database says processed but Qdrant is empty - need to reprocess
                                    return False
                            else:
                                # Collection doesn't exist - not indexed
                                return False
                        except Exception as e:
                            # If we can't check Qdrant, assume not indexed to be safe
                            print(f"⚠️  Warning: Could not verify Qdrant chunks for {pdf_path_obj.name}: {e}")
                            return False
                    else:
                        # No vector store available - can't verify
                        return False
                return False
            finally:
                session.close()
        except Exception as e:
            print(f"⚠️  Warning: Error checking if PDF is indexed: {e}")
            return False
    
    def search_with_rag(
        self,
        product_name: str,
        user_question: str,
        active_ingredient: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Full RAG pipeline: Tavily → Download → Process → Index → RAG Search
        
        Args:
            product_name: Product name (e.g., "Roundup")
            user_question: User's question (e.g., "What's the application rate?")
            active_ingredient: Optional active ingredient
        
        Returns:
            Dict with:
                - success: bool
                - product_name: str
                - rag_chunks: List[Dict] with content, page_number, score
                - pdfs_downloaded: int
                - pdfs_indexed: int
                - total_chunks_found: int
        """
        # Step 1: Search for label PDFs across multiple databases (CDMS → Greenbook → EPA → …)
        print(f"🔍 Step 1: Searching label databases for '{product_name}' (fallback chain)...")
        tavily_result = self.search(
            product_name=product_name,
            active_ingredient=active_ingredient,
            max_results=3
        )
        
        if not tavily_result.get("success"):
            error_msg = tavily_result.get("error", "Label search failed")
            print(f"❌ Label search failed: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "product_name": product_name
            }
        
        labels_found = tavily_result.get("label_count", 0)
        search_source = tavily_result.get("source", "unknown")
        sources_tried = tavily_result.get("sources_tried", [])
        print(f"✅ Label search successful: Found {labels_found} label(s) via {search_source}")
        if len(sources_tried) > 1:
            print(f"   Sources tried: {' → '.join(sources_tried)}")
        
        # Step 2: Download PDFs
        print(f"📥 Step 2: Downloading PDFs for '{product_name}'...")
        download_result = self.download_pdfs(tavily_result, product_name)
        
        if not download_result.get("success"):
            error_msg = download_result.get("error", "PDF download failed")
            print(f"❌ PDF download failed: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "product_name": product_name
            }
        
        downloaded_pdfs = download_result.get("downloaded_pdfs", [])
        
        # Step 3: Process and index PDFs (if not already indexed)
        pdfs_indexed = 0
        print(f"📚 Indexing {len(downloaded_pdfs)} downloaded PDF(s)...")
        for pdf_info in downloaded_pdfs:
            pdf_path = pdf_info["filepath"]
            pdf_url = pdf_info.get("url", "")  # PHASE 1 FIX: Get URL from download info
            
            # Check if already indexed
            is_indexed = self._is_pdf_indexed(pdf_path)
            if is_indexed:
                print(f"   ⏭️  {Path(pdf_path).name}: Already indexed (skipping)")
            else:
                # Process and index with PDF URL
                print(f"   📄 Indexing: {Path(pdf_path).name}...")
                try:
                    index_result = self.document_loader.load_pdf(
                        pdf_path, 
                        force_reprocess=False,
                        pdf_url=pdf_url,  # PHASE 1 FIX: Pass PDF URL to store in metadata
                        product_name=product_name  # For Qdrant native filtering
                    )
                    if index_result.get("success"):
                        chunks = index_result.get("chunks_stored", 0)
                        embeddings = index_result.get("embeddings_generated", 0)
                        if index_result.get("skipped"):
                            print(f"   ⏭️  {Path(pdf_path).name}: Already processed (skipped)")
                        else:
                            print(f"   ✅ {Path(pdf_path).name}: {chunks} chunks, {embeddings} embeddings")
                            pdfs_indexed += 1
                    else:
                        error = index_result.get("error", "Unknown error")
                        print(f"   ❌ Failed to index {Path(pdf_path).name}: {error}")
                except Exception as e:
                    print(f"   ❌ Error indexing {Path(pdf_path).name}: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Step 4: Verify Qdrant has chunks before searching
        qdrant_chunks_count = 0
        if self.rag_search.vector_store:
            try:
                if self.rag_search.vector_store.client.collection_exists("cdms_documents"):
                    collection_info = self.rag_search.vector_store.client.get_collection("cdms_documents")
                    qdrant_chunks_count = collection_info.points_count
                    print(f"📊 Qdrant status: {qdrant_chunks_count} chunk(s) in database")
                else:
                    print(f"⚠️  Warning: Qdrant collection 'cdms_documents' does not exist")
            except Exception as e:
                print(f"⚠️  Warning: Could not check Qdrant status: {e}")
        
        # Step 5: RAG search
        print(f"🔍 Searching Qdrant for: '{user_question}'...")
        rag_chunks = self.rag_search.search(
            query=user_question,
            product_name=product_name,
            limit=5,
            score_threshold=0.3
        )
        print(f"   Found {len(rag_chunks)} chunk(s) from RAG search")
        
        # If no chunks found but PDFs were indexed, suggest reprocessing
        if len(rag_chunks) == 0 and pdfs_indexed > 0:
            print(f"⚠️  Warning: PDFs were indexed but no chunks found in search. This may indicate:")
            print(f"   - Embeddings weren't generated (check OpenAI API key)")
            print(f"   - Qdrant is using in-memory mode (data lost)")
            print(f"   - Try force reprocessing: set force_reprocess=True")
        
        # PHASE 1 FIX: Create multiple mapping strategies for PDF URL matching
        # Strategy 1: Filename to URL mapping (for backwards compatibility)
        filename_to_url = {}
        # Strategy 2: Document ID to URL mapping (more reliable)
        document_id_to_url = {}
        # Strategy 3: URL hash to URL mapping (most reliable)
        url_hash_to_url = {}
        
        for pdf_info in downloaded_pdfs:
            filename = pdf_info.get("filename", "")
            url = pdf_info.get("url", "")
            url_hash = pdf_info.get("url_hash", "")
            
            if filename and url:
                filename_to_url[filename] = url
            if url_hash and url:
                url_hash_to_url[url_hash] = url
        
        # Strategy 4: Create mapping from Tavily labels (fallback for PDFs not downloaded)
        tavily_urls = {}
        tavily_labels = tavily_result.get("labels", [])
        for label in tavily_labels:
            url = label.get("url", "")
            if url and url.lower().endswith('.pdf'):
                # Use URL as key (for direct matching)
                tavily_urls[url] = url
                # Also try to match by extracting identifier from URL
                # CDMS URLs often have format: .../ldat/mp50B003.pdf
                if '/ldat/' in url:
                    url_id = url.split('/ldat/')[-1].replace('.pdf', '')
                    tavily_urls[url_id] = url
        
        # PHASE 1 FIX: Enhanced URL matching with multiple fallback strategies
        chunks_with_url = 0
        chunks_without_url = 0
        
        for chunk in rag_chunks:
            # Strategy 1: Check if URL already in chunk (from Qdrant metadata - preferred)
            if chunk.get("pdf_url"):
                chunks_with_url += 1
                continue  # Already has URL from metadata
            
            source_file = chunk.get("source_file", "")
            document_id = chunk.get("document_id", "")
            chunk_url_hash = chunk.get("url_hash", "")
            
            # Strategy 2: Match by URL hash (most reliable - from Qdrant metadata)
            if chunk_url_hash and chunk_url_hash in url_hash_to_url:
                chunk["pdf_url"] = url_hash_to_url[chunk_url_hash]
                chunks_with_url += 1
                continue
            
            # Strategy 3: Match by document_id (reliable - from Qdrant metadata)
            # Document IDs are generated from filepath, so we can match by checking downloaded PDFs
            if document_id:
                for pdf_info in downloaded_pdfs:
                    # Generate document ID from filepath to match
                    from src.cdms.schema import Document
                    pdf_doc_id = Document.generate_id(pdf_info["filepath"])
                    if pdf_doc_id == document_id:
                        chunk["pdf_url"] = pdf_info.get("url", "")
                        if chunk["pdf_url"]:
                            chunks_with_url += 1
                            break
                if chunk.get("pdf_url"):
                    continue
            
            # Strategy 4: Match by exact filename
            if source_file in filename_to_url:
                chunk["pdf_url"] = filename_to_url[source_file]
                chunks_with_url += 1
                continue
            
            # Strategy 5: Match by source_file partial match (handle sanitized filenames)
            # Try to find URL by matching product name in filename
            product_lower = product_name.lower()
            matched = False
            for filename, url in filename_to_url.items():
                if product_lower in filename.lower():
                    chunk["pdf_url"] = url
                    chunks_with_url += 1
                    matched = True
                    break
            
            if matched:
                continue
            
            # Strategy 6: Fallback to Tavily labels (if no match found)
            if not chunk.get("pdf_url"):
                # Try to match by checking if any Tavily URL matches
                # This is a last resort - use first available Tavily URL
                if tavily_urls:
                    # Use the first Tavily URL as fallback
                    chunk["pdf_url"] = list(tavily_urls.values())[0]
                    chunks_with_url += 1
                else:
                    chunks_without_url += 1
                    print(f"⚠️  Warning: Could not find PDF URL for chunk from {source_file} (document_id: {document_id})")
        
        # Log URL matching results
        if chunks_without_url > 0:
            print(f"⚠️  Warning: {chunks_without_url} chunk(s) missing PDF URLs")
        print(f"✅ PDF URL matching: {chunks_with_url}/{len(rag_chunks)} chunks have URLs")
        
        # Step 5: Return results
        return {
            "success": True,
            "product_name": product_name,
            "rag_chunks": rag_chunks,
            "pdfs_downloaded": len(downloaded_pdfs),
            "pdfs_indexed": pdfs_indexed,
            "total_chunks_found": len(rag_chunks),
            # Ensure Tavily-only response path has the fields it expects when rag_chunks is empty
            "summary": tavily_result.get("summary", ""),
            "labels": tavily_result.get("labels", []),
            "citations": tavily_result.get("citations", ""),
            "tavily_results": tavily_result,
            "download_info": download_result,
            "pdf_urls": list(filename_to_url.values()),  # All PDF URLs
            "tavily_labels": tavily_labels,  # Include Tavily labels with URLs
            # Multi-source metadata
            "label_source": tavily_result.get("source", "CDMS"),
            "sources_tried": tavily_result.get("sources_tried", ["CDMS"]),
        }


# ── Shared constants for product extraction ──────────────────────────
# All pesticide category/type words — used to identify the boundary
# between a product name and its category suffix.
CATEGORY_WORDS = {
    "pesticide", "herbicide", "insecticide", "fungicide",
    "termiticide", "acaricide", "nematicide", "rodenticide",
    "molluscicide", "miticide", "bactericide", "algicide",
    "larvicide", "fumigant", "repellent", "desiccant",
}

# Words that should NEVER be part of a product name.
_EXTRACTION_NOISE = (
    {"the", "a", "an", "find", "get", "show", "search", "for", "of",
     "what", "what's", "whats", "how", "is", "are", "tell", "me",
     "about", "rei", "re-entry", "reentry", "restricted", "entry",
     "interval", "rate", "application", "safety", "mixing",
     "instructions", "information", "data", "sheet", "from", "cdms",
     "label", "labels", "sds"}
    | CATEGORY_WORDS  # category words are boundaries, not product names
)


def _extract_product_words_before(words: list, anchor_idx: int, max_words: int = 4) -> str:
    """
    Walk backwards from *anchor_idx* in *words*, collecting product-name
    tokens until we hit a noise/category word or reach *max_words*.
    Returns the joined product name or empty string.
    """
    parts = []
    for i in range(anchor_idx - 1, -1, -1):
        w = words[i]
        if w in _EXTRACTION_NOISE:
            break
        parts.insert(0, w)
        if len(parts) >= max_words:
            break
    return " ".join(parts)


def _extract_product_words_after(words: list, anchor_idx: int, max_words: int = 4) -> str:
    """
    Walk forwards from the word AFTER *anchor_idx*, collecting product-name
    tokens until we hit a noise/category word or reach *max_words*.
    Skips minor noise words like 'the', 'a'.
    Returns the joined product name or empty string.
    """
    skip = {"the", "a", "an", "this", "that"}
    parts = []
    for w in words[anchor_idx + 1:]:
        if w in skip:
            continue
        if w in _EXTRACTION_NOISE:
            break
        parts.append(w)
        if len(parts) >= max_words:
            break
    return " ".join(parts)


def execute_cdms_label_tool(question: str, conversation_context: list = None) -> Dict:
    """
    Execute CDMS label search tool
    
    This is the interface for the tool executor.
    Extracts product name and active ingredient from the question and searches CDMS.
    Uses conversation context for follow-up questions.
    
    Args:
        question: User's natural language question
        conversation_context: Optional list of previous messages for context
    
    Returns:
        Dict with:
        {
            "success": True/False,
            "tool": "cdms_label",
            "data": {...search results with citations...},
            "error": "error message" if failed
        }
    """
    try:
        import re
        
        # ── Clean question ──────────────────────────────────────────────
        question_clean = re.sub(r'[®™©]', '', question).strip()
        question_lower = question_clean.lower()
        words = question_lower.split()
        
        product_name = None
        active_ingredient = None
        # Track whether the product was extracted from the *current* question
        # (vs. conversation context). This prevents follow-up logic from
        # overwriting a product the user explicitly named.
        product_from_current_question = False
        
        # Well-known products (fast path — NOT the only path)
        KNOWN_PRODUCTS = [
            "roundup", "sevin", "2,4-d", "glyphosate", "carbaryl", "atrazine",
            "machete", "megalodon", "crossbow", "prowl", "gramoxone", "paraquat",
            "dicamba", "liberty", "enlist", "laudis", "callisto", "acuron",
            "warrant", "dual magnum", "metolachlor", "trifluralin",
        ]
        
        # ── Step 1: Check known products in current question (fast path) ─
        for keyword in KNOWN_PRODUCTS:
            if keyword in question_lower:
                product_name = keyword
                product_from_current_question = True
                break
        
        # ── Step 2: Flexible extraction from the *current* question ──────
        #    This runs even if Step 1 found nothing, BEFORE conversation
        #    context, so a new product in the question always wins.
        if not product_name:
            # Pattern A: "label for X …" / "X … label"
            if "label" in words:
                label_idx = words.index("label")
                # "label for X …" → take words AFTER "label for"
                if label_idx + 1 < len(words) and words[label_idx + 1] == "for":
                    potential = _extract_product_words_after(words, label_idx + 1)
                    if potential:
                        product_name = potential
                        product_from_current_question = True
                # "X … label" → take words BEFORE "label"
                if not product_name and label_idx > 0:
                    potential = _extract_product_words_before(words, label_idx)
                    if potential:
                        product_name = potential
                        product_from_current_question = True
            
            # Pattern B: "X herbicide/insecticide/termiticide/…"
            #             Uses the shared CATEGORY_WORDS set so ANY
            #             pesticide-type suffix is handled generically.
            if not product_name:
                for term in CATEGORY_WORDS:
                    if term in words:
                        term_idx = words.index(term)
                        if term_idx > 0:
                            potential = _extract_product_words_before(words, term_idx)
                            if potential:
                                product_name = potential
                                product_from_current_question = True
                                break
            
            # Pattern C: "rei for/of X", "what is X", "tell me about X"
            #             Uses _extract_product_words_after so all noise &
            #             category words are automatically filtered.
            if not product_name:
                for prep in ["for", "of", "about"]:
                    if prep in words:
                        prep_idx = words.index(prep)
                        potential = _extract_product_words_after(words, prep_idx)
                        if potential:
                            product_name = potential
                            product_from_current_question = True
                            break
        
        # ── Step 3: Broad extraction — filter out all known noise, take remainder
        is_pesticide_related = any(
            kw in question_lower for kw in (
                CATEGORY_WORDS | {
                    "label", "application rate", "safety", "mixing",
                    "chemical", "cdms", "rei", "re-entry", "reentry",
                    "spray", "concentrate", "formulation", "active ingredient",
                    "epa", "sds", "msds",
                }
            )
        )
        
        if not product_name and is_pesticide_related:
            filtered = [w for w in question_clean.split()
                        if w.lower() not in _EXTRACTION_NOISE]
            if filtered:
                product_name = " ".join(filtered[:4])
                product_from_current_question = True
        
        # ── Step 4: Conversation context (LAST resort) ──────────────────
        #    Only used when the current question contains NO product at all
        #    (e.g. bare follow-ups like "what about safety?").
        if not product_name and conversation_context:
            for msg in reversed(conversation_context):
                content = msg.get("content", "").lower()
                for keyword in KNOWN_PRODUCTS:
                    if keyword in content:
                        product_name = keyword
                        break
                if product_name:
                    break
        
        # ── Step 5: Final fallback ─────────────────────────────────────
        if not product_name:
            if is_pesticide_related:
                product_name = "pesticide"
            else:
                return {
                    "success": False,
                    "tool": "cdms_label",
                    "error": "Could not identify the pesticide product name. "
                             "Please specify a product (e.g., 'Find Roundup label')",
                    "should_fallback": True
                }
        
        print(f"🏷️  Extracted product_name = '{product_name}' "
              f"(from {'question' if product_from_current_question else 'context'})")
        
        # ── Create tool and prepare enhanced question ───────────────────
        tool = CDMSLabelTool()
        enhanced_question = question
        
        # Detect follow-up question types
        followup_keywords = {
            "safety": ["safety", "safe", "precaution", "hazard", "danger", "toxic", "poison", "warning", "protective"],
            "application": ["application", "apply", "rate", "dosage", "amount", "how much", "when to apply"],
            "mixing": ["mix", "mixing", "dilute", "dilution", "solution", "concentrate", "ratio"],
            "reentry": ["re-entry", "reentry", "rei", "when can i", "how long", "wait", "interval"],
            "storage": ["store", "storage", "keep", "shelf life", "expiration"],
            "crops": ["crop", "crops", "use on", "for", "suitable", "compatible"]
        }
        
        detected_type = None
        for ftype, fkeywords in followup_keywords.items():
            if any(kw in question_lower for kw in fkeywords):
                detected_type = ftype
                break
        
        # Follow-up enhancement — ONLY override product_name when the
        # current question truly has no product (context-only extraction).
        if conversation_context and not product_from_current_question:
            # This is a genuine follow-up (no product in current question).
            context_product = None
            for msg in reversed(conversation_context):
                msg_content = msg.get("content", "").lower()
                for keyword in KNOWN_PRODUCTS:
                    if keyword in msg_content:
                        context_product = keyword
                        break
                if context_product:
                    break
            if context_product and (not product_name or product_name == "pesticide"):
                product_name = context_product
        
        # Build enhanced question (append product + type for better RAG recall)
        if product_name and product_name != "pesticide":
            if detected_type:
                enhanced_question = f"{question} for {product_name} {detected_type}"
            # Only append "about product" if product isn't already in the question
            elif product_name.lower() not in question_lower:
                enhanced_question = f"{question} about {product_name}"
        elif detected_type:
            enhanced_question = f"{question} {detected_type}"
        
        print(f"📝 Enhanced question: {enhanced_question}")
        
        # Use full RAG pipeline: Tavily → Download → Process → Index → RAG Search
        result = tool.search_with_rag(
            product_name=product_name,
            user_question=enhanced_question,
            active_ingredient=active_ingredient
        )
        
        if not result.get("success"):
            return {
                "success": False,
                "tool": "cdms_label",
                "error": result.get("error", "CDMS RAG search failed")
            }
        
        # Return successful result with RAG chunks and page citations
        return {
            "success": True,
            "tool": "cdms_label",
            "data": result
        }
    
    except Exception as e:
        return {
            "success": False,
            "tool": "cdms_label",
            "error": f"Unexpected error: {str(e)}"
        }


# Test the tool
if __name__ == "__main__":
    print("=" * 80)
    print("Testing CDMS Label Tool with Citations")
    print("=" * 80)
    
    tool = CDMSLabelTool()
    
    # Test 1: Roundup (common product)
    print("\nTEST 1: Search for Roundup labels")
    print("-" * 80)
    
    result = tool.search(
        product_name="Roundup",
        active_ingredient="glyphosate",
        max_results=3
    )
    
    # Show formatted output
    print(tool.format_response_for_user(result))
    
    # Test 2: Sevin (another common product)
    print("\n" + "=" * 80)
    print("TEST 2: Search for Sevin labels")
    print("-" * 80)
    
    result = tool.search(
        product_name="Sevin",
        active_ingredient="carbaryl",
        max_results=3
    )
    
    print(tool.format_response_for_user(result))
    
    # Test 3: Just product name (no ingredient)
    print("\n" + "=" * 80)
    print("TEST 3: Search with product name only")
    print("-" * 80)
    
    result = tool.search(
        product_name="2,4-D",
        max_results=3
    )
    
    print(tool.format_response_for_user(result))
    
    print("\n" + "=" * 80)
    print("✅ All tests complete!")
    print("=" * 80)

