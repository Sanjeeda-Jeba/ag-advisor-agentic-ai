"""
Streamlit UI for API Query Parser
This app provides an interactive interface for parsing natural language queries
and matching them to relevant APIs using NLP and fuzzy matching.
"""

import streamlit as st
import sys
from pathlib import Path
import time

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import our parser
from parser import parse_query

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="API Query Parser",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# CUSTOM CSS STYLING
# ============================================================================

st.markdown("""
    <style>
    /* Main header styling */
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Keyword badge styling */
    .keyword-badge {
        background-color: #E3F2FD;
        color: #1976D2;
        padding: 6px 14px;
        border-radius: 16px;
        margin: 4px;
        display: inline-block;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    /* API card styling */
    .api-card {
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 20px;
        margin: 16px 0;
        background-color: #FFFFFF;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .api-card-high {
        border-left: 4px solid #43A047;
    }
    
    .api-card-medium {
        border-left: 4px solid #FB8C00;
    }
    
    .api-card-low {
        border-left: 4px solid #E53935;
    }
    
    .api-name {
        font-size: 1.3rem;
        font-weight: bold;
        color: #212121;
        margin-bottom: 8px;
    }
    
    .api-description {
        font-size: 1rem;
        color: #666;
        margin-bottom: 12px;
    }
    
    .confidence-label {
        font-size: 0.9rem;
        color: #666;
        margin-bottom: 4px;
    }
    
    /* Example query button styling */
    .example-query {
        background-color: #F5F5F5;
        padding: 10px 16px;
        border-radius: 8px;
        margin: 8px 0;
        cursor: pointer;
        border: 1px solid #E0E0E0;
        transition: all 0.3s;
    }
    
    .example-query:hover {
        background-color: #E3F2FD;
        border-color: #1E88E5;
    }
    
    /* Info box styling */
    .info-box {
        background-color: #E8F5E9;
        padding: 16px;
        border-radius: 8px;
        border-left: 4px solid #43A047;
        margin: 16px 0;
    }
    
    /* Divider styling */
    hr {
        margin: 2rem 0;
        border: none;
        border-top: 2px solid #E0E0E0;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

# Initialize session state variables
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

if 'last_query' not in st.session_state:
    st.session_state.last_query = ""

if 'results' not in st.session_state:
    st.session_state.results = None

if 'selected_example' not in st.session_state:
    st.session_state.selected_example = ""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def display_keywords(keywords):
    """Display extracted keywords as styled badges."""
    if keywords:
        st.markdown("### 🔑 Extracted Keywords")
        # Create HTML for keyword badges
        badges_html = ""
        for keyword in keywords:
            badges_html += f'<span class="keyword-badge">{keyword}</span>'
        st.markdown(badges_html, unsafe_allow_html=True)
    else:
        st.info("No keywords extracted from the query.")


def get_confidence_category(score):
    """Categorize confidence score into high/medium/low."""
    if score >= 85:
        return "high", "🟢"
    elif score >= 70:
        return "medium", "🟡"
    else:
        return "low", "🔴"


def display_api_matches(ranked_apis):
    """Display matched APIs as styled cards with confidence scores."""
    if ranked_apis:
        st.markdown("### 🎯 Matched APIs")
        
        for api in ranked_apis:
            api_name = api.get("api_name", "Unknown")
            description = api.get("description", "No description available")
            score = api.get("score", 0)
            
            # Get confidence category and emoji
            category, emoji = get_confidence_category(score)
            
            # Create card HTML
            card_class = f"api-card api-card-{category}"
            
            st.markdown(f"""
                <div class="{card_class}">
                    <div class="api-name">{emoji} {api_name}</div>
                    <div class="api-description">{description}</div>
                    <div class="confidence-label">Confidence Score:</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Display progress bar for confidence score
            st.progress(score / 100)
            st.caption(f"{score}% match")
            st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ No matching APIs found. Try rephrasing your query or use different keywords.")


def process_query(query):
    """Process the query and return results."""
    try:
        with st.spinner("🔄 Parsing your query..."):
            start_time = time.time()
            results = parse_query(query)
            end_time = time.time()
            processing_time = round((end_time - start_time) * 1000, 2)
            
            return results, processing_time
    except Exception as e:
        st.error(f"❌ An error occurred while processing your query: {str(e)}")
        st.info("💡 Please check that all dependencies are installed and the API catalog is available.")
        return None, 0

# ============================================================================
# MAIN UI LAYOUT
# ============================================================================

# Header Section
st.markdown('<div class="main-header">🔍 API Query Parser</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Transform natural language queries into matched APIs using NLP and fuzzy matching</div>',
    unsafe_allow_html=True
)

st.markdown("---")

# Introduction
st.markdown("""
Welcome to the **API Query Parser**! This tool helps you find the right API by simply describing what you need in natural language.
Just type your query below, and we'll analyze it to suggest the most relevant APIs from our catalog.
""")

# ============================================================================
# EXAMPLE QUERIES SECTION
# ============================================================================

st.markdown("### 💡 Try These Example Queries")

example_queries = [
    "Get customer details for John Smith",
    "What's the product stock for laptops?",
    "Check inventory levels for wireless headphones",
    "I need customer information",
    "Show me product availability"
]

# Create columns for example queries
col1, col2 = st.columns(2)

with col1:
    if st.button(example_queries[0], key="ex1", use_container_width=True):
        st.session_state.selected_example = example_queries[0]
    if st.button(example_queries[1], key="ex2", use_container_width=True):
        st.session_state.selected_example = example_queries[1]
    if st.button(example_queries[2], key="ex3", use_container_width=True):
        st.session_state.selected_example = example_queries[2]

with col2:
    if st.button(example_queries[3], key="ex4", use_container_width=True):
        st.session_state.selected_example = example_queries[3]
    if st.button(example_queries[4], key="ex5", use_container_width=True):
        st.session_state.selected_example = example_queries[4]

st.markdown("---")

# ============================================================================
# QUERY INPUT SECTION
# ============================================================================

st.markdown("### ✍️ Enter Your Query")

# Use selected example if available
default_query = st.session_state.selected_example if st.session_state.selected_example else ""

# Create two columns for input and buttons
input_col, button_col = st.columns([4, 1])

with input_col:
    user_query = st.text_input(
        "Type your natural language query here:",
        value=default_query,
        placeholder="e.g., Get customer details or Check product inventory",
        label_visibility="collapsed"
    )

with button_col:
    parse_button = st.button("🔍 Parse Query", type="primary", use_container_width=True)
    clear_button = st.button("🗑️ Clear", use_container_width=True)

# Clear button functionality
if clear_button:
    st.session_state.selected_example = ""
    st.session_state.last_query = ""
    st.session_state.results = None
    st.rerun()

# ============================================================================
# QUERY PROCESSING AND RESULTS DISPLAY
# ============================================================================

# Process query when button is clicked or example is selected
if parse_button or st.session_state.selected_example:
    # Reset selected example after processing
    if st.session_state.selected_example:
        user_query = st.session_state.selected_example
        st.session_state.selected_example = ""
    
    # Validate query
    if not user_query or user_query.strip() == "":
        st.warning("⚠️ Please enter a query before parsing.")
    else:
        # Process the query
        results, processing_time = process_query(user_query)
        
        if results:
            # Store results in session state
            st.session_state.results = results
            st.session_state.last_query = user_query
            
            # Add to query history
            if user_query not in st.session_state.query_history:
                st.session_state.query_history.insert(0, user_query)
                # Keep only last 10 queries
                st.session_state.query_history = st.session_state.query_history[:10]

# Display results if available
if st.session_state.results:
    st.markdown("---")
    st.markdown("## 📊 Results")
    
    # Display original query
    st.markdown(f"""
        <div class="info-box">
            <strong>📝 Your Query:</strong><br>
            <em>"{st.session_state.last_query}"</em>
        </div>
    """, unsafe_allow_html=True)
    
    # Create two columns for results
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        # Display keywords
        keywords = st.session_state.results.get("extracted_keywords", [])
        display_keywords(keywords)
    
    with col_right:
        # Display processing time
        st.markdown("### ⚡ Performance")
        st.metric("Processing Time", "< 1 second")
        st.metric("Keywords Found", len(keywords))
        st.metric("APIs Matched", len(st.session_state.results.get("ranked_api_matches", [])))
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Display API matches
    ranked_apis = st.session_state.results.get("ranked_api_matches", [])
    display_api_matches(ranked_apis)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem; padding: 20px;">
    <strong>API Query Parser v1.0</strong> | Powered by spaCy, RapidFuzz, and LangGraph | Built using Streamlit
</div>
""", unsafe_allow_html=True)

