# Final Implementation Plan: Weather + Soil + RAG System with Visualization UI

## 🎯 Project Scope (FINALIZED)

Build an intelligent agent system with:
1. ✅ **Weather API** - Get weather data for any location
2. ✅ **Soil Data API** - Get soil information for agricultural use
3. ✅ **RAG System** - Search documentation and knowledge base (PDFs)
4. ✅ **Visualization UI** - Interactive dashboard to display all data

---

## 🏗️ System Architecture (Conversational NLP Interface)

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INPUT (Natural Language)                 │
│   "What's the weather in Iowa?"                                  │
│   "Show me soil data for California"                             │
│   "How do I use the weather API?"                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PARSER & KEYWORD EXTRACTOR                     │
│  - Extract keywords: ["weather", "Iowa"]                         │
│  - Extract keywords: ["soil", "data", "California"]              │
│  - Extract keywords: ["how", "use", "API"]                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TOOL MATCHING ENGINE                          │
│  - Match keywords to tool catalog                                │
│  - Score each tool based on keyword overlap                      │
│  - Select best matching tool                                     │
│                                                                  │
│  Weather Tool: Score 95% (keywords: weather, temperature...)    │
│  Soil Tool:    Score 90% (keywords: soil, agriculture...)       │
│  RAG Tool:     Score 85% (keywords: how, documentation...)      │
└────────────────────────────┬────────────────────────────────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ Weather Tool │  │  Soil Tool   │  │   RAG Tool   │
    │ (API Call)   │  │  (API Call)  │  │ (Doc Search) │
    └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
           │                 │                  │
           └────────────┬────┴──────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              NATURAL LANGUAGE RESPONSE GENERATOR                 │
│  - Format tool results into natural language                     │
│  - Add context and explanation                                   │
│  - Make response conversational                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                OUTPUT (Natural Language Response)                │
│                                                                  │
│  "The current weather in Iowa is 18°C with clear skies.         │
│   Humidity is at 65% and wind speed is 5 m/s."                  │
│                                                                  │
│  Tool Used: Weather API ✓                                       │
│  Keywords Matched: weather, Iowa                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Technology Stack

### APIs & Data:
- **Weather**: OpenWeatherMap API ✅ (you have this)
- **Soil**: SoilGrids API or USDA Soil API (free)
- **RAG**: Qdrant + OpenAI Embeddings

### Visualization:
- **Streamlit** - Main framework
- **Plotly** - Interactive charts
- **Folium/Pydeck** - Maps
- **Pandas** - Data processing

### Backend:
- **LangGraph** - Agent orchestration
- **Python** - Core logic

---

## 🚀 Implementation Phases

### **Phase 1: Soil API Integration** (Days 1-2)

#### Step 1.1: Choose Soil Data API

**Option A: SoilGrids API (Recommended)**
- Free, global coverage
- Soil properties at any location
- REST API
- URL: https://rest.isric.org/soilgrids/v2.0/docs

**Option B: USDA Soil Data Access API**
- Detailed US soil data
- Free for US locations
- URL: https://sdmdataaccess.nrcs.usda.gov/

**For this plan, we'll use SoilGrids (global coverage)**

#### Step 1.2: Create Soil Client (`src/api_clients/soil_client.py`)

