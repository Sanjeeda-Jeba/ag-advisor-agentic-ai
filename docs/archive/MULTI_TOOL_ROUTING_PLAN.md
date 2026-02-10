# Multi-Tool Routing Agent System Plan

## 🎯 Overview

Transform your system into an **intelligent agent** that can:
1. **Understand** the user's question
2. **Decide** which tool to use (Weather API, Spotify API, or RAG)
3. **Execute** the appropriate tool
4. **Return** formatted results

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Question                            │
│          "What's the weather in London?"                         │
│          "Play some jazz music"                                  │
│          "How do I use the weather API?"                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Intent Classifier Node                        │
│  - Analyzes the question                                         │
│  - Determines intent: weather | music | documentation | general  │
│  - Routes to appropriate tool                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────┴────────┐
                    │                 │
        ┌───────────▼──────┐  ┌──────▼────────┐  ┌──────▼─────────┐
        │  Weather Tool    │  │  Spotify Tool │  │  RAG Tool      │
        │  (API Call)      │  │  (API Call)   │  │  (Doc Search)  │
        └───────────┬──────┘  └──────┬────────┘  └──────┬─────────┘
                    │                 │                   │
                    └────────┬────────┴──────────┬────────┘
                             │                   │
                             ▼                   ▼
        ┌─────────────────────────────────────────────────────────┐
        │            Response Formatter Node                      │
        │  - Formats weather data                                 │
        │  - Formats music results                                │
        │  - Formats documentation context                        │
        └────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
        ┌─────────────────────────────────────────────────────────┐
        │                   Final Response                        │
        │  "The weather in London is 15°C, partly cloudy"        │
        │  "Here's a jazz playlist: ..."                         │
        │  "According to the docs: ..."                          │
        └─────────────────────────────────────────────────────────┘
```

---

## 🔧 Key Components

### 1. **Intent Classifier** (The Router)
Decides which tool to call based on the question.

**Options for Classification:**
- **Option A:** Simple keyword matching (fast, good for demo)
- **Option B:** ML classifier (spaCy text categorization)
- **Option C:** LLM-based routing (OpenAI API, most flexible)

### 2. **Tool Definitions**
Each tool has:
- **Name**: "weather_api", "spotify_api", "rag_search"
- **Description**: What it does
- **Parameters**: What inputs it needs
- **Execute Function**: How to call it

### 3. **LangGraph Workflow**
Orchestrates the flow from question → classification → tool → response

---

## 📋 Implementation Plan

### **Phase 1: Define Tools & Intent Classifier** (Days 1-2)

#### Step 1.1: Create Tool Registry (`src/tools/tool_registry.py`)

```python
from typing import Dict, Any, Callable
from enum import Enum

class ToolType(Enum):
    WEATHER = "weather"
    SPOTIFY = "spotify"
    RAG = "rag"
    UNKNOWN = "unknown"

class Tool:
    def __init__(self, name: str, description: str, 
                 execute_fn: Callable, required_params: list):
        self.name = name
        self.description = description
        self.execute_fn = execute_fn
        self.required_params = required_params
    
    def execute(self, **kwargs):
        """Execute the tool with given parameters"""
        return self.execute_fn(**kwargs)

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
    
    def register_tool(self, tool: Tool):
        """Register a new tool"""
        self.tools[tool.name] = tool
    
    def get_tool(self, tool_name: str) -> Tool:
        """Get a tool by name"""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> list:
        """List all available tools"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "params": tool.required_params
            }
            for tool in self.tools.values()
        ]
```

#### Step 1.2: Create Intent Classifier (`src/tools/intent_classifier.py`)

**Option A: Keyword-Based (Recommended for Demo)**
```python
import re
from typing import Tuple

class KeywordIntentClassifier:
    def __init__(self):
        self.patterns = {
            "weather": [
                r"\b(weather|temperature|forecast|climate|rain|sunny|cloudy)\b",
                r"\b(hot|cold|warm|humid)\b",
                r"\b(degrees|celsius|fahrenheit)\b"
            ],
            "spotify": [
                r"\b(music|song|play|playlist|artist|album|track)\b",
                r"\b(spotify|listen|playing)\b",
                r"\b(jazz|rock|pop|classical|hip hop)\b"
            ],
            "rag": [
                r"\b(how to|how do|what is|explain|documentation|docs)\b",
                r"\b(api|guide|tutorial|help|instructions)\b",
                r"\b(tell me about|information about)\b"
            ]
        }
    
    def classify(self, question: str) -> Tuple[str, float]:
        """
        Classify the intent of the question
        Returns: (intent, confidence_score)
        """
        question_lower = question.lower()
        scores = {}
        
        for intent, patterns in self.patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, question_lower):
                    score += 1
            scores[intent] = score
        
        # Get highest scoring intent
        if max(scores.values()) > 0:
            best_intent = max(scores, key=scores.get)
            confidence = min(scores[best_intent] / 3, 1.0)  # Normalize
            return best_intent, confidence
        
        return "rag", 0.5  # Default to RAG for general questions
```

**Option B: LLM-Based (More Flexible)**
```python
import openai

class LLMIntentClassifier:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
    
    def classify(self, question: str) -> Tuple[str, float]:
        """Use OpenAI to classify intent"""
        prompt = f"""Classify the following question into one of these categories:
