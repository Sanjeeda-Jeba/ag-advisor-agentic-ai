"""
LLM Response Generator
Converts tool execution results into natural language responses using any configured LLM
(OpenAI, Anthropic Claude, Google Gemini)
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Dict, Any, List
from src.llm.factory import get_llm_client
from src.config.llm_settings import is_llm_response_enabled


def _parse_cdms_max_output_tokens() -> int:
    """
    Max completion tokens for CDMS label answers (RAG + Tavily paths).
    Override with LLM_MAX_OUTPUT_TOKENS_CDMS (e.g. 4096 for long comparisons).
    """
    raw = os.getenv("LLM_MAX_OUTPUT_TOKENS_CDMS", "4096")
    try:
        n = int(str(raw).strip())
    except ValueError:
        n = 4096
    # Keep within sensible bounds for typical chat models
    return max(512, min(n, 32768))


class LLMResponseGenerator:
    """
    Generates natural language responses from tool results using LLM

    This is the FINAL step in the pipeline:
    User Question → Tool Selection → Tool Execution → LLM Response → User

    Uses provider-agnostic LLM layer. Configure via env vars:
        LLM_PROVIDER: openai | anthropic | google
        LLM_MODEL: model name (e.g., gpt-4o, claude-sonnet-4-6, gemini-2.0-flash)
        LLM_MAX_OUTPUT_TOKENS_CDMS: max completion tokens for CDMS answers (default 4096)
        LLM_ENABLED / LLM_RESPONSE_ENABLED: disable LLM and show raw tool output (see src/config/llm_settings.py)
    """

    def __init__(self, provider: str = None, model: str = None, api_key: str = None):
        """
        Initialize LLM Response Generator

        Args:
            provider: LLM provider (openai, anthropic, google). Default: LLM_PROVIDER env or openai
            model: Model name. Default: LLM_MODEL or OPENAI_MODEL_NAME env or gpt-4o-mini
            api_key: API key for the provider (optional, loads from env if not provided)
        """
        self._llm = None
        self._provider = provider
        self._model = model
        self._api_key = api_key
        self.cdms_max_output_tokens = _parse_cdms_max_output_tokens()

    @property
    def llm(self):
        """Lazy LLM client — not created when only deterministic responses are used."""
        if self._llm is None:
            self._llm = get_llm_client(
                provider=self._provider,
                model=self._model,
                api_key=self._api_key,
                purpose="response_generation",
            )
        return self._llm
    
    def generate_response(
        self,
        user_question: str,
        tool_name: str,
        tool_result: Dict[str, Any],
        conversation_context: list = None
    ) -> str:
        """
        Generate natural language response from tool result
        
        Args:
            user_question: Original user question
            tool_name: Name of the tool that was used
            tool_result: Result from tool execution
            conversation_context: Optional list of previous messages for context
        
        Returns:
            Natural language response string
        
        Example:
            >>> generator = LLMResponseGenerator()
            >>> result = {
            ...     "city": "London",
            ...     "temperature": 15,
            ...     "description": "partly cloudy"
            ... }
            >>> response = generator.generate_response(
            ...     "What's the weather in London?",
            ...     "weather",
            ...     result
            ... )
            >>> print(response)
            "The weather in London is currently 15°C with partly cloudy skies..."
        """
        if not is_llm_response_enabled():
            return self._format_deterministic_response(
                user_question, tool_name, tool_result, conversation_context
            )

        # Route to appropriate formatter (pass context)
        if tool_name == "weather":
            return self._generate_weather_response(user_question, tool_result, conversation_context)
        elif tool_name == "soil":
            return self._generate_soil_response(user_question, tool_result, conversation_context)
        elif tool_name == "rag" or tool_name == "documentation":
            # RAG tool is now CDMS - use CDMS response generator
            return self._generate_cdms_response(user_question, tool_result, conversation_context)
        elif tool_name in ["cdms_label", "cdms", "pesticide_label"]:
            return self._generate_cdms_response(user_question, tool_result, conversation_context)
        elif tool_name in ["agriculture_web", "ag_web"]:
            return self._generate_agriculture_web_response(user_question, tool_result, conversation_context)
        else:
            return self._generate_generic_response(user_question, tool_result, conversation_context)

    def _format_deterministic_response(
        self,
        user_question: str,
        tool_name: str,
        tool_result: Dict[str, Any],
        conversation_context: list = None,
    ) -> str:
        """
        When LLM is disabled: return readable markdown from tool payloads (no API calls).
        """
        header = (
            "**LLM response formatting is off** "
            "(`LLM_ENABLED=false` or `LLM_RESPONSE_ENABLED=false`). "
            "Structured tool output:\n\n---\n\n"
        )

        if tool_name == "weather":
            return header + self._format_deterministic_weather(user_question, tool_result)
        if tool_name == "soil":
            return header + self._format_deterministic_soil(user_question, tool_result)
        if tool_name in (
            "rag",
            "documentation",
            "cdms_label",
            "cdms",
            "pesticide_label",
        ):
            data = tool_result or {}
            rag_chunks = data.get("rag_chunks", [])
            if data.get("searched_index_only") and not rag_chunks:
                return header + self._generate_cdms_index_only_no_match_response(
                    user_question, data
                )
            return header + self._format_deterministic_cdms(user_question, data)
        if tool_name in ("agriculture_web", "ag_web"):
            return header + self._format_deterministic_ag_web(user_question, tool_result)
        return header + self._format_deterministic_generic(user_question, tool_result)

    def _format_deterministic_weather(self, user_question: str, data: Dict[str, Any]) -> str:
        return (
            f"**Your question:** {user_question}\n\n"
            f"**Location:** {data.get('city', 'Unknown')}, {data.get('country', '')}\n"
            f"- **Temperature:** {data.get('temperature', 'N/A')} °C\n"
            f"- **Feels like:** {data.get('feels_like', 'N/A')} °C\n"
            f"- **Conditions:** {data.get('description', 'N/A')}\n"
            f"- **Humidity:** {data.get('humidity', 'N/A')} %\n"
            f"- **Wind:** {data.get('wind_speed', 'N/A')} m/s\n"
        )

    def _format_deterministic_soil(self, user_question: str, data: Dict[str, Any]) -> str:
        lines = [f"**Your question:** {user_question}\n"]
        loc = data.get("location") or {}
        lines.append(
            f"**Location:** ({loc.get('lat', 'N/A')}, {loc.get('lon', 'N/A')})\n"
        )
        props = data.get("properties") or {}
        if not props:
            lines.append("\n*(No soil properties in result.)*")
            return "\n".join(lines)
        lines.append("\n**Soil properties:**\n")
        for name, p in props.items():
            if isinstance(p, dict):
                label = p.get("label", name)
                val = p.get("value", "N/A")
                unit = p.get("unit", "")
                lines.append(f"- **{label}:** {val} {unit}".strip())
            else:
                lines.append(f"- **{name}:** {p}")
        return "\n".join(lines)

    def _format_deterministic_cdms(self, user_question: str, data: Dict[str, Any]) -> str:
        product = data.get("product_name", "Unknown product")
        lines = [
            f"**Your question:** {user_question}\n",
            f"**Product:** {product}\n",
            f"**Chunks retrieved:** {data.get('total_chunks_found', 0)}\n",
        ]
        summary = data.get("summary")
        if summary:
            lines.append(f"\n**Search summary:**\n{summary}\n")

        rag_chunks: List[Dict[str, Any]] = data.get("rag_chunks") or []
        if rag_chunks:
            lines.append("\n**Label excerpts (from index):**\n")
            for i, ch in enumerate(rag_chunks[:12], 1):
                page = ch.get("page_number", "?")
                title = ch.get("source_file", "document")
                url = ch.get("pdf_url", "")
                body = (ch.get("content") or "")[:900]
                cite = f"Page {page} — {title}"
                if url:
                    cite += f" — [{url}]({url})"
                lines.append(f"\n*{i}. {cite}*\n{body}")
                if len(body) >= 900:
                    lines.append("…")

        labels = data.get("tavily_labels") or data.get("labels") or []
        if labels:
            lines.append("\n**Labels / links:**\n")
            for lab in labels[:15]:
                t = lab.get("title", "Label")
                u = lab.get("url", "")
                if u:
                    lines.append(f"- [{t}]({u})")
                else:
                    lines.append(f"- {t}")

        pdf_urls = data.get("pdf_urls") or []
        if pdf_urls:
            lines.append("\n**PDF URLs:**\n")
            for u in pdf_urls:
                lines.append(f"- [{u}]({u})")

        if not rag_chunks and not labels and not pdf_urls:
            lines.append(
                "\n*(No indexed excerpts or label links in this result. "
                "Check tool logs or enable LLM for a natural-language summary.)*"
            )
        return "\n".join(lines)

    def _format_deterministic_ag_web(self, user_question: str, data: Dict[str, Any]) -> str:
        lines = [
            f"**Your question:** {user_question}\n",
            f"**Query used:** {data.get('query', user_question)}\n\n",
        ]
        ans = data.get("answer") or data.get("summary")
        if ans:
            lines.append(f"**Tavily answer:**\n{ans}\n\n")
        sources = data.get("sources") or []
        if sources:
            lines.append("**Sources:**\n")
            for s in sources[:12]:
                title = s.get("title", "Source")
                url = s.get("url", "")
                snip = (s.get("snippet") or "")[:300]
                if url:
                    lines.append(f"- [{title}]({url})")
                else:
                    lines.append(f"- {title}")
                if snip:
                    lines.append(f"  _{snip}…_" if len(snip) >= 300 else f"  _{snip}_")
        citations = data.get("citations")
        if citations:
            lines.append(f"\n**Citations:**\n{citations}\n")
        if not ans and not sources:
            lines.append("*(No answer text or sources in tool result.)*")
        return "\n".join(lines)

    def _format_deterministic_generic(self, user_question: str, data: Dict[str, Any]) -> str:
        import json

        try:
            blob = json.dumps(data, indent=2, default=str)[:6000]
        except Exception:
            blob = str(data)[:6000]
        return f"**Your question:** {user_question}\n\n```json\n{blob}\n```\n"
    
    def _generate_weather_response(self, user_question: str, data: Dict, conversation_context: list = None) -> str:
        """Generate natural language response for weather data
        
        IMPORTANT: Only uses weather data. Does NOT call soil or RAG tools.
        """
        
        # Build context from weather data ONLY
        context = f"""