```python
from src.api_clients.base_client import BaseAPIClient
import requests

class SoilClient(BaseAPIClient):
    """
    SoilGrids API Client
    Provides soil data: pH, organic carbon, nutrients, texture
    """
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://rest.isric.org/soilgrids/v2.0"
        self.timeout = 30
    
    def get_soil_data(self, lat: float, lon: float) -> dict:
        """
        Get soil properties for a location
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            dict with soil properties
        """
        endpoint = f"{self.base_url}/properties/query"
        
        params = {
            "lon": lon,
            "lat": lat,
            "property": [
                "phh2o",      # pH
                "soc",        # Soil organic carbon
                "nitrogen",   # Nitrogen
                "clay",       # Clay content
                "sand",       # Sand content
                "silt"        # Silt content
            ],
            "depth": "0-5cm",  # Top soil layer
            "value": "mean"
        }
        
        try:
            response = requests.get(
                endpoint,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            return self._format_soil_data(data, lat, lon)
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_soil_data(self, raw_data: dict, lat: float, lon: float) -> dict:
        """Format soil data for display"""
        properties = raw_data.get("properties", {})
        
        formatted = {
            "success": True,
            "location": {"lat": lat, "lon": lon},
            "properties": {}
        }
        
        # Extract and format each property
        for prop_name, layers in properties.items():
            if layers and "layers" in layers:
                # Get first layer (0-5cm)
                value = layers["layers"][0]["values"].get("mean")
                formatted["properties"][prop_name] = {
                    "value": value,
                    "unit": layers.get("unit", ""),
                    "label": self._get_property_label(prop_name)
                }
        
        return formatted
    
    def _get_property_label(self, prop_name: str) -> str:
        """Get human-readable label for property"""
        labels = {
            "phh2o": "pH Level",
            "soc": "Organic Carbon",
            "nitrogen": "Nitrogen Content",
            "clay": "Clay Content",
            "sand": "Sand Content",
            "silt": "Silt Content"
        }
        return labels.get(prop_name, prop_name)
    
    def get_soil_by_location_name(self, location: str) -> dict:
        """
        Get soil data by location name
        First geocodes location, then fetches soil data
        """
        # Use geocoding to get coordinates
        coords = self._geocode_location(location)
        
        if not coords:
            return {
                "success": False,
                "error": f"Could not geocode location: {location}"
            }
        
        return self.get_soil_data(coords["lat"], coords["lon"])
    
    def _geocode_location(self, location: str) -> dict:
        """Convert location name to coordinates using OpenWeatherMap Geocoding"""
        # Reuse OpenWeatherMap's geocoding
        from src.config.credentials import CredentialsManager
        creds = CredentialsManager()
        api_key = creds.get_api_key("openweather")
        
        url = "http://api.openweathermap.org/geo/1.0/direct"
        params = {"q": location, "limit": 1, "appid": api_key}
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data:
                return {"lat": data[0]["lat"], "lon": data[0]["lon"]}
            return None
        except:
            return None
```

#### Step 1.3: Add Soil API to Catalog

```json
{
  "name": "get_soil_data",
  "description": "Get soil properties including pH, nutrients, and composition for any location",
  "tags": ["soil", "agriculture", "nutrients", "pH", "farming"],
  "keywords": ["soil", "agriculture", "farming", "nutrients", "pH", "clay", "sand"],
  "api_type": "soil",
  "endpoint": "https://rest.isric.org/soilgrids/v2.0",
  "method": "GET",
  "auth_type": "none",
  "required_params": ["location or coordinates"],
  "rate_limit": "100/minute",
  "cost": "free",
  "enabled": true
}
```

#### Step 1.4: Create Parameter Extractor for Soil

Update `src/utils/parameter_extractor.py`:

```python
def extract_location_from_soil_query(query: str) -> dict:
    """
    Extract location from soil-related queries
    Returns: {"location": "place name"} or {"lat": x, "lon": y}
    """
    # Similar to weather extraction
    # Look for: "soil in Iowa", "soil data for California"
    patterns = [
        r"soil (?:in|for|at|near) ([A-Z][a-zA-Z\s]+)",
        r"(?:soil|agriculture) data (?:in|for) ([A-Z][a-zA-Z\s]+)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            return {"location": match.group(1).strip()}
    
    # Fallback: use NER
    doc = nlp(query)
    for ent in doc.ents:
        if ent.label_ == "GPE":
            return {"location": ent.text}
    
    return None
```

---

### **Phase 2: Intent Classifier & Tool Registry** (Days 3-4)

#### Step 2.1: Create Intent Classifier (`src/tools/intent_classifier.py`)

```python
import re
from typing import Tuple

class IntentClassifier:
    """Classify user questions into: weather, soil, or documentation"""
    
    def __init__(self):
        self.patterns = {
            "weather": [
                r"\b(weather|temperature|forecast|climate|rain|sunny|cloudy|wind)\b",
                r"\b(hot|cold|warm|humid|degrees|celsius|fahrenheit)\b",
                r"\b(precipitation|humidity|pressure)\b"
            ],
            "soil": [
                r"\b(soil|agriculture|farming|crop|nutrient|pH|fertility)\b",
                r"\b(clay|sand|silt|organic carbon|nitrogen)\b",
                r"\b(plant|grow|harvest|agricultural)\b"
            ],
            "documentation": [
                r"\b(how to|how do|what is|explain|documentation|docs|guide)\b",
                r"\b(api|tutorial|help|instructions|example)\b",
                r"\b(tell me about|information about|show me how)\b"
            ]
        }
    
    def classify(self, question: str) -> Tuple[str, float]:
        """
        Classify the intent
        Returns: (intent, confidence_score)
        """
        question_lower = question.lower()
        scores = {"weather": 0, "soil": 0, "documentation": 0}
        
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, question_lower):
                    scores[intent] += 1
        
        # Get highest scoring intent
        max_score = max(scores.values())
        
        if max_score > 0:
            best_intent = max(scores, key=scores.get)
            confidence = min(max_score / 2, 1.0)  # Normalize
            return best_intent, confidence
        
        # Default to documentation for general questions
        return "documentation", 0.5
```

