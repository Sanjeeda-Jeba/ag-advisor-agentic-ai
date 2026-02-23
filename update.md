# Project Updates

## Qdrant API Fix
- Replaced deprecated `self.client.search()` with `self.client.query_points()` in `src/rag/vector_store.py`
- Changed parameter `query_vector` → `query`
- Fixed response parsing to access `response.points`

## PDF Processing & Chunking Fixes (`src/cdms/document_loader.py`)
- Fixed multiple indentation errors causing `SyntaxError: expected 'except' or 'finally' block`
- Added chunk verification — checks if a PDF marked as processed actually has chunks in Qdrant; forces reprocessing if not
- Added embedding validation (dimension check, None/empty guard)
- Wrapped chunk-processing loop in `session.no_autoflush` to prevent `IntegrityError` from premature INSERT
- Added `session.rollback()` in `except` block for cleaner error recovery
- Added detailed logging for chunks stored, embeddings generated, and service availability warnings

## RAG Search Improvements (`src/cdms/rag_search.py`)
- Lowered `score_threshold` by 20% when filtering by product name to get more candidates
- Increased `search_limit` multiplier from 2× to 3× when filtering by product
- Enhanced product matching — checks first 200 chars of chunk content in addition to filename
- Added fallback: if product filter removes all results, returns unfiltered results instead of empty

## Multi-Domain Label Search (`src/api_clients/tavily_client.py`)
- Implemented fallback chain: `cdms.net` → `greenbook.net` → `epa.gov`
- Added `_process_and_validate_results` helper to filter out irrelevant search results by checking title, content, and URL against product name
- Strips `®`, `™`, `©` from product names before searching
- Returns `source` and `sources_tried` metadata in results

## LLM Response Guardrails (`src/tools/llm_response_generator.py`)
- Updated `_generate_cdms_tavily_response` prompt to forbid inventing product descriptions or safety info when no labels are found
- Updated `_generate_cdms_rag_response` to reference "official label databases" instead of just "CDMS"
- Added specific response formats for labels-found vs. no-labels-found scenarios

## CDMS Label Tool Enhancements (`src/tools/cdms_label_tool.py`)
- Strips `®`, `™`, `©` from product names during extraction
- `_is_pdf_indexed()` reuses `self.document_loader.db_manager` instead of creating a new `DatabaseManager()` to prevent SQLite lock contention
- `search_with_rag()` now returns Tavily `summary`, `labels`, `citations` at top level so the LLM response generator can use them when RAG chunks are empty
- Passes `source` and `sources_tried` through from Tavily results

## Streamlit UI Fix (`src/streamlit_app_conversational.py`)
- Replaced custom HTML rendering (`st.markdown` with `unsafe_allow_html=True`) with native `st.chat_message("user")` and `st.chat_message("assistant")` — fixes bold, links, and other markdown not rendering
- Metadata badges now use `st.caption()` inside chat bubbles
- Removed unused CSS classes (`.user-message`, `.assistant-message`, `.tool-badge`, etc.)

## SQLite Concurrency Fixes (`src/cdms/schema.py`)
- Added `timeout=30` to SQLite connection (up from 5s default)
- Enabled WAL journal mode (`PRAGMA journal_mode=WAL`) for better read/write concurrency
- Added `PRAGMA busy_timeout=30000` as backup timeout
- Added `pool_pre_ping=True` for connection health checks

## Persistent Vector DB & Singleton Pattern
- **`src/rag/vector_store.py`**: Reads `QDRANT_HOST` / `QDRANT_PORT` from env vars (for Docker/EC2). Falls back to persistent local disk (`data/qdrant_storage/`) instead of `:memory:`. Never uses in-memory mode.
- **`src/cdms/document_loader.py`**: Accepts optional `vector_store` param for dependency injection
- **`src/cdms/rag_search.py`**: Accepts optional `vector_store` param for dependency injection
- **`src/rag/hybrid_retriever.py`**: Accepts optional `vector_store` param for dependency injection
- **`src/tools/cdms_label_tool.py`**: Creates one shared `QdrantVectorStore` and passes it to both `DocumentLoader` and `CDMSRAGSearch` — chunks written by loader are immediately visible to search

## Larger Chunks for Better RAG Recall (`src/cdms/pdf_processor.py`)
- Increased default `chunk_size` from 1000 → 2000 characters and `chunk_overlap` from 200 → 300
- Larger chunks keep related label sections (e.g., REI, directions, restrictions) together, improving search hit quality

## REI Keyword-Boosted Search (`src/cdms/rag_search.py`)
- When the user asks about REI / re-entry interval but no returned chunks contain REI text, a targeted follow-up search is fired using REI-specific language ("re-entry interval restricted entry agricultural use requirements")
- Chunks from the follow-up that contain REI keywords are merged into the results and deduplicated

## Docker Compose (`docker-compose.yml`)
- Added `app_data:/app/data` volume mount for SQLite, cached PDFs, and local Qdrant fallback persistence
- Added `restart: unless-stopped` to both `qdrant` and `app` services