User asked: "{user_question}"

Weather data retrieved:
- Location: {data.get('city', 'Unknown')}, {data.get('country', '')}
- Temperature: {data.get('temperature', 'N/A')}°C
- Feels like: {data.get('feels_like', 'N/A')}°C
- Conditions: {data.get('description', 'N/A')}
- Humidity: {data.get('humidity', 'N/A')}%
- Wind speed: {data.get('wind_speed', 'N/A')} m/s
"""
        
        # Create prompt for LLM - ONLY weather data
        prompt = f"""You are a helpful weather assistant. Generate a natural, conversational response based ONLY on the weather data provided below.

{context}

Requirements:
1. Answer directly and conversationally using ONLY the weather data above
2. Include relevant weather details from the data
3. Add a helpful suggestion if appropriate (e.g., "Bring an umbrella" if rainy)
4. Keep it concise (2-3 sentences)
5. Do NOT mention soil data or documentation (those are separate tools)
6. Use weather emoji if it enhances the message
7. Be friendly and helpful

Generate the response:"""
        
        return self.llm.chat(
            messages=[
                {"role": "system", "content": "You are a helpful weather assistant that provides clear, friendly weather information."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
    
    def _generate_soil_response(self, user_question: str, data: Dict, conversation_context: list = None) -> str:
        """Generate natural language response for soil data
        
        IMPORTANT: Only uses soil data. Does NOT call weather or RAG tools.
        """
        
        properties = data.get('properties', {})
        location = data.get('location', {})
        
        # Build context from soil data ONLY
        context = f"""