#### Step 2.2: Create Tool Implementations

**Weather Tool (`src/tools/weather_tool.py`)**
```python
from src.api_clients.weather_client import WeatherClient
from src.utils.parameter_extractor import extract_city_from_query

def execute_weather_tool(question: str) -> dict:
    """Get weather data"""
    city = extract_city_from_query(question)
    
    if not city:
        return {"success": False, "error": "Could not extract location"}
    
    client = WeatherClient()
    result = client.get_weather(city=city)
    
    return {
        "success": True,
        "tool": "weather",
        "data": result
    }
```

**Soil Tool (`src/tools/soil_tool.py`)**
```python
from src.api_clients.soil_client import SoilClient
from src.utils.parameter_extractor import extract_location_from_soil_query

def execute_soil_tool(question: str) -> dict:
    """Get soil data"""
    location_info = extract_location_from_soil_query(question)
    
    if not location_info:
        return {"success": False, "error": "Could not extract location"}
    
    client = SoilClient()
    
    if "location" in location_info:
        result = client.get_soil_by_location_name(location_info["location"])
    else:
        result = client.get_soil_data(
            lat=location_info["lat"],
            lon=location_info["lon"]
        )
    
    return {
        "success": True,
        "tool": "soil",
        "data": result
    }
```

**RAG Tool (`src/tools/rag_tool.py`)**
```python
from src.rag.hybrid_retriever import HybridRetriever

def execute_rag_tool(question: str) -> dict:
    """Search documentation"""
    retriever = HybridRetriever()
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

### **Phase 3: LangGraph Agent** (Day 5)

#### Step 3.1: Create Multi-Tool Agent (`src/agent_graph_multi_tool.py`)

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from src.tools.intent_classifier import IntentClassifier
from src.tools.weather_tool import execute_weather_tool
from src.tools.soil_tool import execute_soil_tool
from src.tools.rag_tool import execute_rag_tool

class AgentState(TypedDict):
    question: str
    intent: str
    confidence: float
    tool_result: dict
    formatted_response: str

# Initialize classifier
classifier = IntentClassifier()

def classify_node(state: AgentState):
    """Classify user intent"""
    question = state["question"]
    intent, confidence = classifier.classify(question)
    return {"intent": intent, "confidence": confidence}

def route_to_tool(state: AgentState):
    """Route based on intent"""
    intent = state["intent"]
    question = state["question"]
    
    tool_map = {
        "weather": execute_weather_tool,
        "soil": execute_soil_tool,
        "documentation": execute_rag_tool
    }
    
    tool_fn = tool_map.get(intent, execute_rag_tool)
    result = tool_fn(question)
    
    return {"tool_result": result}

def format_response(state: AgentState):
    """Format final response"""
    result = state["tool_result"]
    intent = state["intent"]
    
    if not result.get("success"):
        response = f"Error: {result.get('error')}"
    elif intent == "weather":
        response = format_weather_response(result["data"])
    elif intent == "soil":
        response = format_soil_response(result["data"])
    else:
        response = format_rag_response(result["data"])
    
    return {"formatted_response": response}

# Build graph
builder = StateGraph(AgentState)
builder.add_node("classify", classify_node)
builder.add_node("execute", route_to_tool)
builder.add_node("format", format_response)

builder.add_edge(START, "classify")
builder.add_edge("classify", "execute")
builder.add_edge("execute", "format")
builder.add_edge("format", END)

multi_tool_agent = builder.compile()
```

---

### **Phase 4: RAG Implementation** (Days 6-8)

Follow the original **HYBRID_RAG_IMPLEMENTATION_PLAN.md**, but focused on:
- PDF document processing
- Qdrant setup
- OpenAI embeddings
- Hybrid retrieval

(Details already in HYBRID_RAG_IMPLEMENTATION_PLAN.md)

---