- weather: Questions about weather, temperature, climate
- spotify: Questions about music, songs, playlists
- rag: Questions about documentation, how-to, API usage
- general: General questions

Question: {question}

Respond with only the category name."""

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        intent = response.choices[0].message.content.strip().lower()
        confidence = 0.9  # LLM confidence is generally high
        
        return intent, confidence
```

#### Step 1.3: Create Tool Implementations (`src/tools/`)

**Weather Tool (`src/tools/weather_tool.py`)**
```python
from src.api_clients.weather_client import WeatherClient
from src.utils.parameter_extractor import extract_city_from_query

def execute_weather_tool(question: str, **kwargs) -> dict:
    """Execute weather API call"""
    # Extract city from question
    city = extract_city_from_query(question)
    
    if not city:
        return {
            "success": False,
            "error": "Could not extract city from question"
        }
    
    # Call weather API
    client = WeatherClient()
    result = client.get_weather(city=city)
    
    return {
        "success": True,
        "tool": "weather",
        "data": result
    }
```

**Spotify Tool (`src/tools/spotify_tool.py`)**
```python
from src.api_clients.spotify_client import SpotifyClient

def execute_spotify_tool(question: str, **kwargs) -> dict:
    """Execute Spotify API call"""
    # Extract music query (genre, artist, etc.)
    query = extract_music_query(question)
    
    # Call Spotify API
    client = SpotifyClient()
    result = client.search_tracks(query=query, limit=10)
    
    return {
        "success": True,
        "tool": "spotify",
        "data": result
    }
```

**RAG Tool (`src/tools/rag_tool.py`)**
```python
from src.rag.hybrid_retriever import HybridRetriever

def execute_rag_tool(question: str, **kwargs) -> dict:
    """Execute RAG document search"""
    retriever = HybridRetriever()
    
    # Search both API catalog and PDF documents
    results = retriever.retrieve(question, top_k=5)
    
    return {
        "success": True,
        "tool": "rag",
        "data": {
            "api_matches": results["results"],
            "document_context": results["document_context"]
        }
    }
```

---

### **Phase 2: Update LangGraph with Tool Routing** (Days 3-4)

#### Step 2.1: Create New Agent Graph (`src/agent_graph_v2.py`)

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal
from src.tools.intent_classifier import KeywordIntentClassifier
from src.tools.tool_registry import ToolRegistry, Tool
from src.tools.weather_tool import execute_weather_tool
from src.tools.spotify_tool import execute_spotify_tool
from src.tools.rag_tool import execute_rag_tool

# Define the state
class AgentState(TypedDict):
    question: str
    intent: str
    confidence: float
    tool_result: dict
    formatted_response: str

# Initialize classifier and registry
classifier = KeywordIntentClassifier()
registry = ToolRegistry()

# Register tools
registry.register_tool(Tool(
    name="weather",
    description="Get weather information for a city",
    execute_fn=execute_weather_tool,
    required_params=["question"]
))

registry.register_tool(Tool(
    name="spotify",
    description="Search for music on Spotify",
    execute_fn=execute_spotify_tool,
    required_params=["question"]
))

registry.register_tool(Tool(
    name="rag",
    description="Search documentation and knowledge base",
    execute_fn=execute_rag_tool,
    required_params=["question"]
))

# Node 1: Classify Intent
def classify_intent_node(state: AgentState) -> AgentState:
    """Classify the user's question intent"""
    question = state["question"]
    intent, confidence = classifier.classify(question)
    
    return {
        "intent": intent,
        "confidence": confidence
    }