User asked: "{user_question}"

Soil data retrieved for location ({location.get('lat', 'N/A')}, {location.get('lon', 'N/A')}):
"""
        
        for prop_name, prop_data in properties.items():
            if isinstance(prop_data, dict):
                value = prop_data.get('value', 'N/A')
                unit = prop_data.get('unit', '')
                label = prop_data.get('label', prop_name)
                context += f"- {label}: {value} {unit}\n"
        
        # Create prompt for LLM - ONLY soil data
        prompt = f"""You are a helpful agricultural advisor. Generate a natural, informative response based ONLY on the soil data provided below.

{context}

Requirements:
1. Explain the soil properties in simple terms using ONLY the data above
2. Mention what the data means for agriculture/gardening
3. Be clear and educational
4. Keep it conversational (2-4 sentences)
5. Do NOT mention weather data or documentation (those are separate tools)
6. Add practical advice if relevant

Generate the response:"""
        
        return self.llm.chat(
            messages=[
                {"role": "system", "content": "You are a helpful agricultural advisor that explains soil data clearly."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=250
        )
    
    def _generate_rag_response(self, user_question: str, data: Dict, conversation_context: list = None) -> str:
        """Generate natural language response for RAG results
        
        IMPORTANT: Only uses information from the RAG tool (PDFs about agriculture/pesticides).
        Does NOT call weather or soil tools.
        """
        
        api_matches = data.get('api_matches', [])
        doc_context = data.get('document_context', [])
        
        # Build context - ONLY from RAG search results (agriculture/pesticides content)
        context = f"""
User asked: "{user_question}"

Information found from agriculture knowledge base (CDMS labels about pesticides, insecticides, farming):
"""
        
        # Add API catalog matches (from fuzzy matching - might find agriculture-related APIs)
        if api_matches:
            context += "\nRelevant items from catalog:\n"
            for api in api_matches[:3]:
                context += f"- {api.get('api_name', 'N/A')}: {api.get('description', 'N/A')}\n"
        
        # Add PDF document excerpts (from vector search - agriculture/pesticides content)
        if doc_context:
            context += "\nRelevant information from documentation:\n"
            for doc in doc_context[:2]:
                content_preview = doc.get('content', '')[:400]  # First 400 chars for agriculture content
                context += f"- From {doc.get('source_file', 'document')} (Page {doc.get('page_number', 'N/A')}): {content_preview}...\n"
        
        # If no results found
        if not api_matches and not doc_context:
            context += "\nNo relevant information found in the knowledge base about agriculture, pesticides, or insecticides."
            context += "\n\nIMPORTANT: The user may need to process PDFs first by running: python src/cdms/document_loader.py"
        
        # Create prompt for LLM - agriculture/pesticides focus
        prompt = f"""You are a helpful agricultural advisor. Answer the user's question about agriculture, pesticides, insecticides, or farming based ONLY on the information provided below.