### **Phase 5: Conversational NLP UI** (Days 9-12) ⭐ **KEY COMPONENT**

#### Step 5.1: Simple Conversational Interface (`src/streamlit_app_conversational.py`)

```python
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src.agent_graph_multi_tool import multi_tool_agent

# Page config
st.set_page_config(
    page_title="Agriculture Intelligence Dashboard",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .big-font {font-size:30px !important; font-weight:bold;}
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=AgriAI", use_column_width=True)
    st.title("🌾 AgriIntel Dashboard")
    
    st.markdown("---")
    
    # Tool selector
    tool_mode = st.radio(
        "Select Tool:",
        ["🤖 Auto-Detect", "🌤️ Weather", "🌱 Soil Data", "📚 Documentation"]
    )
    
    st.markdown("---")
    
    # Settings
    st.subheader("⚙️ Settings")
    show_raw_data = st.checkbox("Show Raw Data", value=False)
    show_charts = st.checkbox("Show Charts", value=True)
    show_map = st.checkbox("Show Map", value=True)

# Main content
st.markdown('<p class="big-font">🌾 Agriculture Intelligence System</p>', unsafe_allow_html=True)
st.markdown("Ask about weather, soil data, or search our documentation!")

# Input section
col1, col2 = st.columns([3, 1])
with col1:
    user_question = st.text_input(
        "Ask your question:",
        placeholder="e.g., What's the weather in Iowa? or Show soil data for California",
        label_visibility="collapsed"
    )
with col2:
    ask_button = st.button("🔍 Ask", type="primary", use_container_width=True)

# Process query
if ask_button and user_question:
    with st.spinner("🤔 Processing your question..."):
        # Override intent if manual selection
        if tool_mode != "🤖 Auto-Detect":
            intent_map = {
                "🌤️ Weather": "weather",
                "🌱 Soil Data": "soil",
                "📚 Documentation": "documentation"
            }
            # Would need to modify agent to accept intent override
        
        # Execute agent
        result = multi_tool_agent.invoke({"question": user_question})
        
        # Store in session state
        st.session_state.last_result = result

# Display results
if "last_result" in st.session_state:
    result = st.session_state.last_result
    
    # Intent badge
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🎯 Detected Intent", result["intent"].title())
    with col2:
        st.metric("💯 Confidence", f"{result['confidence']:.0%}")
    with col3:
        tool_icon = {"weather": "🌤️", "soil": "🌱", "documentation": "📚"}
        st.metric("🔧 Tool Used", tool_icon.get(result["intent"], "❓"))
    
    st.markdown("---")
    
    # Tool-specific visualization
    tool = result["tool_result"].get("tool")
    data = result["tool_result"].get("data", {})
    
    if tool == "weather" and data.get("success"):
        display_weather_visualization(data)
    
    elif tool == "soil" and data.get("success"):
        display_soil_visualization(data)
    
    elif tool == "rag":
        display_rag_visualization(data)
    
    # Show raw data if enabled
    if show_raw_data:
        with st.expander("🔍 View Raw Data"):
            st.json(result)

# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def display_weather_visualization(data):
    """Display weather data with visualizations"""
    st.subheader("🌤️ Weather Information")
    
    # Extract data
    temp = data.get("temperature", 0)
    feels_like = data.get("feels_like", 0)
    humidity = data.get("humidity", 0)
    wind_speed = data.get("wind_speed", 0)
    description = data.get("description", "N/A")
    city = data.get("city", "Unknown")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🌡️ Temperature",
            f"{temp}°C",
            f"{temp - feels_like:+.1f}°C feels"
        )
    
    with col2:
        st.metric("💧 Humidity", f"{humidity}%")
    
    with col3:
        st.metric("💨 Wind Speed", f"{wind_speed} m/s")
    
    with col4:
        st.metric("☁️ Conditions", description.title())
    
    # Gauges for metrics
    if show_charts:
        col1, col2 = st.columns(2)
        
        with col1:
            # Temperature gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=temp,
                title={'text': "Temperature (°C)"},
                gauge={
                    'axis': {'range': [-20, 50]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [-20, 0], 'color': "lightblue"},
                        {'range': [0, 20], 'color': "lightyellow"},
                        {'range': [20, 50], 'color': "lightcoral"}
                    ],
                }
            ))
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Humidity gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=humidity,
                title={'text': "Humidity (%)"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkgreen"},
                    'steps': [
                        {'range': [0, 30], 'color': "lightyellow"},
                        {'range': [30, 60], 'color': "lightgreen"},
                        {'range': [60, 100], 'color': "lightblue"}
                    ],
                }
            ))
            st.plotly_chart(fig, use_container_width=True)
    
    # Map
    if show_map and "lat" in data and "lon" in data:
        st.subheader("📍 Location")
        map_data = pd.DataFrame({
            'lat': [data["lat"]],
            'lon': [data["lon"]],
            'name': [city]
        })
        st.map(map_data, zoom=5)

def display_soil_visualization(data):
    """Display soil data with visualizations"""
    st.subheader("🌱 Soil Properties")
    
    properties = data.get("properties", {})
    
    if not properties:
        st.warning("No soil data available")
        return
    
    # Metrics cards
    cols = st.columns(len(properties))
    
    for idx, (prop_name, prop_data) in enumerate(properties.items()):
        with cols[idx]:
            value = prop_data.get("value", 0)
            label = prop_data.get("label", prop_name)
            unit = prop_data.get("unit", "")
            
            st.metric(
                f"🌿 {label}",
                f"{value} {unit}"
            )
    
    if show_charts:
        # Soil composition pie chart
        composition_props = ["clay", "sand", "silt"]
        composition_data = {
            prop: properties[prop]["value"]
            for prop in composition_props
            if prop in properties
        }
        
        if composition_data:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Soil Composition")
                fig = px.pie(
                    values=list(composition_data.values()),
                    names=[p.title() for p in composition_data.keys()],
                    title="Soil Texture Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Nutrient Levels")
                # Bar chart for nutrients
                nutrient_props = ["nitrogen", "soc", "phh2o"]
                nutrient_data = {
                    properties[prop]["label"]: properties[prop]["value"]
                    for prop in nutrient_props
                    if prop in properties
                }
                
                fig = px.bar(
                    x=list(nutrient_data.keys()),
                    y=list(nutrient_data.values()),
                    title="Soil Nutrients",
                    labels={"x": "Property", "y": "Value"}
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Map
    if show_map:
        location = data.get("location", {})
        if "lat" in location and "lon" in location:
            st.subheader("📍 Sample Location")
            map_data = pd.DataFrame({
                'lat': [location["lat"]],
                'lon': [location["lon"]]
            })
            st.map(map_data, zoom=5)

def display_rag_visualization(data):
    """Display RAG results"""
    st.subheader("📚 Documentation Search Results")
    
    # API matches
    api_matches = data.get("api_matches", [])
    if api_matches:
        st.markdown("### 🎯 Relevant APIs")
        for api in api_matches[:3]:
            with st.expander(f"📌 {api['api_name']} - {api['score']}% match"):
                st.write(api.get("description", "No description"))
                st.progress(api["score"] / 100)
    
    # Document context
    doc_context = data.get("document_context", [])
    if doc_context:
        st.markdown("### 📄 Relevant Documentation")
        for doc in doc_context[:3]:
            with st.expander(f"📖 {doc['source']} (Page {doc['page']})"):
                st.write(doc["content"])
                st.caption(f"Relevance: {doc['score']:.1%}")
                st.progress(doc["score"])

# ============================================================================
# EXAMPLE QUERIES
# ============================================================================

st.markdown("---")
st.subheader("💡 Example Queries")

example_col1, example_col2, example_col3 = st.columns(3)

with example_col1:
    if st.button("🌤️ Weather in London", use_container_width=True):
        st.session_state.example_query = "What's the weather in London?"

with example_col2:
    if st.button("🌱 Soil data for Iowa", use_container_width=True):
        st.session_state.example_query = "Show me soil data for Iowa"

with example_col3:
    if st.button("📚 API Documentation", use_container_width=True):
        st.session_state.example_query = "How do I use the weather API?"
```