# Node 2: Execute Tool
def execute_tool_node(state: AgentState) -> AgentState:
    """Execute the appropriate tool based on intent"""
    intent = state["intent"]
    question = state["question"]
    
    # Get the tool
    tool = registry.get_tool(intent)
    
    if not tool:
        # Fallback to RAG
        tool = registry.get_tool("rag")
    
    # Execute the tool
    result = tool.execute(question=question)
    
    return {
        "tool_result": result
    }

# Node 3: Format Response
def format_response_node(state: AgentState) -> AgentState:
    """Format the tool result into a user-friendly response"""
    tool_result = state["tool_result"]
    intent = state["intent"]
    
    if not tool_result.get("success"):
        response = f"Sorry, I couldn't process your request: {tool_result.get('error')}"
    elif intent == "weather":
        data = tool_result["data"]
        response = format_weather_response(data)
    elif intent == "spotify":
        data = tool_result["data"]
        response = format_spotify_response(data)
    elif intent == "rag":
        data = tool_result["data"]
        response = format_rag_response(data)
    else:
        response = "I'm not sure how to help with that."
    
    return {
        "formatted_response": response
    }

# Build the graph
graph_builder = StateGraph(AgentState)

# Add nodes
graph_builder.add_node("classify_intent", classify_intent_node)
graph_builder.add_node("execute_tool", execute_tool_node)
graph_builder.add_node("format_response", format_response_node)

# Add edges
graph_builder.add_edge(START, "classify_intent")
graph_builder.add_edge("classify_intent", "execute_tool")
graph_builder.add_edge("execute_tool", "format_response")
graph_builder.add_edge("format_response", END)

# Compile
multi_tool_agent = graph_builder.compile()
```

#### Step 2.2: Add Conditional Routing (Optional - More Advanced)

```python
# Instead of direct edge, use conditional routing

def route_to_tool(state: AgentState) -> Literal["weather_tool", "spotify_tool", "rag_tool"]:
    """Route to appropriate tool based on intent"""
    intent = state["intent"]
    
    if intent == "weather":
        return "weather_tool"
    elif intent == "spotify":
        return "spotify_tool"
    else:
        return "rag_tool"

# Update graph with conditional routing
graph_builder.add_conditional_edges(
    "classify_intent",
    route_to_tool,
    {
        "weather_tool": "weather_tool",
        "spotify_tool": "spotify_tool",
        "rag_tool": "rag_tool"
    }
)

# Add separate tool nodes
graph_builder.add_node("weather_tool", execute_weather_node)
graph_builder.add_node("spotify_tool", execute_spotify_node)
graph_builder.add_node("rag_tool", execute_rag_node)

# All tools converge to formatter
graph_builder.add_edge("weather_tool", "format_response")
graph_builder.add_edge("spotify_tool", "format_response")
graph_builder.add_edge("rag_tool", "format_response")
```

---

### **Phase 3: Implement Spotify API Integration** (Days 5-6)

#### Step 3.1: Add Spotify to API Catalog
```json
{
  "name": "spotify_search",
  "description": "Search for music tracks, artists, and playlists on Spotify",
  "tags": ["music", "spotify", "songs", "playlist"],
  "keywords": ["music", "song", "play", "artist", "album", "spotify"],
  "api_type": "spotify",
  "endpoint": "https://api.spotify.com/v1/search",
  "method": "GET",
  "auth_type": "bearer_token",
  "required_params": ["q", "type"],
  "enabled": true
}
```

#### Step 3.2: Create Spotify Client (`src/api_clients/spotify_client.py`)
```python
from src.api_clients.base_client import BaseAPIClient
import requests