{context}

IMPORTANT:
- Only use information from the documentation provided above (CDMS labels about pesticides/agriculture)
- Do NOT make up information
- Do NOT reference weather or soil data (those are separate tools)
- Focus on agriculture, pesticides, insecticides, farming practices
- If the documentation doesn't contain the answer, say so clearly
- Cite sources when relevant (mention document name and page)
- Be clear, educational, and helpful (3-5 sentences)

Generate the response:"""
        
        return self.llm.chat(
            messages=[
                {"role": "system", "content": "You are a helpful agricultural advisor. You answer questions about agriculture, pesticides, insecticides, and farming based on provided documentation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
    
    def _generate_cdms_response(self, user_question: str, data: Dict, conversation_context: list = None) -> str:
        """
        Generate natural language response for CDMS label search results
        
        Handles both old format (Tavily-only) and new format (RAG pipeline with page citations)
        """
        # Check if this is the new RAG pipeline format
        rag_chunks = data.get('rag_chunks', [])
        if data.get("searched_index_only") and not rag_chunks:
            return self._generate_cdms_index_only_no_match_response(user_question, data)
        
        if rag_chunks:
            # New RAG pipeline format - use page citations
            return self._generate_cdms_rag_response(user_question, data, conversation_context)
        else:
            # Old format - Tavily-only search
            return self._generate_cdms_tavily_response(user_question, data, conversation_context)

    def _generate_cdms_index_only_no_match_response(self, user_question: str, data: Dict) -> str:
        """Deterministic response when a same-product follow-up finds nothing in indexed PDFs."""
        product_name = data.get("product_name", "this product")
        labels = data.get("labels", [])
        download_info = data.get("download_info", {})
        pdf_urls = list(data.get("pdf_urls", []))

        url_to_title = {}
        for label in labels:
            url = label.get("url", "")
            title = label.get("title", "")
            if url and title:
                url_to_title[url] = title

        for pdf_info in download_info.get("downloaded_pdfs", []):
            url = pdf_info.get("url", "")
            filename = pdf_info.get("filename", "")
            if url and url not in url_to_title:
                url_to_title[url] = filename.replace(".pdf", "").replace("_", " ").title()
            if url and url not in pdf_urls:
                pdf_urls.append(url)

        if pdf_urls:
            links = "\n".join(
                f"- [{url_to_title.get(url, 'Label PDF')}]({url})"
                for url in pdf_urls
            )
            return (
                f"I searched the indexed **{product_name}** label PDFs for your follow-up question, "
                f"but I could not find explicit information about that in the retrieved excerpts.\n\n"
                f"**📄 PDF Downloads:**\n{links}"
            )

        return (
            f"I searched the indexed **{product_name}** label PDFs for your follow-up question, "
            f"but I could not find explicit information about that in the retrieved excerpts."
        )
    
    def _generate_cdms_rag_response(self, user_question: str, data: Dict, conversation_context: list = None) -> str:
        """
        Generate response from RAG chunks with page citations and PDF links
        
        NEW: Uses RAG search results with exact page numbers and PDF download URLs
        """
        product_name = data.get('product_name', 'Unknown product')
        rag_chunks = data.get('rag_chunks', [])
        pdfs_downloaded = data.get('pdfs_downloaded', 0)
        total_chunks = data.get('total_chunks_found', 0)
        tavily_labels = data.get('tavily_labels', [])
        
        # Detect if the user is asking specifically about REI / re-entry interval
        question_lower = (user_question or "").lower()
        rei_keywords = ["rei", "re-entry", "reentry", "re entry", "restricted entry interval"]
        is_rei_question = any(kw in question_lower for kw in rei_keywords)
        
        # Detect if any chunk explicitly mentions REI / re-entry
        has_rei_evidence = False
        for chunk in rag_chunks:
            content_lower = (chunk.get("content", "") or "").lower()
            if any(kw in content_lower for kw in rei_keywords):
                has_rei_evidence = True
                break
        
        # Create mapping of URLs to titles for better citations
        url_to_title = {}
        for label in tavily_labels:
            url = label.get('url', '')
            title = label.get('title', '')
            if url and title:
                # Clean up title
                if title.startswith('PDF'):
                    title = title[3:].strip()
                url_to_title[url] = title
        
        # Also get titles from downloaded PDFs
        download_info = data.get('download_info', {})
        downloaded_pdfs = download_info.get('downloaded_pdfs', [])
        for pdf_info in downloaded_pdfs:
            url = pdf_info.get('url', '')
            filename = pdf_info.get('filename', '')
            if url and url not in url_to_title:
                # Use filename as fallback title
                url_to_title[url] = filename.replace('.pdf', '').replace('_', ' ').title()
        
        # Build context from RAG chunks with page numbers, PDF titles, and URLs
        chunks_text = []
        pages_cited = {}  # Changed to dict: {page_num: {pdf_url: pdf_title}}
        pdf_urls_used = set()
        
        # PHASE 2 FIX: Debug - log page numbers from chunks
        print(f"🔍 DEBUG: Processing {len(rag_chunks)} RAG chunks for page numbers...")
        for i, chunk in enumerate(rag_chunks[:3], 1):  # Log first 3 chunks
            original_page = chunk.get('page_number', 0)
            print(f"   Chunk {i}: page_number={original_page}, chunk_index={chunk.get('chunk_index', 0)}")
        
        for i, chunk in enumerate(rag_chunks, 1):
            page_num = chunk.get('page_number', 0)
            content = chunk.get('content', '')
            score = chunk.get('score', 0.0)
            source_file = chunk.get('source_file', 'Unknown')
            pdf_url = chunk.get('pdf_url', '')
            chunk_index = chunk.get('chunk_index', 0)
            
            # PHASE 2 FIX: Ensure page number is always valid (> 0)
            original_page_num = page_num
            if page_num <= 0:
                # Fallback: Estimate page number based on chunk_index
                if chunk_index > 0:
                    # Rough estimate: 3 chunks per page
                    page_num = (chunk_index // 3) + 1
                else:
                    # Last resort: use page 1
                    page_num = 1
                print(f"⚠️  Warning: Invalid page_number ({original_page_num}) for chunk {i}, using estimated value: {page_num}")
            
            # Get PDF title
            pdf_title = url_to_title.get(pdf_url, source_file.replace('.pdf', '').replace('_', ' ').title())
            
            # Format chunk with page number, PDF title, and URL
            # PHASE 2 FIX: Make page numbers more prominent in the output
            if pdf_url:
                chunk_text = f"**Page {page_num}** of **{pdf_title}** (Relevance: {score:.2f})\n"
                chunk_text += f"PDF URL: {pdf_url}\n"
                chunk_text += f"Source: {source_file}\n"
                pdf_urls_used.add(pdf_url)
                # Track page citations with PDF info
                if page_num not in pages_cited:
                    pages_cited[page_num] = {}
                pages_cited[page_num][pdf_url] = pdf_title
            else:
                chunk_text = f"**Page {page_num}** of **{pdf_title}** (Relevance: {score:.2f})\n"
                chunk_text += f"Source: {source_file}\n"
            chunk_text += f"\nContent:\n{content}"
            
            chunks_text.append(chunk_text)
        
        context_chunks = "\n\n---\n\n".join(chunks_text)
        
        # Build list of all available PDF URLs with descriptive titles
        # Get URLs from multiple sources to ensure we have all of them
        pdf_urls_list = []
        pdf_urls_seen = set()
        
        # Create a mapping of URLs to titles from Tavily labels first
        url_to_title = {}
        for label in tavily_labels:
            url = label.get('url', '')
            title = label.get('title', '')
            if url and title:
                url_to_title[url] = title
        
        # First, get URLs from downloaded PDFs (most reliable)
        download_info = data.get('download_info', {})
        downloaded_pdfs = download_info.get('downloaded_pdfs', [])
        for pdf_info in downloaded_pdfs:
            url = pdf_info.get('url', '')
            if url and url not in pdf_urls_seen:
                # Use title from Tavily if available, otherwise use filename
                title = url_to_title.get(url, pdf_info.get('filename', 'Label PDF'))
                # Clean up title (remove "PDF" prefix if present)
                if title.startswith('PDF'):
                    title = title[3:].strip()
                pdf_urls_list.append(f"- {title}: {url}")
                pdf_urls_seen.add(url)
        
        # Also get URLs from pdf_urls field
        pdf_urls = data.get('pdf_urls', [])
        for url in pdf_urls:
            if url and url not in pdf_urls_seen:
                title = url_to_title.get(url, 'Label PDF')
                if title.startswith('PDF'):
                    title = title[3:].strip()
                pdf_urls_list.append(f"- {title}: {url}")
                pdf_urls_seen.add(url)
        
        # Finally, get any remaining URLs from Tavily labels
        for label in tavily_labels:
            url = label.get('url', '')
            title = label.get('title', 'No title')
            if url and url not in pdf_urls_seen:
                if title.startswith('PDF'):
                    title = title[3:].strip()
                pdf_urls_list.append(f"- {title}: {url}")
                pdf_urls_seen.add(url)
        
        pdf_urls_text = "\n".join(pdf_urls_list) if pdf_urls_list else "No PDF URLs available"
        
        # Build conversation context summary if available
        context_summary = ""
        if conversation_context:
            context_parts = []
            for msg in conversation_context[-4:]:  # Last 4 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")[:200]  # Truncate long messages
                context_parts.append(f"{'User' if role == 'user' else 'Assistant'}: {content}")
            if context_parts:
                context_summary = "\n\nPrevious conversation:\n" + "\n".join(context_parts)
        
        context = f"""