#### Step 5.2: Add Visualization Dependencies

Update `environment.yml`:
```yaml
dependencies:
  # Existing...
  
  # Visualization
  - plotly>=5.17.0           # Interactive charts
  - folium>=0.14.0           # Maps
  - pydeck>=0.8.0            # 3D maps (optional)
  - matplotlib>=3.7.0        # Static plots
  - seaborn>=0.12.0          # Statistical viz
```

---

### **Phase 6: Testing & Integration** (Days 13-14)

#### Step 6.1: Integration Tests

```python
# tests/test_integration.py

def test_weather_flow():
    """Test end-to-end weather query"""
    result = multi_tool_agent.invoke({
        "question": "What's the weather in Paris?"
    })
    
    assert result["intent"] == "weather"
    assert result["tool_result"]["success"] == True
    assert "temperature" in result["tool_result"]["data"]

def test_soil_flow():
    """Test end-to-end soil query"""
    result = multi_tool_agent.invoke({
        "question": "Show soil data for California"
    })
    
    assert result["intent"] == "soil"
    assert result["tool_result"]["success"] == True
    assert "properties" in result["tool_result"]["data"]

def test_rag_flow():
    """Test end-to-end documentation query"""
    result = multi_tool_agent.invoke({
        "question": "How do I authenticate with the API?"
    })
    
    assert result["intent"] == "documentation"
    assert result["tool_result"]["success"] == True
```