class SpotifyClient(BaseAPIClient):
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.spotify.com/v1"
        self.access_token = self._get_access_token()
    
    def _get_access_token(self):
        """Get Spotify access token using client credentials"""
        # This requires SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET
        auth_url = "https://accounts.spotify.com/api/token"
        
        response = requests.post(auth_url, data={
            "grant_type": "client_credentials"
        }, auth=(self.client_id, self.client_secret))
        
        return response.json()["access_token"]
    
    def search_tracks(self, query: str, limit: int = 10):
        """Search for tracks on Spotify"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        response = requests.get(
            f"{self.base_url}/search",
            headers=headers,
            params={
                "q": query,
                "type": "track",
                "limit": limit
            }
        )
        
        return self._format_track_results(response.json())
```

#### Step 3.3: Add to Environment Variables
```bash
# Add to .env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
```

---

### **Phase 4: Update Streamlit UI** (Days 7-8)

#### Step 4.1: Create Multi-Tool Interface

```python
import streamlit as st
from src.agent_graph_v2 import multi_tool_agent

st.title("🤖 Multi-Tool AI Assistant")

st.markdown("""
Ask me anything! I can help with:
- 🌤️ **Weather**: "What's the weather in Paris?"
- 🎵 **Music**: "Play some jazz music"
- 📚 **Documentation**: "How do I use the weather API?"
""")

# User input
question = st.text_input("Ask me anything:", placeholder="What's the weather like today?")

if st.button("Ask"):
    with st.spinner("Processing your question..."):
        # Run the agent
        result = multi_tool_agent.invoke({"question": question})
        
        # Display intent classification
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Detected Intent", result["intent"].title())
        with col2:
            st.metric("Confidence", f"{result['confidence']:.0%}")
        
        st.divider()
        
        # Display result based on tool used
        tool_used = result["tool_result"].get("tool")
        
        if tool_used == "weather":
            st.markdown("### 🌤️ Weather Information")
            # Display weather data
            
        elif tool_used == "spotify":
            st.markdown("### 🎵 Music Results")
            # Display music results
            
        elif tool_used == "rag":
            st.markdown("### 📚 Documentation")
            # Display RAG results
        
        # Show formatted response
        st.markdown("### 💬 Response")
        st.info(result["formatted_response"])
```

#### Step 4.2: Add Tool Selection Override

```python
# Let users manually select a tool
tool_override = st.selectbox(
    "Or manually select a tool:",
    ["Auto-detect", "Weather", "Music", "Documentation"]
)

if tool_override != "Auto-detect":
    # Force specific tool
    intent_map = {
        "Weather": "weather",
        "Music": "spotify",
        "Documentation": "rag"
    }
    result = multi_tool_agent.invoke({
        "question": question,
        "intent": intent_map[tool_override]  # Override classification
    })
```

---

### **Phase 5: Testing & Optimization** (Days 9-10)

#### Step 5.1: Test Cases

```python
# tests/test_multi_tool_routing.py

test_cases = [
    # Weather questions
    ("What's the weather in London?", "weather"),
    ("Is it going to rain today?", "weather"),
    ("Temperature in Tokyo", "weather"),
    
    # Music questions
    ("Play some jazz music", "spotify"),
    ("Find songs by Taylor Swift", "spotify"),
    ("What's trending in music?", "spotify"),
    
    # Documentation questions
    ("How do I use the weather API?", "rag"),
    ("What parameters does the API need?", "rag"),
    ("Explain how to authenticate", "rag"),
]

def test_intent_classification():
    classifier = KeywordIntentClassifier()
    
    for question, expected_intent in test_cases:
        intent, confidence = classifier.classify(question)
        assert intent == expected_intent, f"Failed for: {question}"
```

---

## 🔄 Changes to Original RAG Plan

### **What Stays the Same:**
1. ✅ RAG implementation (Qdrant + OpenAI embeddings)
2. ✅ PDF document processing
3. ✅ Hybrid retrieval system
4. ✅ Vector store setup

### **What Changes:**
1. 🔄 **RAG becomes ONE of multiple tools** (not the main system)
2. 🔄 **LangGraph workflow** - More complex with routing
3. 🔄 **Streamlit UI** - Shows which tool was used
4. ➕ **Add Spotify API** integration
5. ➕ **Add Intent Classifier** module
6. ➕ **Add Tool Registry** for managing tools

---

## 📊 Updated System Flow

```
User Question
     │
     ▼
[Intent Classification]
     │
     ├──→ "weather" → Weather API → Format → Response
     ├──→ "spotify" → Spotify API → Format → Response
     └──→ "rag/docs" → RAG Search → Format → Response
```

---

## 🎯 Implementation Priority

### **Phase 1 (Days 1-4): Core Routing**
- Intent classifier
- Tool registry
- Updated LangGraph
- Testing with Weather API only

### **Phase 2 (Days 5-6): Add Spotify**
- Spotify API integration
- Spotify tool implementation
- Testing with all 3 tools

### **Phase 3 (Days 7-8): RAG Integration**
- Implement RAG as a tool
- PDF processing
- Qdrant setup

### **Phase 4 (Days 9-10): UI & Testing**
- Multi-tool Streamlit interface
- Comprehensive testing
- Optimization

---

## 💡 Key Design Decisions

### **1. When to Use RAG?**

**Option A: RAG as Fallback**
```python
if intent == "unknown" or confidence < 0.7:
    use_rag_tool()
```

**Option B: RAG for Documentation Questions Only**
```python
if intent == "rag" or keywords_match(["how", "what", "explain"]):
    use_rag_tool()
```

**Option C: RAG as Context Provider (Recommended)**
```python
# For ANY question, optionally fetch RAG context
rag_context = get_rag_context(question)

# Then route to appropriate tool
if intent == "weather":
    # Use RAG context + Weather API
    weather_result = call_weather_api()
    enhanced_result = enhance_with_context(weather_result, rag_context)
```

### **2. Intent Classifier Choice**

| Method | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **Keywords** | Fast, free, simple | Less flexible | ✅ Demo |
| **ML Classifier** | Accurate, offline | Training needed | Production v1 |
| **LLM** | Most flexible | Costs $, slower | Production v2 |

**Recommendation for Your Demo:** Start with **Keywords**, upgrade to **LLM** later if needed.

---

## 🔧 Updated Dependencies

```yaml
# Add to environment.yml
dependencies:
  # Existing...
  
  # Spotify API
  - spotipy>=2.23.0          # Spotify API wrapper
  
  # Optional: For ML-based classification
  - scikit-learn>=1.3.0      # For ML classifier
```

---

## 📁 Updated File Structure

```
src/
├── tools/                     # NEW
│   ├── __init__.py
│   ├── intent_classifier.py   # Routes questions to tools
│   ├── tool_registry.py       # Manages all tools
│   ├── weather_tool.py        # Weather tool implementation
│   ├── spotify_tool.py        # Spotify tool implementation
│   └── rag_tool.py            # RAG tool implementation
├── api_clients/
│   ├── weather_client.py      # Existing
│   └── spotify_client.py      # NEW
├── rag/                       # From original RAG plan
│   ├── embeddings.py
│   ├── vector_store.py
│   └── hybrid_retriever.py
├── agent_graph.py            # OLD - Simple parser
├── agent_graph_v2.py         # NEW - Multi-tool routing
└── streamlit_app.py          # Updated for multi-tool
```

---

## 🎬 Quick Start Example

```python
# How to use the multi-tool agent

from src.agent_graph_v2 import multi_tool_agent

# Ask any question
questions = [
    "What's the weather in London?",
    "Play some jazz music",
    "How do I authenticate with the weather API?"
]

for question in questions:
    result = multi_tool_agent.invoke({"question": question})
    
    print(f"Question: {question}")
    print(f"Intent: {result['intent']} ({result['confidence']:.0%})")
    print(f"Response: {result['formatted_response']}")
    print("-" * 50)
```

**Output:**
```
Question: What's the weather in London?
Intent: weather (95%)
Response: The weather in London is 15°C with partly cloudy skies.
--------------------------------------------------
Question: Play some jazz music
Intent: spotify (100%)
Response: Here are some jazz tracks: [list of songs]
--------------------------------------------------
Question: How do I authenticate with the weather API?
Intent: rag (85%)
Response: According to the documentation, you need to...
--------------------------------------------------
```

---

## ✅ Summary

Your system will become:

**Before:** Simple API parser with fuzzy matching
**After:** Intelligent multi-tool agent that can:
- ✅ Call Weather API for weather questions
- ✅ Call Spotify API for music questions
- ✅ Use RAG for documentation/knowledge questions
- ✅ Automatically route based on question intent
- ✅ Provide formatted, context-aware responses

---

## 🚀 Next Steps

1. **Review this plan** - Does this match your vision?
2. **Choose intent classifier** - Keywords or LLM?
3. **Get Spotify API keys** - If you want music functionality
4. **Decide on RAG role** - Fallback? Context provider? Documentation tool?

**Ready to implement? Let me know and I'll start building!** 🎯