User asked: "{user_question}"
{context_summary}

Product: {product_name}

Label Source: {data.get('label_source', 'CDMS')}
Sources Searched: {', '.join(data.get('sources_tried', ['CDMS']))}

I searched official pesticide label databases and found {total_chunks} relevant excerpt(s) from the labels.

REI_QUESTION: {"YES" if is_rei_question else "NO"}
REI_TEXT_FOUND_IN_EXCERPTS: {"YES" if has_rei_evidence else "NO"}

Relevant excerpts with page citations:

{context_chunks}

Pages cited (with PDF source):
{chr(10).join([f"- Page {page}: {', '.join([f'{title} ({url})' for url, title in pdfs.items()])}" for page, pdfs in sorted(pages_cited.items()) if page > 0])}

Available PDF Downloads (YOU MUST INCLUDE ALL OF THESE IN YOUR RESPONSE):
{pdf_urls_text}

CRITICAL INSTRUCTIONS - READ CAREFULLY:

1. Answer the user's question directly using the provided excerpts

2. PAGE NUMBERS ARE MANDATORY - YOU MUST INCLUDE THEM:
   - EVERY piece of information you cite MUST include the page number
   - Format: "According to page X of [PDF Title]..." or "Page X of [PDF Title] states..."
   - Example: "The application rate is 2 quarts per acre (see page 5 of Roundup Label)"
   - Example: "Page 3 of the Sevin Label indicates a 7-day waiting period"
   - NEVER provide information without citing the page number
   - If you mention ANY fact from the excerpts, you MUST include which page it came from