---

## 📊 Updated File Structure

```
agentic_ai_project/
├── src/
│   ├── api_clients/
│   │   ├── weather_client.py      ✅ Existing
│   │   ├── soil_client.py         ⭐ NEW
│   │   └── base_client.py         ✅ Existing
│   │
│   ├── tools/                     ⭐ NEW FOLDER
│   │   ├── __init__.py
│   │   ├── intent_classifier.py
│   │   ├── weather_tool.py
│   │   ├── soil_tool.py
│   │   └── rag_tool.py
│   │
│   ├── rag/                       ⭐ NEW (from RAG plan)
│   │   ├── embeddings.py
│   │   ├── vector_store.py
│   │   └── hybrid_retriever.py
│   │
│   ├── cdms/                      ⭐ NEW (from RAG plan)
│   │   ├── pdf_processor.py
│   │   ├── database.py
│   │   └── document_loader.py
│   │
│   ├── agent_graph_multi_tool.py  ⭐ NEW
│   ├── streamlit_app_v2.py        ⭐ NEW (visualization UI)
│   └── api_catalog.json           ✅ Update
│
├── data/
│   ├── pdfs/                      ⭐ NEW (your PDF docs)
│   ├── qdrant_storage/            ⭐ NEW
│   └── cdms_metadata.db           ⭐ NEW
│
├── tests/
│   └── test_integration.py        ⭐ NEW
│
├── FINAL_IMPLEMENTATION_PLAN.md   ⭐ THIS FILE
└── environment.yml                ✅ Update
```

---

## 🎯 Implementation Priority

### **Week 1: Core Functionality**
- Days 1-2: Soil API integration
- Days 3-4: Intent classifier + Tool system
- Day 5: LangGraph agent

### **Week 2: RAG + Visualization**
- Days 6-8: RAG implementation (Qdrant + PDFs)
- Days 9-12: Visualization UI
- Days 13-14: Testing & polish

---

## 💰 Total Cost Estimate

| Component | Cost |
|-----------|------|
| Weather API (OpenWeatherMap) | Free tier |
| Soil API (SoilGrids) | Free |
| Qdrant (Docker local) | Free |
| OpenAI Embeddings | < $0.01 for demo |
| **Total** | **Essentially FREE** |

---

## 🎨 UI Features Summary

### Dashboard Includes:
1. ✅ **Weather Visualization**
   - Temperature gauges
   - Humidity indicators
   - Wind speed metrics
   - Location map
   
2. ✅ **Soil Data Visualization**
   - Pie chart (soil composition)
   - Bar chart (nutrients)
   - Metric cards (pH, carbon, etc.)
   - Sample location map
   
3. ✅ **RAG Results**
   - API match cards with scores
   - Document excerpts with sources
   - Relevance indicators
   
4. ✅ **Interactive Controls**
   - Tool selector (auto/manual)
   - Settings toggles
   - Example queries
   - Raw data viewer

---

## 📋 What You Need to Prepare

1. ✅ **OpenWeatherMap API Key** (you have this)
2. ✅ **OpenAI API Key** (you have this)
3. ⭐ **PDF Documents** (download 5-10 PDFs about):
   - Weather API documentation
   - Soil/agriculture guides
   - Farming best practices
   - Any domain-specific docs
4. ⭐ **Docker** (for Qdrant) - optional, can use in-memory mode

---

## 🚀 Ready to Start?

This plan combines:
- ✅ Weather API (existing)
- ⭐ Soil API (new, free)
- ⭐ RAG with PDFs (new)
- ⭐ Beautiful visualization UI (new)

**All in one cohesive system!**

When you're ready, say **"Let's implement this"** and I'll start building phase by phase! 🎯

