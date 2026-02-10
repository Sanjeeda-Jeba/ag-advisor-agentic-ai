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
from pathlib import Path


class CDMSLabelTool:
    """
    Tool for searching CDMS pesticide labels
    
    Uses Tavily with domain filtering (cdms.net) to find accurate label information
    with full citations and source URLs
    """
    
    def __init__(self):
        """Initialize the CDMS label search tool"""
        self.client = TavilyAPIClient()
        self.pdf_downloader = CDMSPDFDownloader()
        self.rag_search = CDMSRAGSearch()
        self.document_loader = DocumentLoader(pdf_folder="data/pdfs/cdms")
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
            "raw_tavily_results": raw_results  # Keep for PDF extraction
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
            from src.cdms.schema import Document, DatabaseManager
            db_manager = DatabaseManager()
            session = db_manager.get_session()
            
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
                                # We can't easily filter by document_id in Qdrant without searching,
                                # so we'll just check if collection has any points
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
        # Step 1: Tavily search for PDF URLs
        print(f"🔍 Step 1: Searching Tavily for '{product_name}' PDFs...")
        tavily_result = self.search(
            product_name=product_name,
            active_ingredient=active_ingredient,
            max_results=3
        )
        
        if not tavily_result.get("success"):
            error_msg = tavily_result.get("error", "Tavily search failed")
            print(f"❌ Tavily search failed: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "product_name": product_name
            }
        
        labels_found = tavily_result.get("label_count", 0)
        print(f"✅ Tavily search successful: Found {labels_found} label(s)")
        
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
                        pdf_url=pdf_url  # PHASE 1 FIX: Pass PDF URL to store in metadata
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
            "tavily_results": tavily_result,
            "download_info": download_result,
            "pdf_urls": list(filename_to_url.values()),  # All PDF URLs
            "tavily_labels": tavily_labels  # Include Tavily labels with URLs
        }


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
        # Simple parameter extraction
        # TODO: Could use NLP to better extract product names and ingredients
        # For now, we'll pass the whole question and let Tavily handle it
        
        # Try to extract product name (simple approach)
        # Common keywords to look for
        keywords = ["roundup", "sevin", "2,4-d", "glyphosate", "carbaryl", "atrazine"]
        
        product_name = None
        active_ingredient = None
        
        question_lower = question.lower()
        
        # Check for common product names in current question
        for keyword in keywords:
            if keyword in question_lower:
                product_name = keyword
                break
        
        # If no product found in current question, check conversation context
        if not product_name and conversation_context:
            # Look for product name in previous messages
            for msg in reversed(conversation_context):  # Start from most recent
                content = msg.get("content", "").lower()
                for keyword in keywords:
                    if keyword in content:
                        product_name = keyword
                        break
                if product_name:
                    break
        
        # If still no product found, try to extract from phrases like "label for X" or "X label"
        if not product_name:
            if "label for" in question_lower:
                parts = question_lower.split("label for")
                if len(parts) > 1:
                    product_name = parts[1].strip().split()[0] if parts[1].strip() else None
            elif "label" in question_lower:
                parts = question_lower.split("label")
                if parts[0].strip():
                    words = parts[0].strip().split()
                    if words:
                        product_name = words[-1]
        
        # If no product found, check if this is a pesticide-related question
        # If it is, we'll try CDMS anyway (might find something), otherwise it will fallback
        is_pesticide_related = any(
            kw in question_lower for kw in [
                "pesticide", "herbicide", "insecticide", "fungicide", "label",
                "application rate", "safety", "mixing", "chemical", "cdms"
            ]
        )
        
        # PHASE 2 FIX: Be more flexible - if tool matcher selected CDMS, trust it and try to search
        # Extract any potential product name from the question itself
        if not product_name:
            # Try to extract product name from common patterns
            # Pattern: "X label", "label for X", "X pesticide", etc.
            words = question_lower.split()
            
            # Look for word before "label"
            if "label" in words:
                label_idx = words.index("label")
                if label_idx > 0:
                    # Take words before "label" as potential product name (could be multiple words)
                    # Example: "Actagro 10% Boron label" -> "Actagro 10% Boron"
                    potential_product_parts = []
                    for i in range(label_idx - 1, -1, -1):  # Go backwards from label
                        word = words[i]
                        if word in ["the", "a", "an", "find", "get", "show", "search", "for", "of"]:
                            break
                        potential_product_parts.insert(0, word)
                        if len(potential_product_parts) >= 4:  # Limit to 4 words max
                            break
                    if potential_product_parts:
                        product_name = " ".join(potential_product_parts)
            
            # Look for word before "pesticide", "herbicide", etc.
            if not product_name:
                for term in ["pesticide", "herbicide", "insecticide", "fungicide"]:
                    if term in words:
                        term_idx = words.index(term)
                        if term_idx > 0:
                            # Take words before the term
                            potential_product_parts = []
                            for i in range(term_idx - 1, -1, -1):
                                word = words[i]
                                if word in ["the", "a", "an", "find", "get", "show", "search", "for", "of"]:
                                    break
                                potential_product_parts.insert(0, word)
                                if len(potential_product_parts) >= 4:
                                    break
                            if potential_product_parts:
                                product_name = " ".join(potential_product_parts)
                                break
        
        # If still no product but pesticide-related, try with the question itself or generic term
        if not product_name:
            if is_pesticide_related:
                # Use first few words of question as product name, or generic "pesticide"
                # This allows CDMS to search even without specific product name
                # IMPROVED: Handle multi-word product names like "Actagro 10% Boron"
                words = question.split()  # Use original case to preserve special chars like "10%"
                # Filter out common question words
                filtered_words = [w for w in words if w.lower() not in ["what", "how", "tell", "me", "about", "find", "get", "show", "search", "for", "the", "a", "an", "label", "pesticide", "herbicide"]]
                if filtered_words:
                    # Take up to 4 words for product name (handles "Actagro 10% Boron")
                    product_name = " ".join(filtered_words[:4])
                else:
                    product_name = "pesticide"  # Generic fallback
            else:
                # Not pesticide-related and no product - return error (will trigger fallback)
                return {
                    "success": False,
                    "tool": "cdms_label",
                    "error": "Could not identify the pesticide product name. Please specify a product (e.g., 'Find Roundup label')",
                    "should_fallback": True  # Flag for fallback
                }
        
        # Create tool and run full RAG pipeline
        tool = CDMSLabelTool()
        
        # Enhance question with context if this is a follow-up
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
        
        # If this looks like a follow-up question, enhance with context
        is_followup = (
            conversation_context and (
                # No product name in current question but has context
                (not product_name or product_name == "pesticide") or
                # Question is vague/short
                len(question.split()) <= 5 or
                # Detected follow-up type
                detected_type is not None or
                # Common follow-up phrases
                any(phrase in question_lower for phrase in [
                    "what about", "how about", "tell me more", "and", "also", "what's the"
                ])
            )
        )
        
        if is_followup:
            # Find the most recent mention of the product in context
            context_product = None
            for msg in reversed(conversation_context):
                msg_content = msg.get("content", "").lower()
                # Check for product names in previous messages
                for keyword in keywords:
                    if keyword in msg_content:
                        context_product = keyword
                        break
                if context_product:
                    break
            
            # If we found a product in context, use it
            if context_product and (not product_name or product_name == "pesticide"):
                product_name = context_product
            
            # Enhance question with product context and follow-up type
            if product_name and product_name != "pesticide":
                if detected_type:
                    # Add specific context based on follow-up type
                    enhanced_question = f"{question} for {product_name} {detected_type}"
                else:
                    enhanced_question = f"{question} about {product_name}"
            elif detected_type:
                # Add follow-up type context
                enhanced_question = f"{question} {detected_type}"
        
        # Use full RAG pipeline: Tavily → Download → Process → Index → RAG Search
        result = tool.search_with_rag(
            product_name=product_name,
            user_question=enhanced_question,  # Pass enhanced question for RAG search
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