3. PDF TITLES AND LINKS:
   - Always specify which PDF document you're citing (use the PDF title from the excerpts)
   - Include clickable links to PDFs when available: [PDF Title](PDF_URL)
   - Format: "see page X of [PDF Title](PDF_URL)" or "page X of [PDF Title](PDF_URL) states..."

4. If this is a follow-up question (like "What about safety?" or "How do I mix it?"), use the conversation context to understand what product/topic the user is asking about

5. Quote relevant sections when providing specific data (rates, safety info, etc.) - ALWAYS with page numbers

6. Be precise and factual - only use information from the provided excerpts

7. If the question asks for specific information (like application rates), provide the exact numbers from the excerpts WITH page citations

8. CRITICAL: You MUST include ALL PDF download links from the "Available PDF Downloads" section above in your response. Format them in a "📄 PDF Downloads" section at the end.

9. Use the exact URLs provided above - do not modify or shorten them

REMINDER: Page numbers are NOT optional. Every citation must include a page number. If you fail to include page numbers, your response is incomplete.
"""
        
        system_prompt = """You are an expert agriculture assistant specializing in pesticide labels with access to exact excerpts from official pesticide label databases (CDMS, Greenbook, EPA, and state databases).

MANDATORY REQUIREMENTS - PAGE NUMBERS ARE REQUIRED:

1. Answer the user's question directly using the provided excerpts

2. PAGE NUMBERS ARE MANDATORY - YOU CANNOT OMIT THEM:
   - EVERY fact, quote, or piece of information you provide MUST include the page number
   - Format examples:
     * "According to page 5 of Roundup Label, the application rate is..."
     * "Page 3 of the Sevin Label states that the waiting period is..."
     * "The mixing instructions on page 7 of [PDF Title](PDF_URL) indicate..."
   - NEVER say "the label states" without including the page number
   - NEVER provide information without citing which page it came from
   - If you reference ANY information from the excerpts, you MUST include the page number

3. PDF CITATIONS MUST INCLUDE:
   - The page number (REQUIRED)
   - The PDF title/name (REQUIRED)
   - A clickable link to the PDF when available (format: [PDF Title](PDF_URL))
   - Example: "see page 5 of [Roundup Label](https://cdms.net/.../roundup.pdf)"
   - NEVER cite just a page number without the PDF title

4. If this is a follow-up question (e.g., "What about safety?" after asking about application rates), use the conversation context to understand the product/topic being discussed

5. Quote relevant sections when providing specific data (rates, safety info, mixing instructions, etc.) - ALWAYS with page numbers

6. Be precise and factual - only use information from the provided excerpts

7. If specific numbers or rates are mentioned, include them exactly WITH page citations

8. CRITICAL: You MUST include ALL PDF download links provided in the "Available PDF Downloads" section at the end of your response in a "📄 PDF Downloads" section

