"""
Document Loader
Scans PDF folder, processes PDFs, and stores in database + Qdrant
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import List, Dict
from datetime import datetime
from src.cdms.pdf_processor import PDFProcessor
from src.cdms.schema import DatabaseManager, Document, DocumentChunk
from src.rag.embeddings import OpenAIEmbeddingService
from src.rag.vector_store import QdrantVectorStore
from src.config.credentials import CredentialsManager


class DocumentLoader:
    """
    Loads and indexes PDF documents for RAG
    
    Usage:
        loader = DocumentLoader()
        loader.load_all_pdfs()  # Process all PDFs in data/pdfs/
    """
    
    def __init__(self, pdf_folder: str = "data/pdfs"):
        """
        Initialize document loader
        
        Args:
            pdf_folder: Folder containing PDF files
        """
        self.pdf_folder = Path(pdf_folder)
        self.pdf_folder.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.pdf_processor = PDFProcessor()
        self.db_manager = DatabaseManager()
        
        # Initialize embedding service (will load OpenAI key)
        try:
            creds = CredentialsManager()
            openai_key = creds.get_api_key("openai")
            self.embedding_service = OpenAIEmbeddingService(api_key=openai_key)
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize OpenAI embeddings: {e}")
            self.embedding_service = None
        
        # Initialize vector store
        try:
            self.vector_store = QdrantVectorStore()
            # Verify vector store is working
            if hasattr(self.vector_store, 'client'):
                print(f"✅ Vector store initialized successfully")
            else:
                print(f"⚠️  Warning: Vector store initialized but client is missing")
                self.vector_store = None
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize Qdrant: {e}")
            import traceback
            traceback.print_exc()
            self.vector_store = None
    
    def load_pdf(self, pdf_path: str, force_reprocess: bool = False, pdf_url: str = None) -> Dict:
        """
        Load a single PDF file
        
        Args:
            pdf_path: Path to PDF file
            force_reprocess: If True, reprocess even if already indexed
            pdf_url: Optional original PDF URL (for CDMS labels from Tavily)
        
        Returns:
            Dict with processing result
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            return {
                "success": False,
                "error": f"File not found: {pdf_path}"
            }
        
        # Check if already processed
        session = self.db_manager.get_session()
        try:
            doc_id = Document.generate_id(str(pdf_path))
            existing_doc = session.query(Document).filter_by(id=doc_id).first()
            
            if existing_doc and existing_doc.processed == 1 and not force_reprocess:
                # Verify chunks actually exist in Qdrant before skipping
                chunks_in_qdrant = 0
                if self.vector_store:
                    try:
                        # Check if collection exists and has points
                        if self.vector_store.client.collection_exists("cdms_documents"):
                            collection_info = self.vector_store.client.get_collection("cdms_documents")
                            chunks_in_qdrant = collection_info.points_count
                    except Exception as e:
                        print(f"⚠️  Warning: Could not verify Qdrant chunks: {e}")
                
                if chunks_in_qdrant == 0:
                    print(f"⚠️  Warning: PDF {pdf_path.name} marked as processed but no chunks in Qdrant. Reprocessing...")
                    force_reprocess = True
                else:
                    return {
                        "success": True,
                        "message": f"PDF already processed: {pdf_path.name}",
                        "document_id": doc_id,
                        "skipped": True,
                        "chunks_in_qdrant": chunks_in_qdrant
                    }
            
            # If force reprocess, delete old chunks and document
            if force_reprocess and existing_doc:
                # Delete old chunks
                session.query(DocumentChunk).filter_by(document_id=doc_id).delete()
                # Delete old document
                session.delete(existing_doc)
                session.commit()
                print(f"🔄 Re-processing: {pdf_path.name}")
            
            # Process PDF
            print(f"📄 Processing: {pdf_path.name}")
            result = self.pdf_processor.process_pdf(str(pdf_path))
            
            if not result.get("success"):
                return result
            
            # Store in database
            doc = Document(
                id=doc_id,
                filename=pdf_path.name,
                filepath=str(pdf_path),
                file_size=pdf_path.stat().st_size,
                num_pages=result["num_pages"],
                num_chunks=result["num_chunks"],
                processed=1,
                last_processed=datetime.utcnow()
            )
            
            session.merge(doc)
            
            # Store chunks with accurate page numbers
            chunks_stored = 0
            embeddings_generated = 0
            
            chunks = result.get("chunks", [])
            page_numbers = result.get("page_numbers", [])
            
            # PHASE 2 FIX: Validate page numbers with warnings
            if not page_numbers:
                print(f"⚠️  Warning: No page numbers provided for {pdf_path.name}, estimating...")
                page_numbers = [(idx // 3) + 1 for idx in range(len(chunks))]
            elif len(page_numbers) != len(chunks):
                print(f"⚠️  Warning: Page numbers count ({len(page_numbers)}) doesn't match chunks count ({len(chunks)}) for {pdf_path.name}")
                # Fix by padding or truncating to match
                if len(page_numbers) < len(chunks):
                    last_page = page_numbers[-1] if page_numbers else 1
                    page_numbers.extend([last_page] * (len(chunks) - len(page_numbers)))
                else:
                    page_numbers = page_numbers[:len(chunks)]
            
            for idx, (chunk_text, page_num) in enumerate(zip(chunks, page_numbers)):
                # PHASE 2 FIX: Validate page number is positive
                if page_num <= 0:
                    print(f"⚠️  Warning: Invalid page number {page_num} for chunk {idx} in {pdf_path.name}, using estimated value")
                    # Estimate page number based on chunk index
                    page_num = (idx // 3) + 1
                    page_numbers[idx] = page_num
                chunk_id = DocumentChunk.generate_id(doc_id, idx)
                
                # Calculate token count (rough estimate: 1 token ≈ 4 chars)
                token_count = len(chunk_text) // 4
                
                chunk = DocumentChunk(
                    id=chunk_id,
                    document_id=doc_id,
                    chunk_index=idx,
                    content=chunk_text,
                    page_number=page_num,  # ENHANCED: Accurate page number from PDF processor
                    char_count=len(chunk_text),
                    token_count=token_count
                )
                
                session.merge(chunk)
                
                # Generate embedding and store in Qdrant
                if self.embedding_service and self.vector_store:
                    try:
                        embedding = self.embedding_service.generate_embedding(chunk_text)
                        
                        # Validate embedding was generated
                        if not embedding:
                            print(f"⚠️  Warning: Failed to generate embedding for chunk {idx} in {pdf_path.name}")
                        elif len(embedding) != 1536:
                            print(f"⚠️  Warning: Invalid embedding dimension {len(embedding)} for chunk {idx} in {pdf_path.name}")
                        else:
                            # PHASE 1 FIX: Generate URL hash for matching
                            url_hash = ""
                            if pdf_url:
                                import hashlib
                                url_hash = hashlib.md5(pdf_url.encode()).hexdigest()[:12]
                            
                            metadata = {
                                "document_id": doc_id,
                                "document_name": pdf_path.name,
                                "chunk_index": idx,
                                "content": chunk_text,  # Store full content for search
                                "page_number": page_num,  # ENHANCED: Accurate page number
                                "source_file": pdf_path.name,
                                "pdf_url": pdf_url if pdf_url else "",  # PHASE 1 FIX: Store PDF URL in metadata
                                "url_hash": url_hash  # PHASE 1 FIX: Store URL hash for reliable matching
                            }
                            
                            success = self.vector_store.add_document_chunk(
                                chunk_id=chunk_id,
                                embedding=embedding,
                                metadata=metadata
                            )
                            if success:
                                embeddings_generated += 1
                            else:
                                print(f"⚠️  Warning: Failed to store chunk {idx} in Qdrant for {pdf_path.name}")
                    except Exception as e:
                        print(f"⚠️  Warning: Could not generate embedding for chunk {idx}: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    # Log why embeddings aren't being generated
                    if not self.embedding_service:
                        print(f"⚠️  Warning: Embedding service not available, skipping embeddings for chunk {idx}")
                    if not self.vector_store:
                        print(f"⚠️  Warning: Vector store not available, skipping embeddings for chunk {idx}")
                
                chunks_stored += 1
            
            session.commit()
            
            # Log summary
            print(f"   ✅ Stored {chunks_stored} chunks, {embeddings_generated} embeddings generated")
            if chunks_stored > 0 and embeddings_generated == 0:
                print(f"   ⚠️  Warning: No embeddings were generated! Check embedding service and vector store initialization.")
            
            return {
                "success": True,
                "document_id": doc_id,
                "filename": pdf_path.name,
                "chunks_stored": chunks_stored,
                "embeddings_generated": embeddings_generated,
                "num_pages": result["num_pages"]
            }
        
        finally:
            session.close()
    
    def load_all_pdfs(self, force_reprocess: bool = False) -> Dict:
        """
        Load all PDFs from the pdf_folder
        
        Returns:
            Dict with summary of processing
        """
        if not self.pdf_folder.exists():
            return {
                "success": False,
                "error": f"PDF folder not found: {self.pdf_folder}"
            }
        
        pdf_files = list(self.pdf_folder.glob("*.pdf"))
        
        if not pdf_files:
            return {
                "success": False,
                "error": f"No PDF files found in {self.pdf_folder}"
            }
        
        print(f"📚 Found {len(pdf_files)} PDF file(s)")
        print("-" * 70)
        
        results = []
        for pdf_file in pdf_files:
            result = self.load_pdf(str(pdf_file), force_reprocess=force_reprocess)
            results.append(result)
            if result.get("success") and not result.get("skipped"):
                print(f"✅ {pdf_file.name}: {result.get('chunks_stored', 0)} chunks, {result.get('embeddings_generated', 0)} embeddings")
            elif result.get("skipped"):
                print(f"⏭️  {pdf_file.name}: Already processed (skipped)")
            print()
        
        # Summary
        successful = sum(1 for r in results if r.get("success"))
        total_chunks = sum(r.get("chunks_stored", 0) for r in results)
        total_embeddings = sum(r.get("embeddings_generated", 0) for r in results)
        
        return {
            "success": True,
            "total_files": len(pdf_files),
            "successful": successful,
            "total_chunks": total_chunks,
            "total_embeddings": total_embeddings,
            "results": results
        }


# Test function
if __name__ == "__main__":
    print("Testing Document Loader...")
    print("=" * 70)
    
    loader = DocumentLoader()
    
    # Load all PDFs
    result = loader.load_all_pdfs()
    
    if result.get("success"):
        print("\n" + "=" * 70)
        print("✅ Processing Complete!")
        print(f"   Files processed: {result['successful']}/{result['total_files']}")
        print(f"   Total chunks: {result['total_chunks']}")
        print(f"   Embeddings generated: {result['total_embeddings']}")
    else:
        print(f"\n❌ Error: {result.get('error')}")
        print("\n💡 To use:")
        print("   1. Create data/pdfs/ folder")
        print("   2. Add PDF files")
        print("   3. Make sure OPENAI_API_KEY is in .env")
        print("   4. Make sure Qdrant is running (Docker)")

