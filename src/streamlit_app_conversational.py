"""
Conversational AI Assistant - Streamlit UI
Natural language input → Tool selection → LLM response → User
"""

import streamlit as st
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.parser import parse_query
from src.utils.parameter_extractor import extract_keywords_from_query
from src.tools.tool_matcher import ToolMatcher
from src.tools.tool_executor import ToolExecutor
from src.cdms.schema import DatabaseManager, Feedback, QueryLog

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="AgAdvisor",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# CUSTOM STYLING
# ============================================================================

st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    
    /* Colorful chat input */
    .stChatInput {
        border: 2px solid #1E88E5 !important;
        border-radius: 10px !important;
        background: linear-gradient(135deg, #E3F2FD 0%, #FFFFFF 100%) !important;
    }
    .stChatInput:focus-within {
        border: 2px solid #4CAF50 !important;
        box-shadow: 0 0 10px rgba(76, 175, 80, 0.3) !important;
    }
    
    /* Borderless, muted processing details toggle */
    .proc-details summary {
        font-size: 0.78rem;
        color: #999;
        cursor: pointer;
        list-style: none;
        margin-bottom: 4px;
    }
    .proc-details summary::-webkit-details-marker { display: none; }
    .proc-details summary::before { content: "▸ "; }
    .proc-details[open] summary::before { content: "▾ "; }
    .proc-details .proc-log {
        font-size: 0.75rem;
        color: #999;
        line-height: 1.6;
        margin: 0 0 8px 6px;
        padding: 0;
    }
    
    /* Sleek processing UI — progress bar & steps */
    .proc-progress-wrap {
        margin: 12px 0 16px 0;
        border-radius: 8px;
        overflow: hidden;
        background: #e8eef5;
        height: 6px;
    }
    .proc-progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #1E88E5 0%, #4CAF50 100%);
        border-radius: 8px;
        transition: width 0.4s ease-out;
    }
    .proc-step {
        padding: 6px 0;
        border-left: 3px solid #e0e0e0;
        margin-left: 8px;
        padding-left: 12px;
        transition: all 0.3s ease;
    }
    .proc-step.done {
        border-left-color: #4CAF50;
        opacity: 1;
    }
    .proc-step.active {
        border-left-color: #1E88E5;
        background: linear-gradient(90deg, rgba(30,136,229,0.08) 0%, transparent 100%);
        border-radius: 8px;
        margin: 4px 0 4px 8px;
        padding: 8px 12px;
        animation: proc-pulse 1.5s ease-in-out infinite;
    }
    @keyframes proc-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.85; }
    }
    .proc-hourglass {
        display: inline-block;
        animation: proc-hourglass-flip 1.5s ease-in-out infinite;
    }
    @keyframes proc-hourglass-flip {
        0%, 100% { transform: rotate(0deg); }
        50% { transform: rotate(180deg); }
    }
    .proc-step-label {
        font-size: 0.9rem;
        font-weight: 500;
        color: #333;
    }
    .proc-step-detail {
        font-size: 0.8rem;
        color: #666;
        margin-top: 2px;
    }
    /* Loading spinner next to "Processing your question" */
    .proc-loading-spinner {
        display: inline-block;
        width: 18px;
        height: 18px;
        border: 2px solid #e0e0e0;
        border-top-color: #1E88E5;
        border-radius: 50%;
        animation: proc-spin 0.8s linear infinite;
        vertical-align: middle;
        margin-right: 8px;
    }
    @keyframes proc-spin {
        to { transform: rotate(360deg); }
    }

    /* Pull invisible star buttons up over the colored HTML stars */
    [data-testid="stChatMessage"] [data-testid="stHorizontalBlock"]
        [data-testid="stBaseButton-secondary"] {
        margin-top: -2.2rem !important;
        height: 1.8rem !important;
    }
    [data-testid="stChatMessage"] [data-testid="stHorizontalBlock"]
        [data-testid="stBaseButton-secondary"] button {
        opacity: 0 !important;
        width: 100% !important;
        height: 1.8rem !important;
        min-height: 0 !important;
        padding: 0 !important;
        cursor: pointer !important;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

# Initialize chat sessions
if 'chats' not in st.session_state:
    st.session_state.chats = {
        'chat_1': {
            'name': 'Chat 1',
            'messages': [],
            'created_at': time.time()
        }
    }
    st.session_state.current_chat_id = 'chat_1'
    st.session_state.chat_counter = 1

# Get current chat
if 'current_chat_id' not in st.session_state:
    st.session_state.current_chat_id = 'chat_1'

# For backwards compatibility
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = st.session_state.chats.get(
        st.session_state.current_chat_id, {}
    ).get('messages', [])

if 'feedback_state' not in st.session_state:
    st.session_state.feedback_state = {}

if 'tool_matcher' not in st.session_state:
    st.session_state.tool_matcher = ToolMatcher()

if 'tool_executor' not in st.session_state:
    st.session_state.tool_executor = ToolExecutor()

# ============================================================================
# HEADER WITH CHAT CONTROLS
# ============================================================================

# Chat management in header
col_title, col_new_chat = st.columns([4, 1])

with col_title:
    st.markdown('<div class="main-title">🌱 AgAdvisor</div>', unsafe_allow_html=True)

with col_new_chat:
    if st.button("➕ New Chat", type="primary", use_container_width=True):
        # Create new chat
        st.session_state.chat_counter += 1
        new_chat_id = f'chat_{st.session_state.chat_counter}'
        st.session_state.chats[new_chat_id] = {
            'name': f'Chat {st.session_state.chat_counter}',
            'messages': [],
            'created_at': time.time()
        }
        st.session_state.current_chat_id = new_chat_id
        st.rerun()

st.markdown(
    '<div class="subtitle">Our intelligent farming assistant! Get pesticide labels (CDMS), and chemical application best practices with citations.</div>',
    unsafe_allow_html=True
)

# ============================================================================
# EXAMPLE QUESTIONS (MOVED TO TOP)
# ============================================================================

# Example queries section at the top
with st.expander("💡 Example Questions", expanded=False):
    st.markdown("#### 📄 Pesticide Labels (CDMS)")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("REI for Sevin", use_container_width=True, key="ex_rei"):
            st.session_state.example_input = "What is the REI (re-entry interval) for Sevin?"
    
    with col2:
        if st.button("Roundup on Corn", use_container_width=True, key="ex_roundup"):
            st.session_state.example_input = "Find the application rate for Roundup on corn."
    
    with col3:
        if st.button("2,4-D Safety", use_container_width=True, key="ex_24d"):
            st.session_state.example_input = "What are the safety precautions for 2,4-D herbicide?"
    
    st.markdown("#### 🌾 General Agriculture")
    col4, col5, col6 = st.columns(3)
    
    with col4:
        if st.button("Spider Mites", use_container_width=True, key="ex_mites"):
            st.session_state.example_input = "How do I control spider mites on soybean plants?"
    
    with col5:
        if st.button("Nitrogen Timing", use_container_width=True, key="ex_nitrogen"):
            st.session_state.example_input = "When should I apply nitrogen fertilizer to winter wheat?"
    
    with col6:
        if st.button("Blossom End Rot", use_container_width=True, key="ex_blossom"):
            st.session_state.example_input = "What causes blossom end rot in tomatoes and how do I fix it?"

st.markdown("---")

# Show current chat info
current_chat = st.session_state.chats[st.session_state.current_chat_id]
msg_count = len(current_chat['messages'])
st.caption(f"💬 {current_chat['name']} • {msg_count} messages")

# ============================================================================
# DISPLAY CONVERSATION HISTORY (CHAT-STYLE)
# ============================================================================

# Get messages for current chat
messages = current_chat['messages']

# Create a container for messages (chat window)
chat_container = st.container()

with chat_container:
    if not messages:
        st.info("👋 Welcome! Start a conversation by typing a question below.")
    else:
        # Display messages in chronological order (oldest to newest, like ChatGPT)
        for idx, message in enumerate(messages):
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(message["content"])
            
            else:  # assistant
                with st.chat_message("assistant"):
                    # Processing details — collapsed dropdown (all steps ✅, progress bar)
                    metadata = message.get("metadata", {})
                    proc_log = metadata.get("processing_log", []) if metadata else []
                    if proc_log:
                        lines = []
                        for line in proc_log:
                            clean = line.replace("**", "")
                            if line.strip().startswith("**Step"):
                                lines.append(f'<span class="proc-step done">✅ {clean}</span>')
                            else:
                                lines.append(f'<span class="proc-step-detail" style="margin-left:20px">{clean}</span>')
                        log_html = "<br>".join(lines)
                        st.markdown(
                            f'<details class="proc-details">'
                            f'<summary>Processing details</summary>'
                            f'<div class="proc-progress-wrap" style="margin:8px 0">'
                            f'<div class="proc-progress-fill" style="width:100%"></div></div>'
                            f'<div class="proc-log">{log_html}</div>'
                            f'</details>',
                            unsafe_allow_html=True
                        )
                    
                    # Main response
                    st.markdown(message["content"])
                    
                    # --- Feedback UI ---
                    _STAR_COLORS = ["#e53935", "#fb8c00", "#fdd835", "#c0ca33", "#43a047"]
                    chat_id = st.session_state.current_chat_id
                    fb_key = f"{chat_id}_{idx}"
                    fb_state = st.session_state.feedback_state.get(fb_key)
                    
                    if fb_state and fb_state.get("submitted"):
                        r = fb_state['rating']
                        c = _STAR_COLORS[r - 1]
                        filled = "".join(f'<span style="color:{_STAR_COLORS[i]}">★</span>' for i in range(r))
                        empty = "".join(f'<span style="color:#ddd">☆</span>' for _ in range(5 - r))
                        st.markdown(
                            f'<span style="font-size:0.85rem;">{filled}{empty}</span>'
                            f' <span style="color:#999;font-size:0.78rem;">thanks!</span>',
                            unsafe_allow_html=True,
                        )
                    else:
                        selected = fb_state.get("rating") if fb_state else None
                        st.markdown(
                            '<span style="color:#aaa;font-size:0.78rem;">Rate this response</span>',
                            unsafe_allow_html=True,
                        )
                        cols = st.columns([0.3, 0.3, 0.3, 0.3, 0.3, 6])
                        for star in range(1, 6):
                            with cols[star - 1]:
                                c = _STAR_COLORS[star - 1]
                                filled = selected is not None and star <= selected
                                sym = "★" if filled else "☆"
                                st.markdown(
                                    f'<span style="color:{c};font-size:1.3rem;'
                                    f'cursor:pointer;user-select:none;">{sym}</span>',
                                    unsafe_allow_html=True,
                                )
                                st.button("\u200b", key=f"star_{fb_key}_{star}")
                                if st.session_state.get(f"star_{fb_key}_{star}"):
                                    st.session_state.feedback_state[fb_key] = {"rating": star, "submitted": False}
                                    st.rerun()
                        
                        if selected and not (fb_state or {}).get("submitted"):
                            comment = st.text_input(
                                "Could you briefly explain your rating?",
                                key=f"comment_{fb_key}",
                                placeholder="e.g. The answer was helpful but could use more detail...",
                            )
                            if st.button("Submit", key=f"submit_{fb_key}"):
                                if not comment or not comment.strip():
                                    st.warning("Please share a brief comment before submitting.")
                                    st.stop()
                                user_msg = ""
                                if idx > 0:
                                    prev = messages[idx - 1]
                                    if prev["role"] == "user":
                                        user_msg = prev["content"]
                                try:
                                    db = DatabaseManager()
                                    session = db.get_session()
                                    session.add(Feedback(
                                        chat_id=chat_id,
                                        user_query=user_msg,
                                        agent_response=message["content"][:2000],
                                        tool_used=metadata.get("tool", "") if metadata else "",
                                        rating=selected,
                                        comment=comment if comment else None,
                                    ))
                                    session.commit()
                                    session.close()
                                except Exception:
                                    pass
                                st.session_state.feedback_state[fb_key] = {
                                    "rating": selected,
                                    "submitted": True,
                                }
                                st.rerun()

# ============================================================================
# INPUT SECTION (AT BOTTOM, LIKE CHATGPT)
# ============================================================================

# Chat input (like ChatGPT)
user_input = st.chat_input(
    placeholder="Type your message here... e.g., 'Find Roundup label', 'Weather in Paris?', 'How to control aphids?'",
    key="chat_input"
)

# Handle example button clicks
if 'example_input' in st.session_state:
    user_input = st.session_state.example_input
    del st.session_state.example_input

# Process if there's input OR if there's a pending processing task
current_chat = st.session_state.chats[st.session_state.current_chat_id]
has_new_input = user_input is not None and user_input.strip() != ""

# Check for pending processing (after rerun)
pending_processing_key = None
for key in list(st.session_state.keys()):
    if key.startswith(f"processing_{st.session_state.current_chat_id}_"):
        pending_processing_key = key
        break

# Processing state (multi-step with progressive display)
proc_state = st.session_state.get("_proc_state")

# ============================================================================
# PROCESS QUERY
# ============================================================================

if has_new_input or pending_processing_key or (proc_state and proc_state.get("chat_id") == st.session_state.current_chat_id):
    # --- New input: add user message and init processing state ---
    if has_new_input:
        msg_count_before = len(current_chat['messages'])
        processing_key = f"processing_{st.session_state.current_chat_id}_{msg_count_before}"
        current_chat['messages'].append({
            "role": "user",
            "content": user_input,
            "timestamp": time.time()
        })
        st.session_state[processing_key] = user_input
        st.session_state["_proc_state"] = {
            "chat_id": st.session_state.current_chat_id,
            "step": 0,
            "log": [],
            "question": user_input,
            "processing_key": processing_key,
        }
        st.rerun()
    
    # --- Get processing state ---
    proc_state = st.session_state.get("_proc_state", {})
    processing_key = proc_state.get("processing_key") or pending_processing_key
    question_to_process = proc_state.get("question", "") or st.session_state.get(processing_key, "")
    
    # --- Sleek processing UI: spinner + progress bar + steps — as assistant message ---
    step = proc_state.get("step", 0)
    log = proc_state.get("log", [])
    # Progress bar: 0→25→50→75→90→100 as steps complete
    progress_pct = (step * 25) if step < 4 else 90
    
    with st.chat_message("assistant"):
        with st.status("Processing your question...", expanded=True, state="running"):
            # Loading spinner (always visible next to header)
            st.markdown(
                '<div style="margin-bottom:12px;display:flex;align-items:center;gap:8px">'
                '<span class="proc-loading-spinner"></span>'
                '<span style="font-size:0.9rem;color:#555;font-weight:500">Processing your question...</span>'
                '</div>',
                unsafe_allow_html=True
            )
            # Progress bar (fills sequentially with each task)
            st.markdown(
                f'<div class="proc-progress-wrap">'
                f'<div class="proc-progress-fill" style="width:{progress_pct}%"></div>'
                f'</div>'
                f'<div style="font-size:0.75rem;color:#999;margin-top:4px">'
                f'Step {min(step + 1, 4)} of 4</div>',
                unsafe_allow_html=True
            )
            if not log:
                st.caption("Analyzing your question...")
            else:
                step_header_idxs = [i for i, L in enumerate(log) if L.strip().startswith("**Step")]
                last_step_idx = step_header_idxs[-1] if step_header_idxs else -1
                for i, line in enumerate(log):
                    clean = line.replace("**", "")
                    if line.strip().startswith("**Step"):
                        is_active = i == last_step_idx
                        cls = "active" if is_active else "done"
                        icon = '<span class="proc-hourglass">⏳</span>' if is_active else "✅"
                        st.markdown(
                            f'<div class="proc-step {cls}">'
                            f'<span class="proc-step-label">{icon} {clean}</span></div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(f'<div class="proc-step-detail" style="margin-left:20px">{clean}</div>', unsafe_allow_html=True)
    
    # --- Run next step ---
    step = proc_state.get("step", 0)
    log = list(proc_state.get("log", []))
    keywords = proc_state.get("keywords", [])
    conversation_context = proc_state.get("conversation_context", [])
    selected_tool = proc_state.get("selected_tool", "cdms_label")
    confidence = proc_state.get("confidence", 0.0)
    method = proc_state.get("method", "unknown")
    tool_result = proc_state.get("tool_result")
    
    try:
        if step == 0:
            log.append("**Step 1:** 🔍 Analyzing your question...")
            try:
                parsed = parse_query(question_to_process)
                keywords = parsed.get("extracted_keywords", [])
                log.append(f"   ✅ Keywords: {', '.join(keywords[:5])}")
            except Exception:
                log.append("   ⚠️ Using direct matching")
                keywords = []
            st.session_state["_proc_state"] = {**proc_state, "step": 1, "log": log, "keywords": keywords}
            st.rerun()
        
        if step == 1:
            log.append("**Step 2:** 🔄 Checking conversation context...")
            if len(current_chat['messages']) > 1:
                recent = current_chat['messages'][-6:-1]
                conversation_context = [{"role": m["role"], "content": m["content"]} for m in recent]
                log.append(f"   ✅ Using context from {len(conversation_context)} previous messages")
            else:
                log.append("   ℹ️ No previous context")
            st.session_state["_proc_state"] = {**proc_state, "step": 2, "log": log, "conversation_context": conversation_context}
            st.rerun()
        
        if step == 2:
            log.append("**Step 3:** 🎯 Selecting best tool...")
            try:
                tool_match = st.session_state.tool_matcher.match_tool(
                    keywords, question_to_process, conversation_context=conversation_context
                )
                selected_tool = tool_match["tool_name"]
                confidence = tool_match["confidence"]
                method = tool_match.get("method", "unknown")
                if method == "fast_path":
                    log.append("   ⚡ Fast path (keyword matching)")
                elif method in ("llm_path", "llm_cached"):
                    log.append(f"   🧠 LLM classification ({'cached' if method == 'llm_cached' else 'live'})")
                elif method == "hybrid":
                    log.append("   🔀 Hybrid (fast + LLM)")
                else:
                    log.append(f"   ⚙️ {method}")
                log.append(f"   ✅ Selected: **{selected_tool}** ({confidence:.0%} confidence)")
            except Exception:
                log.append("   ⚠️ Using default tool")
                selected_tool = "cdms_label"
                confidence = 0.3
                method = "fallback"
            st.session_state["_proc_state"] = {**proc_state, "step": 3, "log": log, "selected_tool": selected_tool, "confidence": confidence, "method": method}
            st.rerun()
        
        if step == 3:
            # Add Step 4 to checklist first so it appears as "in progress", then rerun
            log.append(f"**Step 4:** ⚙️ Executing **{selected_tool}** tool...")
            st.session_state["_proc_state"] = {**proc_state, "step": 4, "log": log}
            st.rerun()
        
        if step == 4:
            try:
                tool_result = st.session_state.tool_executor.execute(
                    tool_name=selected_tool,
                    user_question=question_to_process,
                    conversation_context=conversation_context
                )
                if not tool_result.get("success", False):
                    tool_result["llm_response"] = f"I encountered an error: {tool_result.get('error', 'Unknown error')}"
                    log.append(f"   ❌ Error: {tool_result.get('error', 'Unknown error')}")
                else:
                    if tool_result.get("fallback_used"):
                        log.append("   ⚠️ CDMS found no results, using agriculture web search as fallback")
                    else:
                        log.append("   ✅ Tool executed successfully!")
                        if selected_tool in ["cdms_label", "cdms", "pesticide_label"]:
                            raw = tool_result.get("raw_data", {})
                            pdfs_d = raw.get("pdfs_downloaded", 0)
                            pdfs_i = raw.get("pdfs_indexed", 0)
                            if pdfs_d > 0:
                                log.append(f"   📥 Downloaded {pdfs_d} PDF(s)")
                                if pdfs_i > 0:
                                    log.append(f"   📚 Indexed {pdfs_i} PDF(s) for RAG search")
                                for pdf in raw.get("download_info", {}).get("downloaded_pdfs", [])[:3]:
                                    cached = "cached" if pdf.get("cached") else "new"
                                    log.append(f"   📄 {pdf.get('filename', 'Unknown')} ({cached})")
            except Exception as e:
                tool_result = {"success": False, "error": str(e), "llm_response": f"I encountered an error: {str(e)}"}
                log.append(f"   ❌ Execution error: {str(e)}")
            
            # Done: add assistant message, clear state
            response_text = tool_result.get("llm_response", "I couldn't process that request. Please try again.")
            current_chat['messages'].append({
                "role": "assistant",
                "content": response_text,
                "timestamp": time.time(),
                "metadata": {
                    "tool": tool_result.get("tool_used", selected_tool),
                    "original_tool": selected_tool,
                    "fallback_used": tool_result.get("fallback_used", False),
                    "keywords": keywords,
                    "confidence": confidence,
                    "raw_data": tool_result.get("raw_data"),
                    "success": tool_result.get("success", False),
                    "error": tool_result.get("error") if not tool_result.get("success") else None,
                    "has_context": len(conversation_context) > 0,
                    "context_messages": len(conversation_context),
                    "processing_log": log  # for collapsed dropdown after
                }
            })
            # Log every query to shared DB (all users, all devices)
            try:
                db = DatabaseManager()
                session = db.get_session()
                session.add(QueryLog(
                    user_query=question_to_process[:2000],
                    agent_response=response_text[:5000] if response_text else None,
                    tool_used=tool_result.get("tool_used", selected_tool),
                    success=1 if tool_result.get("success", False) else 0,
                ))
                session.commit()
                session.close()
            except Exception:
                pass
            if "_proc_state" in st.session_state:
                del st.session_state["_proc_state"]
            if processing_key and processing_key in st.session_state:
                del st.session_state[processing_key]
            st.rerun()
    
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        current_chat['messages'].append({
            "role": "assistant",
            "content": f"I encountered an error: {str(e)}. Please check the error details above.",
            "timestamp": time.time(),
            "metadata": {"tool": "unknown", "error": str(e)}
        })
        for k in ["_proc_state", processing_key]:
            if k and k in st.session_state:
                del st.session_state[k]
        st.rerun()

# Clear chat button moved to sidebar

# ============================================================================
# SIDEBAR - CHAT MANAGEMENT
# ============================================================================

with st.sidebar:
    st.markdown("### 💬 Chat Sessions")
    
    # Clear current chat button
    if st.button("🗑️ Clear Current Chat", type="secondary", use_container_width=True, key="clear_sidebar"):
        current_chat['messages'] = []
        st.rerun()
    
    st.markdown("---")
    
    # Sort chats by created_at (newest first)
    sorted_chats = sorted(
        st.session_state.chats.items(),
        key=lambda x: x[1]['created_at'],
        reverse=True
    )
    
    # Display all chats
    for chat_id, chat_data in sorted_chats:
        # Count messages
        msg_count = len(chat_data['messages'])
        
        # Get first user message as preview
        preview = "Empty chat"
        if chat_data['messages']:
            first_msg = next(
                (msg for msg in chat_data['messages'] if msg['role'] == 'user'),
                None
            )
            if first_msg:
                preview = first_msg['content'][:30] + "..." if len(first_msg['content']) > 30 else first_msg['content']
        
        # Create button for each chat
        is_current = chat_id == st.session_state.current_chat_id
        button_type = "primary" if is_current else "secondary"
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            if st.button(
                f"{'📍' if is_current else '💬'} {chat_data['name']}\n{preview}\n({msg_count} msgs)",
                key=f"chat_{chat_id}",
                type=button_type,
                use_container_width=True
            ):
                if not is_current:
                    st.session_state.current_chat_id = chat_id
                    st.rerun()
        
        with col2:
            if not is_current and len(st.session_state.chats) > 1:
                if st.button("🗑️", key=f"delete_{chat_id}", help="Delete chat"):
                    del st.session_state.chats[chat_id]
                    # If we deleted the current chat, switch to another one
                    if st.session_state.current_chat_id == chat_id:
                        st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
                    st.rerun()
    
    st.markdown("---")
    
    # Feedback & Query Log export
    st.markdown("### 📊 Data Export")
    try:
        db = DatabaseManager()
        session = db.get_session()
        feedback_rows = session.query(Feedback).order_by(Feedback.created_at.desc()).all()
        try:
            query_rows = session.query(QueryLog).order_by(QueryLog.created_at.desc()).all()
        except Exception:
            query_rows = []
        session.close()
        st.caption(f"{len(feedback_rows)} feedback, {len(query_rows)} queries (all users)")
        if feedback_rows:
            import io, csv
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["id", "chat_id", "user_query", "agent_response", "tool_used", "rating", "comment", "created_at"])
            for r in feedback_rows:
                writer.writerow([r.id, r.chat_id, r.user_query, r.agent_response, r.tool_used, r.rating, r.comment, r.created_at])
            st.download_button(
                "Download Feedback CSV",
                data=buf.getvalue(),
                file_name="agadvisor_feedback.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_feedback",
            )
        if query_rows:
            import io, csv
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["id", "user_query", "agent_response", "tool_used", "success", "created_at"])
            for r in query_rows:
                writer.writerow([r.id, r.user_query, getattr(r, "agent_response", ""), r.tool_used, r.success, r.created_at])
            st.download_button(
                "Download Query Log CSV",
                data=buf.getvalue(),
                file_name="agadvisor_queries.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_queries",
            )
    except Exception:
        st.caption("Database not available")
    
    st.markdown("---")
    
    # Debug mode
    st.markdown("### ⚙️ Debug")
    debug_mode = st.checkbox("Show Debug Info", value=False)
    
    if debug_mode:
        st.markdown("---")
        st.markdown("### Session State")
        current_chat = st.session_state.chats[st.session_state.current_chat_id]
        st.json({
            "total_chats": len(st.session_state.chats),
            "current_chat_id": st.session_state.current_chat_id,
            "current_chat_messages": len(current_chat['messages'])
        })

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #999; font-size: 0.8rem;">
        AgAdvisor can make mistakes. Always verify important information with official sources before making decisions.
    </div>
""", unsafe_allow_html=True)