9. REI / RE-ENTRY INTERVAL QUESTIONS:
   - If REI_QUESTION is YES but REI_TEXT_FOUND_IN_EXCERPTS is NO:
     * You MUST NOT guess or invent any REI value (hours/days) for the product.
     * Clearly state that the exact REI is not present in the provided excerpts.
     * Direct the user to consult the linked labels and specify that REI is usually found in the "Directions for Use", "Restrictions", or "Agricultural Use Requirements" section.
   - If REI_TEXT_FOUND_IN_EXCERPTS is YES, you may summarize the REI but ONLY using explicit text from the excerpts, with page numbers and PDF titles.

Format your response like this:

"[Direct answer to the user's question, using information from the excerpts. Be specific and cite page numbers with PDF titles. 

EXAMPLE OF CORRECT FORMATTING:
"According to page 5 of Roundup Label, the application rate is 2 quarts per acre. Page 7 of the same label indicates a 14-day waiting period."

EXAMPLE OF INCORRECT FORMATTING (DO NOT DO THIS):
"The application rate is 2 quarts per acre."  ❌ MISSING PAGE NUMBER
"The label states the rate is 2 quarts per acre."  ❌ MISSING PAGE NUMBER
]

**Key Information:**
[Quote or summarize relevant sections with page citations that include PDF titles. EVERY sentence that references information from the excerpts MUST include a page number.]

**REQUIRED Citation Format Examples:**
- "The application rate is 1.5-2.5 quarts per acre (see page 5 of [Roundup QuikPRO Label](https://www.cdms.net/ldat/mp50B003.pdf))."
- "Hand protection requirements are specified on page 5 of [Roundup Custom Safety Data Sheet](https://www.cdms.net/ldat/mp34B003.pdf)."
- "Page 3 of the Sevin Label states: 'Apply at a rate of 1-2 pounds per acre.'"

CRITICAL: Every citation MUST follow this format: "page X of [PDF Title](PDF_URL)" - make the PDF title a clickable link. NEVER omit the page number.

**📄 PDF Downloads:**
You MUST include ALL the PDF links from the "Available PDF Downloads" section below. Format them as clickable markdown links with descriptive labels:
- [Label Name/Description](Full PDF URL)
- [Label Name/Description](Full PDF URL)

