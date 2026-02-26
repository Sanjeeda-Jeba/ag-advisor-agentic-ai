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
from src.cdms.schema import DatabaseManager, Feedback

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
    '<div class="subtitle">Your intelligent farming assistant! Get weather data, soil information, pesticide labels (CDMS), and agriculture best practices with citations.</div>',
    unsafe_allow_html=True
)

# ============================================================================
# EXAMPLE QUESTIONS (MOVED TO TOP)
# ============================================================================

# Example queries section at the top
with st.expander("💡 Example Questions", expanded=False):
    st.markdown("#### 🔍 Quick Search Tools")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🌤️ Weather", use_container_width=True, key="ex_weather"):
            st.session_state.example_input = "What's the weather in London?"
    
    with col2:
        if st.button("🌱 Soil Data", use_container_width=True, key="ex_soil"):
            st.session_state.example_input = "Show me soil data for Iowa"
    
    with col3:
        if st.button("📄 CDMS Search", use_container_width=True, key="ex_cdms"):
            st.session_state.example_input = "Find Roundup label"
    
    st.markdown("#### 🏷️ CDMS Pesticide Labels (with Citations)")
    col4, col5, col6 = st.columns(3)
    
    with col4:
        if st.button("🌿 Roundup Label", use_container_width=True, key="ex_roundup"):
            st.session_state.example_input = "Find me the Roundup pesticide label"
    
    with col5:
        if st.button("🐛 Sevin Label", use_container_width=True, key="ex_sevin"):
            st.session_state.example_input = "Show me the Sevin insecticide label"
    
    with col6:
        if st.button("🌾 2,4-D Label", use_container_width=True, key="ex_24d"):
            st.session_state.example_input = "Get the 2,4-D herbicide label"
    
    st.markdown("#### 🌐 Agriculture Web Search (with Citations)")
    col7, col8, col9 = st.columns(3)
    
    with col7:
        if st.button("🐜 Pest Control", use_container_width=True, key="ex_pest"):
            st.session_state.example_input = "How to control aphids on tomato plants?"
    
    with col8:
        if st.button("🌱 Fertilization", use_container_width=True, key="ex_fert"):
            st.session_state.example_input = "Best practices for corn fertilization timing"
    
    with col9:
        if st.button("🌍 Soil Health", use_container_width=True, key="ex_soil_health"):
            st.session_state.example_input = "How to improve soil organic matter?"

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
                    # Processing details — muted toggle ABOVE the response
                    metadata = message.get("metadata", {})
                    proc_log = metadata.get("processing_log", []) if metadata else []
                    if proc_log:
                        log_html = "<br>".join(
                            line.replace("**", "") for line in proc_log
                        )
                        st.markdown(
                            f'<details class="proc-details">'
                            f'<summary>Processing details</summary>'
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
for key in st.session_state.keys():
    if key.startswith(f"processing_{st.session_state.current_chat_id}_"):
        pending_processing_key = key
        break

# ============================================================================
# PROCESS QUERY
# ============================================================================

if has_new_input or pending_processing_key:
    # Get current chat (already have it)
    
    if has_new_input:
        # New input - add user message and set processing flag
        # Use message count before adding to create unique key
        msg_count_before = len(current_chat['messages'])
        processing_key = f"processing_{st.session_state.current_chat_id}_{msg_count_before}"
        
        # Add user message to current chat
        current_chat['messages'].append({
            "role": "user",
            "content": user_input,
            "timestamp": time.time()
        })
        st.session_state[processing_key] = user_input
        # Rerun immediately to show user message
        st.rerun()
    else:
        # Pending processing - continue with existing processing key
        processing_key = pending_processing_key
    
    # Get the question to process (from session state)
    question_to_process = st.session_state.get(processing_key, user_input if has_new_input else "")
    
    # Processing — show a simple spinner; collect detailed log for the
    # dropdown that persists in the chat history after processing.
    processing_log = []   # collects lines for the post-response expander
    try:
        with st.spinner("Processing your question..."):
            # Step 1: Parse and extract keywords
            processing_log.append("**Step 1:** 🔍 Analyzing your question...")
            try:
                parsed = parse_query(question_to_process)
                keywords = parsed.get("extracted_keywords", [])
                processing_log.append(f"   ✅ Keywords: {', '.join(keywords[:5])}")
            except Exception as e:
                processing_log.append(f"   ⚠️ Using direct matching")
                keywords = []
            
            # Step 2: Get conversation history for context
            processing_log.append("**Step 2:** 🔄 Checking conversation context...")
            conversation_context = []
            if len(current_chat['messages']) > 1:
                recent_messages = current_chat['messages'][-6:-1]
                for msg in recent_messages:
                    conversation_context.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                processing_log.append(f"   ✅ Using context from {len(conversation_context)} previous messages")
            else:
                processing_log.append(f"   ℹ️ No previous context")
            
            # Step 3: Match with tools
            processing_log.append("**Step 3:** 🎯 Selecting best tool...")
            try:
                tool_match = st.session_state.tool_matcher.match_tool(
                    keywords,
                    question_to_process,
                    conversation_context=conversation_context
                )
                selected_tool = tool_match["tool_name"]
                confidence = tool_match["confidence"]
                method = tool_match.get("method", "unknown")
                llm_used = tool_match.get("llm_used", False)
                
                if method == "fast_path":
                    processing_log.append(f"   ⚡ Fast path (keyword matching)")
                elif method in ("llm_path", "llm_cached"):
                    processing_log.append(f"   🧠 LLM classification ({'cached' if method == 'llm_cached' else 'live'})")
                elif method == "hybrid":
                    processing_log.append(f"   🔀 Hybrid (fast + LLM)")
                else:
                    processing_log.append(f"   ⚙️ {method}")
                
                processing_log.append(f"   ✅ Selected: **{selected_tool}** ({confidence:.0%} confidence)")
                
                if llm_used and tool_match.get("llm_reasoning"):
                    processing_log.append(f"   💭 Reasoning: {tool_match['llm_reasoning'][:100]}...")
            except Exception as e:
                processing_log.append(f"   ⚠️ Using default tool")
                selected_tool = "cdms_label"
                confidence = 0.3
                method = "fallback"
            
            # Step 4: Execute tool
            processing_log.append(f"**Step 4:** ⚙️ Executing **{selected_tool}** tool...")
            try:
                tool_result = st.session_state.tool_executor.execute(
                    tool_name=selected_tool,
                    user_question=question_to_process,
                    conversation_context=conversation_context
                )
                
                if not tool_result.get("success", False):
                    error_msg = tool_result.get("error", "Unknown error")
                    tool_result["llm_response"] = f"I encountered an error: {error_msg}"
                    processing_log.append(f"   ❌ Error: {error_msg}")
                else:
                    if tool_result.get("fallback_used"):
                        processing_log.append(f"   ⚠️ CDMS found no results, using agriculture web search as fallback")
                    else:
                        processing_log.append(f"   ✅ Tool executed successfully!")
                        
                        if selected_tool in ["cdms_label", "cdms", "pesticide_label"]:
                            raw_data = tool_result.get("raw_data", {})
                            pdfs_downloaded = raw_data.get("pdfs_downloaded", 0)
                            pdfs_indexed = raw_data.get("pdfs_indexed", 0)
                            if pdfs_downloaded > 0:
                                processing_log.append(f"   📥 Downloaded {pdfs_downloaded} PDF(s)")
                                if pdfs_indexed > 0:
                                    processing_log.append(f"   📚 Indexed {pdfs_indexed} PDF(s) for RAG search")
                                download_info = raw_data.get("download_info", {})
                                downloaded_pdfs = download_info.get("downloaded_pdfs", [])
                                for pdf in downloaded_pdfs[:3]:
                                    cached = "cached" if pdf.get("cached") else "new"
                                    processing_log.append(f"   📄 {pdf.get('filename', 'Unknown')} ({cached})")
                
            except Exception as e:
                tool_result = {
                    "success": False,
                    "error": str(e),
                    "llm_response": f"I encountered an error while processing your request: {str(e)}"
                }
                processing_log.append(f"   ❌ Execution error: {str(e)}")
        
        # Add assistant response to current chat
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
                "processing_log": processing_log  # saved for the dropdown
            }
        })
        
        # Clear processing flag
        if processing_key in st.session_state:
            del st.session_state[processing_key]
        
        # Rerun to show the new message
        st.rerun()
    
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        
        # Add error message to current chat
        current_chat['messages'].append({
            "role": "assistant",
            "content": f"I encountered an error: {str(e)}. Please check the error details above.",
            "timestamp": time.time(),
            "metadata": {
                "tool": "unknown",
                "error": str(e)
            }
        })
        
        # Clear processing flag (use the one from outer scope)
        if 'processing_key' in locals() and processing_key in st.session_state:
            del st.session_state[processing_key]
        elif pending_processing_key and pending_processing_key in st.session_state:
            del st.session_state[pending_processing_key]
        
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
    
    # Feedback export
    st.markdown("### 📊 Feedback")
    try:
        db = DatabaseManager()
        session = db.get_session()
        rows = session.query(Feedback).order_by(Feedback.created_at.desc()).all()
        session.close()
        st.caption(f"{len(rows)} response(s) collected")
        if rows:
            import io, csv
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["id", "chat_id", "user_query", "agent_response", "tool_used", "rating", "comment", "created_at"])
            for r in rows:
                writer.writerow([r.id, r.chat_id, r.user_query, r.agent_response, r.tool_used, r.rating, r.comment, r.created_at])
            st.download_button(
                "Download CSV",
                data=buf.getvalue(),
                file_name="agadvisor_feedback.csv",
                mime="text/csv",
                use_container_width=True,
            )
    except Exception:
        st.caption("Feedback DB not available")
    
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

