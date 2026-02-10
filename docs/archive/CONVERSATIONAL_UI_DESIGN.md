# Conversational NLP UI Design

## 🎯 UI Flow Overview

```
┌────────────────────────────────────────────────────────────────┐
│  User Input (Natural Language)                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ "What's the weather in Iowa?"                            │ │
│  └──────────────────────────────────────────────────────────┘ │
│                           [Ask] Button                         │
└────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────┐
│  Processing (Behind the scenes)                                │
│  1. Parser extracts keywords: ["weather", "Iowa"]              │
│  2. Match keywords with tool catalog                           │
│  3. Tool Matcher selects: Weather API (95% match)              │
│  4. Execute Weather API call                                   │
│  5. Generate natural language response                         │
└────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────┐
│  Response Display                                              │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 🤖 Assistant:                                            │ │
│  │                                                          │ │
│  │ The current weather in Iowa is 18°C with clear skies.   │ │
│  │ Humidity is at 65% and wind speed is 5 m/s. It's a      │ │
│  │ pleasant day!                                            │ │
│  │                                                          │ │
│  │ ✓ Tool Used: Weather API                                │ │
│  │ ✓ Keywords: weather, Iowa                               │ │
│  │ ✓ Confidence: 95%                                        │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

---

## 🎨 UI Components

### 1. **Input Section**
- Large text input box for natural language questions
- Placeholder text with examples
- "Ask" button to submit
- Optional: Voice input button

### 2. **Processing Indicator**
- Shows: "Analyzing your question..."
- Shows: "Extracting keywords..."
- Shows: "Matching with tools..."
- Shows: "Calling [Tool Name]..."
- Shows: "Generating response..."

### 3. **Response Section**
- Natural language response (main content)
- Tool information badge
- Keywords extracted badge
- Confidence score
- Optional: "Show Details" expander with raw data

### 4. **Conversation History**
- Previous questions and answers
- Scroll through conversation
- Clear history button

---

## 💻 Implementation

### Main UI File: `src/streamlit_app_conversational.py`

```python
import streamlit as st
from src.parser import parse_query
from src.tools.tool_matcher import ToolMatcher
from src.tools.nlp_response_generator import generate_natural_response

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="AI Assistant",
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
    .user-message {
        background-color: #E3F2FD;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #1E88E5;
    }
    .assistant-message {
        background-color: #F5F5F5;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #4CAF50;
    }
    .tool-badge {
        display: inline-block;
        background-color: #4CAF50;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 0.85rem;
        margin: 5px 5px 5px 0;
    }
    .keyword-badge {
        display: inline-block;
        background-color: #FF9800;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 0.85rem;
        margin: 5px 5px 5px 0;
    }
    .confidence-badge {
        display: inline-block;
        background-color: #2196F3;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 0.85rem;
        margin: 5px 5px 5px 0;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'tool_matcher' not in st.session_state:
    st.session_state.tool_matcher = ToolMatcher()

# ============================================================================
# HEADER
# ============================================================================

st.markdown('<div class="main-title">🤖 AI Assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Ask me anything! I can help with weather, soil data, and documentation.</div>',
    unsafe_allow_html=True
)

# ============================================================================
# MAIN INPUT
# ============================================================================

# Example queries section
with st.expander("💡 Example Questions", expanded=False):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🌤️ Weather Example", use_container_width=True):
            st.session_state.example_input = "What's the weather in London?"
    
    with col2:
        if st.button("🌱 Soil Example", use_container_width=True):
            st.session_state.example_input = "Show me soil data for Iowa"
    
    with col3:
        if st.button("📚 Documentation Example", use_container_width=True):
            st.session_state.example_input = "How do I use the weather API?"

# Input box
user_input = st.text_area(
    "Ask your question:",
    value=st.session_state.get('example_input', ''),
    placeholder="Type your question here... e.g., 'What's the weather in Paris?'",
    height=100,
    label_visibility="collapsed"
)

# Clear example after using it
if 'example_input' in st.session_state:
    del st.session_state.example_input

# Submit button
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    ask_button = st.button("🔍 Ask", type="primary", use_container_width=True)

# ============================================================================
# PROCESS QUERY
# ============================================================================

if ask_button and user_input.strip():
    # Add user message to history
    st.session_state.conversation_history.append({
        "role": "user",
        "content": user_input
    })
    
    # Processing steps with status updates
    with st.status("🤔 Processing your question...", expanded=True) as status:
        # Step 1: Parse and extract keywords
        st.write("1️⃣ Parsing query and extracting keywords...")
        parsed = parse_query(user_input)
        keywords = parsed.get("extracted_keywords", [])
        
        # Step 2: Match with tools
        st.write("2️⃣ Matching keywords with available tools...")
        tool_match = st.session_state.tool_matcher.match_tool(keywords, user_input)
        selected_tool = tool_match["tool_name"]
        confidence = tool_match["confidence"]
        
        # Step 3: Execute tool
        st.write(f"3️⃣ Calling {selected_tool}...")
        tool_result = st.session_state.tool_matcher.execute_tool(
            tool_name=selected_tool,
            question=user_input,
            keywords=keywords
        )
        
        # Step 4: Generate natural language response
        st.write("4️⃣ Generating response...")
        nl_response = generate_natural_response(
            tool_name=selected_tool,
            tool_result=tool_result,
            user_question=user_input
        )
        
        status.update(label="✅ Complete!", state="complete", expanded=False)
    
    # Add assistant response to history
    st.session_state.conversation_history.append({
        "role": "assistant",
        "content": nl_response,
        "metadata": {
            "tool": selected_tool,
            "keywords": keywords,
            "confidence": confidence,
            "raw_data": tool_result
        }
    })

# ============================================================================
# DISPLAY CONVERSATION HISTORY
# ============================================================================

st.markdown("---")

if st.session_state.conversation_history:
    # Clear history button
    if st.button("🗑️ Clear Conversation", type="secondary"):
        st.session_state.conversation_history = []
        st.rerun()
    
    st.markdown("### 💬 Conversation")
    
    # Display messages
    for idx, message in enumerate(st.session_state.conversation_history):
        if message["role"] == "user":
            st.markdown(f"""
                <div class="user-message">
                    <strong>👤 You:</strong><br>
                    {message["content"]}
                </div>
            """, unsafe_allow_html=True)
        
        else:  # assistant
            st.markdown(f"""
                <div class="assistant-message">
                    <strong>🤖 Assistant:</strong><br>
                    {message["content"]}
                </div>
            """, unsafe_allow_html=True)
            
            # Show metadata badges
            metadata = message.get("metadata", {})
            if metadata:
                badges_html = f"""
                    <div style="margin-top: 10px;">
                        <span class="tool-badge">🔧 {metadata.get('tool', 'Unknown')}</span>
                        <span class="confidence-badge">📊 {metadata.get('confidence', 0):.0%} confidence</span>
                """
                
                keywords = metadata.get('keywords', [])
                if keywords:
                    keywords_text = ", ".join(keywords[:3])  # Show first 3 keywords
                    badges_html += f'<span class="keyword-badge">🔑 {keywords_text}</span>'
                
                badges_html += "</div>"
                st.markdown(badges_html, unsafe_allow_html=True)
            
            # Optional: Show raw data
            if metadata and "raw_data" in metadata:
                with st.expander("🔍 Show Technical Details"):
                    st.json(metadata["raw_data"])

else:
    # Empty state
    st.info("👋 Welcome! Ask me a question to get started.")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        Powered by LangGraph, spaCy, and OpenAI | 
        <a href="#" style="color: #1E88E5;">About</a> | 
        <a href="#" style="color: #1E88E5;">Help</a>
    </div>
""", unsafe_allow_html=True)
```

---

## 🔧 Supporting Components

### 1. Tool Matcher (`src/tools/tool_matcher.py`)

```python
from typing import List, Dict
from rapidfuzz import fuzz
from src.tools.weather_tool import execute_weather_tool
from src.tools.soil_tool import execute_soil_tool
from src.tools.rag_tool import execute_rag_tool

class ToolMatcher:
    """
    Matches user queries to appropriate tools based on keyword matching
    """
    
    def __init__(self):
        # Define tool catalog with keywords
        self.tools = {
            "weather": {
                "name": "Weather API",
                "keywords": ["weather", "temperature", "forecast", "climate", 
                           "rain", "sunny", "cloudy", "hot", "cold", "humid",
                           "wind", "precipitation"],
                "execute_fn": execute_weather_tool,
                "description": "Get weather information for any location"
            },
            "soil": {
                "name": "Soil Data API",
                "keywords": ["soil", "agriculture", "farming", "crop", "pH",
                           "nutrients", "clay", "sand", "silt", "organic",
                           "nitrogen", "fertility", "plant", "grow"],
                "execute_fn": execute_soil_tool,
                "description": "Get soil properties and agricultural data"
            },
            "documentation": {
                "name": "Documentation Search",
                "keywords": ["how", "what", "why", "explain", "documentation",
                           "docs", "guide", "tutorial", "help", "api",
                           "instructions", "example", "show", "tell"],
                "execute_fn": execute_rag_tool,
                "description": "Search documentation and knowledge base"
            }
        }
    
    def match_tool(self, keywords: List[str], full_query: str) -> Dict:
        """
        Match extracted keywords to the best tool
        
        Args:
            keywords: List of extracted keywords
            full_query: Original user question
        
        Returns:
            Dict with tool_name, confidence, and matched_keywords
        """
        scores = {}
        
        # Score each tool based on keyword overlap
        for tool_id, tool_info in self.tools.items():
            score = 0
            matched_keywords = []
            
            # Check keyword overlap
            for keyword in keywords:
                for tool_keyword in tool_info["keywords"]:
                    # Use fuzzy matching
                    similarity = fuzz.ratio(keyword.lower(), tool_keyword.lower())
                    if similarity > 80:  # 80% similarity threshold
                        score += similarity
                        matched_keywords.append(tool_keyword)
            
            # Also check full query against tool keywords
            query_lower = full_query.lower()
            for tool_keyword in tool_info["keywords"]:
                if tool_keyword in query_lower:
                    score += 50  # Bonus for exact matches in query
            
            scores[tool_id] = {
                "score": score,
                "matched_keywords": list(set(matched_keywords))
            }
        
        # Get best matching tool
        if not scores or max(s["score"] for s in scores.values()) == 0:
            # Default to documentation if no match
            best_tool = "documentation"
            confidence = 0.5
        else:
            best_tool = max(scores, key=lambda x: scores[x]["score"])
            max_score = scores[best_tool]["score"]
            # Normalize confidence to 0-1
            confidence = min(max_score / 300, 1.0)
        
        return {
            "tool_name": best_tool,
            "tool_display_name": self.tools[best_tool]["name"],
            "confidence": confidence,
            "matched_keywords": scores[best_tool]["matched_keywords"],
            "all_scores": scores
        }
    
    def execute_tool(self, tool_name: str, question: str, keywords: List[str]) -> Dict:
        """
        Execute the selected tool
        
        Args:
            tool_name: Name of the tool to execute
            question: User's question
            keywords: Extracted keywords
        
        Returns:
            Tool execution result
        """
        tool = self.tools.get(tool_name)
        
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found"
            }
        
        try:
            result = tool["execute_fn"](question)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

### 2. Natural Language Response Generator (`src/tools/nlp_response_generator.py`)

```python
def generate_natural_response(tool_name: str, tool_result: dict, user_question: str) -> str:
    """
    Convert tool results into natural language responses
    
    Args:
        tool_name: Name of the tool that was used
        tool_result: Result from tool execution
        user_question: Original user question
    
    Returns:
        Natural language response string
    """
    
    if not tool_result.get("success"):
        return f"I'm sorry, I encountered an error: {tool_result.get('error', 'Unknown error')}"
    
    # Route to appropriate formatter
    if tool_name == "weather":
        return format_weather_nl(tool_result["data"])
    elif tool_name == "soil":
        return format_soil_nl(tool_result["data"])
    elif tool_name == "documentation":
        return format_rag_nl(tool_result["data"])
    else:
        return "I processed your request but couldn't format the response properly."


def format_weather_nl(data: dict) -> str:
    """Format weather data as natural language"""
    temp = data.get("temperature", "N/A")
    feels_like = data.get("feels_like", "N/A")
    humidity = data.get("humidity", "N/A")
    wind = data.get("wind_speed", "N/A")
    description = data.get("description", "unclear")
    city = data.get("city", "the requested location")
    
    response = f"The current weather in {city} is {temp}°C with {description} skies. "
    
    if feels_like != temp:
        response += f"It feels like {feels_like}°C. "
    
    response += f"The humidity is at {humidity}% and wind speed is {wind} m/s."
    
    # Add contextual advice
    if temp < 10:
        response += " It's quite cold, dress warmly!"
    elif temp > 30:
        response += " It's hot outside, stay hydrated!"
    
    return response


def format_soil_nl(data: dict) -> str:
    """Format soil data as natural language"""
    location = data.get("location", {})
    properties = data.get("properties", {})
    
    if not properties:
        return "I found the location but couldn't retrieve soil data. The area might not have available soil information."
    
    response = f"Here's the soil information for the requested location:\n\n"
    
    # pH Level
    if "phh2o" in properties:
        ph = properties["phh2o"]["value"]
        response += f"• The soil pH is {ph}, which is "
        if ph < 6.5:
            response += "acidic. "
        elif ph > 7.5:
            response += "alkaline. "
        else:
            response += "neutral. "
        response += "\n"
    
    # Soil composition
    composition = []
    if "clay" in properties:
        composition.append(f"{properties['clay']['value']}% clay")
    if "sand" in properties:
        composition.append(f"{properties['sand']['value']}% sand")
    if "silt" in properties:
        composition.append(f"{properties['silt']['value']}% silt")
    
    if composition:
        response += f"• Soil composition: {', '.join(composition)}.\n"
    
    # Nutrients
    if "nitrogen" in properties:
        response += f"• Nitrogen content: {properties['nitrogen']['value']} {properties['nitrogen'].get('unit', '')}.\n"
    
    if "soc" in properties:
        response += f"• Organic carbon: {properties['soc']['value']} {properties['soc'].get('unit', '')}.\n"
    
    return response


def format_rag_nl(data: dict) -> str:
    """Format RAG results as natural language"""
    api_matches = data.get("api_matches", [])
    doc_context = data.get("document_context", [])
    
    response = "Based on the documentation, here's what I found:\n\n"
    
    # API matches
    if api_matches:
        response += "**Relevant APIs:**\n"
        for api in api_matches[:3]:  # Top 3
            response += f"• {api['api_name']}: {api.get('description', 'No description')}\n"
        response += "\n"
    
    # Document context
    if doc_context:
        response += "**From the documentation:**\n"
        for doc in doc_context[:2]:  # Top 2
            excerpt = doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"]
            response += f"• {excerpt}\n"
            response += f"  (Source: {doc['source']}, Page {doc['page']})\n\n"
    
    if not api_matches and not doc_context:
        response = "I searched the documentation but couldn't find specific information about your question. Could you rephrase or ask something else?"
    
    return response
```

---

## 🎯 Key Features

### ✅ **Natural Language In/Out**
- User types normal questions
- System responds in conversational language
- No technical jargon in responses

### ✅ **Keyword-Based Tool Matching**
- Extract keywords using spaCy
- Match keywords to tool catalog
- Score and rank tools
- Select best match

### ✅ **Transparent Processing**
- Show which tool was selected
- Display confidence score
- Show matched keywords
- Optional: Show raw data

### ✅ **Conversation History**
- Keep track of Q&A
- Scroll through history
- Clear conversation option

### ✅ **Simple & Clean UI**
- Centered layout
- Chat-like interface
- Color-coded messages
- Clear visual hierarchy

---

## 📊 Example Interactions

### Example 1: Weather Query
```
User: "What's the weather like in Paris today?"

[Processing...]
✓ Keywords extracted: weather, Paris, today
✓ Tool matched: Weather API (95% confidence)
✓ Calling Weather API...