Example:
- [Roundup QuikPRO Label](https://www.cdms.net/ldat/mp50B003.pdf)
- [Roundup Custom Safety Data Sheet](https://www.cdms.net/ldat/mp34B003.pdf)

All information is from official pesticide label databases (CDMS, Greenbook, EPA, or state DBs). Be conversational, helpful, and emphasize accuracy and safety. 
IMPORTANT: Always end your response with the "📄 PDF Downloads" section containing ALL the PDF URLs provided in the context."
"""
        
        return self.llm.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ],
            temperature=0.7,
            max_tokens=self.cdms_max_output_tokens
        )

    def _generate_cdms_tavily_response(self, user_question: str, data: Dict, conversation_context: list = None) -> str:
        """
        Generate response from Tavily-only search (old format, fallback)
        """
        product_name = data.get('product_name', 'Unknown product')
        ingredient = data.get('active_ingredient')
        summary = data.get('summary', '')
        labels = data.get('labels', [])
        
        # Detect if the user is asking specifically about REI / re-entry interval
        question_lower = (user_question or "").lower()
        rei_keywords = ["rei", "re-entry", "reentry", "re entry", "restricted entry interval"]
        is_rei_question = any(kw in question_lower for kw in rei_keywords)
        
        # Build context with citation emphasis
        label_list = []
        for i, label in enumerate(labels, 1):
            label_list.append(
                f"{i}. {label.get('title', 'No title')}\n"
                f"   URL: {label.get('url', '')}\n"
                f"   Relevance: {label.get('relevance', 0):.2f}\n"
                f"   Preview: {label.get('snippet', '')[:150]}..."
            )
        
        labels_text = "\n".join(label_list) if label_list else "No labels found"
        
        label_source = data.get('label_source', 'CDMS')
        sources_tried = data.get('sources_tried', ['CDMS'])
        
        context = f"""
User asked: "{user_question}"

Pesticide Label Search Results:
Product: {product_name}
{f'Active Ingredient: {ingredient}' if ingredient else ''}
Label Source: {label_source}
Sources Searched: {', '.join(sources_tried)}

AI Summary:
{summary}

Found {len(labels)} label(s):
{labels_text}

REI_QUESTION: {"YES" if is_rei_question else "NO"}

IMPORTANT: 
1. Answer the user's question based on the summary and labels
2. Provide direct PDF download links
3. Be clear about what information is available
4. Mention which database the labels came from (e.g. CDMS, Greenbook, EPA)
"""
        
        system_prompt = """You are an expert agriculture assistant specializing in pesticide information and safety.

CRITICAL RULES — DO NOT VIOLATE:
1. ONLY use information from the provided summary and labels. DO NOT invent, guess, or fabricate product descriptions, active ingredients, or safety info.
2. If 0 labels were found, say so clearly. Do NOT make up product information.
3. If labels were found, list them with download links. Only describe the product using text from the AI summary — do NOT add your own knowledge.

REI / RE-ENTRY INTERVAL QUESTIONS:
- If REI_QUESTION is YES and the summary/label snippets do NOT explicitly state an REI or re-entry interval:
  * You MUST NOT guess or invent any REI value.
  * Clearly say that the REI is not visible in the provided snippets.
  * Recommend downloading the label PDFs and checking the "Agricultural Use Requirements" or "Restrictions" section.
- Only mention specific REI values if they are clearly present in the Tavily summary or label snippets.

FORMAT when labels are found:

"I found [X] label(s) for **[Product Name]** from [Source Database Name].

**Available Labels:**
1. **[Label Name]**
   📄 Download: [URL]

2. **[Label Name]**
   📄 Download: [URL]

**💡 Tip:** These labels contain important safety information, application rates, and usage instructions. Always read the full label before use."

FORMAT when NO labels are found:

"I could not find any labels for **[Product Name]** across the pesticide label databases I searched ([list sources searched]). This product may be listed under a different name.

💡 Try searching with the active ingredient name or an alternative brand name."

Be conversational, helpful, and emphasize safety. Only state facts from the provided data."
"""
        
        return self.llm.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ],
            temperature=0.7,
            max_tokens=self.cdms_max_output_tokens
        )

    def _generate_agriculture_web_response(self, user_question: str, data: Dict, conversation_context: list = None) -> str:
        """
        Generate natural language response for agriculture web search results
        
        IMPORTANT: Must include ALL citations with URLs
        """
        query = data.get('query', user_question)
        answer = data.get('answer', '')
        sources = data.get('sources', [])
        citations = data.get('citations', '')
        
        # Build context with citation emphasis
        source_list = []
        for i, source in enumerate(sources, 1):
            source_list.append(
                f"{i}. {source.get('title', 'No title')}\n"
                f"   URL: {source.get('url', '')}\n"
                f"   Snippet: {source.get('snippet', '')[:200]}..."
            )
        
        sources_text = "\n".join(source_list) if source_list else "No sources found"
        
        context = f"""
User asked: "{user_question}"

Web Search Results:

Tavily AI Answer:
{answer}

Found {len(sources)} source(s):
{sources_text}

IMPORTANT:
1. Answer based on the Tavily AI answer and sources
2. Provide source links for further reading
3. Be informative and helpful
"""
        
        system_prompt = """You are an expert agriculture consultant helping farmers with practical, research-based advice.

Your response MUST be comprehensive and include:
1. A concise opening paragraph that directly answers the question
2. Step-by-step guidance or key points
3. Practical tips derived from the research
4. All source links for further reading

Format your response like this:

"[Write the opening summary paragraph here. Be specific, actionable, and reference the Tavily AI answer.]

**Key Points:**
• [Important point 1 from the sources]
• [Important point 2]
• [Important point 3]

**Recommended Approach:**
[If applicable, provide step-by-step guidance or a clear method]

**Learn More:**
1. **[Source Title]**
   🔗 [URL]
   
2. **[Source Title]**
   🔗 [URL]

**💡 Pro Tip:** [Add a relevant practical tip or best practice based on the information]"

Be conversational, practical, and farmer-focused. Translate research into actionable advice. Use the Tavily AI answer as your primary source, then supplement with details from the sources."
"""
        
        return self.llm.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ],
            temperature=0.7,
            max_tokens=800
        )

    def _generate_generic_response(self, user_question: str, data: Dict, conversation_context: list = None) -> str:
        """Generate generic response for unknown tool types"""
        
        prompt = f"""User asked: "{user_question}"

Tool returned this data: {data}

Generate a helpful, natural language response based on this information. Keep it concise and conversational (2-3 sentences)."""
        
        return self.llm.chat(
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )


# Test function
if __name__ == "__main__":
    print("Testing LLM Response Generator...")
    print("-" * 70)
    
    try:
        generator = LLMResponseGenerator()
        
        # Test with weather data
        print("\n📝 Test: Weather Response")
        print("-" * 70)
        
        weather_data = {
            "city": "London",
            "country": "GB",
            "temperature": 15.5,
            "feels_like": 14.2,
            "humidity": 72,
            "wind_speed": 5.2,
            "description": "partly cloudy"
        }
        
        response = generator.generate_response(
            user_question="What's the weather in London?",
            tool_name="weather",
            tool_result=weather_data
        )
        
        print(f"User Question: What's the weather in London?")
        print(f"\n🤖 LLM Response:\n{response}")
        
        print("\n" + "=" * 70)
        print("✅ Test complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure:")
        print("   1. You have LLM_PROVIDER and LLM_MODEL set in .env (or use defaults)")
        print("   2. You have the appropriate API key (OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY)")
        print("   3. You have internet connection")

