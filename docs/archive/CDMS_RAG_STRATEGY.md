# 🏷️ CDMS Label RAG Strategy

## 🎯 Goal
Configure the RAG tool to specifically retrieve and answer questions about pesticide labels from the **California Department of Pesticide Regulation's Chemical Database Management System (CDMS)**.

**Date Created:** November 18, 2025  
**Status:** 📋 Strategic Planning

---

## 📚 What is CDMS?

**CDMS** = California Department of Pesticide Regulation's **Chemical Database Management System**

### What It Contains:
- 🏷️ **Pesticide Product Labels** - Official EPA-approved labels
- 📋 **Active Ingredients** - Chemical composition details
- ⚠️ **Safety Information** - Hazards, precautions, PPE requirements
- 🌾 **Usage Instructions** - Application rates, crops, timing
- 🚫 **Restrictions** - Legal restrictions, environmental concerns
- 📞 **Registration Info** - Manufacturers, registration numbers

### Why It's Valuable:
- ✅ **Authoritative** - Official regulatory data
- ✅ **Comprehensive** - Thousands of products
- ✅ **Detailed** - Full label information
- ✅ **Legal** - Compliance requirements
- ✅ **Searchable** - Product names, active ingredients, uses

**Website:** https://www.cdpr.ca.gov/

---

## 🤔 Strategic Decision: RAG Tool Purpose

### Current Question:
**What should the RAG tool focus on?**

### Option A: CDMS Labels Only (Recommended)
```
RAG Tool = Pesticide Label Database
- Focus: CDMS pesticide labels
- Content: Product labels, safety data, usage instructions
- Source: Curated CDMS label collection
- Tavily: Used for general agriculture questions
```

**Pros:**
- ✅ Clear, focused purpose
- ✅ High-quality, authoritative data
- ✅ Answers regulatory/compliance questions
- ✅ Legal accuracy

**Cons:**
- ⚠️ Narrow scope (only pesticides)
- ⚠️ Need to populate database with labels

---

### Option B: Hybrid Agriculture + CDMS
```
RAG Tool = Agriculture Knowledge Base
- Focus: General agriculture + CDMS labels
- Content: Farming practices + pesticide labels
- Source: Mixed PDFs (agriculture + CDMS)
- Tavily: Used for current events/news
```

**Pros:**
- ✅ Broader knowledge base
- ✅ Can answer various agriculture questions
- ✅ More versatile

**Cons:**
- ⚠️ Less focused
- ⚠️ May dilute label search quality
- ⚠️ Harder to maintain quality

---

### Option C: Separate Tools
```
RAG Tool #1 = CDMS Labels (pesticide-specific)
RAG Tool #2 = General Agriculture
Web Search Tool = Tavily (current info)
```

**Pros:**
- ✅ Crystal clear separation
- ✅ Optimal for each use case
- ✅ Easy to debug/maintain

**Cons:**
- ⚠️ More complex architecture
- ⚠️ Need to update tool matcher
- ⚠️ More files to manage

---

## 🎯 Recommended Strategy: Option A + Tavily

### Architecture:
```
User Query
    ↓
Tool Matcher
    ↓
    ├─→ Weather Tool → OpenWeatherMap (current weather)
    ├─→ Soil Tool → USDA API (soil data)
    ├─→ RAG Tool → Qdrant (CDMS pesticide labels)
    └─→ Web Search Tool → Tavily (general agriculture, current events)
```

### Division of Labor:

| Question Type | Tool | Source |
|---------------|------|--------|
| "What's on the label for Roundup?" | RAG | CDMS labels in Qdrant |
| "Safety precautions for glyphosate?" | RAG | CDMS labels in Qdrant |
| "Application rate for 2,4-D?" | RAG | CDMS labels in Qdrant |
| "What are pesticides?" | Web Search | Tavily |
| "Latest pesticide regulations?" | Web Search | Tavily |
| "Organic farming practices?" | Web Search | Tavily |
| "Weather in Iowa?" | Weather | OpenWeatherMap |
| "Soil data for California?" | Soil | USDA |

**Clean separation of concerns!**

---

## 📋 Implementation Plan

### Phase 1: Assess Current RAG Setup (30 min)

#### Step 1.1: Check Existing PDFs
```bash
# What's currently in your vector database?
ls -la data/pdfs/  # or wherever PDFs are stored
```

**Questions:**
- What PDFs are currently loaded?
- Are they agriculture-focused or CDMS labels?
- How many documents?

#### Step 1.2: Check Qdrant Collection
```python
# What's in Qdrant now?
from qdrant_client import QdrantClient
client = QdrantClient(host="localhost", port=6333)
collections = client.get_collections()
# Check collection size, content
```

---

### Phase 2: Acquire CDMS Label Data (varies)

#### Option 2A: Download CDMS Labels Manually
**If you have specific products:**
1. Visit https://www.cdpr.ca.gov/
2. Search for products (e.g., "Roundup", "glyphosate")
3. Download PDF labels
4. Save to `data/cdms_labels/`

**Pros:**
- ✅ Full control over which labels
- ✅ Curated collection
- ✅ High quality

**Cons:**
- ⚠️ Manual process
- ⚠️ Time-consuming for many labels
- ⚠️ Need to update manually

---

#### Option 2B: CDMS API/Database Access
**If CDMS provides API or bulk download:**

Research if CDMS offers:
- Public API for label retrieval
- Bulk download option
- Database export

**Pros:**
- ✅ Automated
- ✅ Comprehensive
- ✅ Can update regularly

**Cons:**
- ⚠️ May require registration
- ⚠️ Need to check terms of use
- ⚠️ API may not exist

---

#### Option 2C: Web Scraping CDMS
**Automated label collection:**

```python
# Example scraper structure
def scrape_cdms_labels(product_names):
    for product in product_names:
        # Search CDMS
        # Download PDF
        # Save to data/cdms_labels/
```

**Pros:**
- ✅ Can get many labels
- ✅ Automated process
- ✅ Customizable

**Cons:**
- ⚠️ May violate terms of service
- ⚠️ Website changes break scraper
- ⚠️ Ethical/legal concerns

**Check CDMS terms of service first!**

---

#### Option 2D: Use Tavily for CDMS Labels
**Search for labels online when needed:**

```python
# Real-time label lookup
query = "CDMS label for Roundup glyphosate"
results = tavily.search(query)
# Returns: Links to CDMS labels
```

**Pros:**
- ✅ No storage needed
- ✅ Always current
- ✅ No manual downloads

**Cons:**
- ⚠️ Slower (API call each time)
- ⚠️ Costs per search
- ⚠️ Dependent on Tavily finding labels

---

### Recommended: 2A + 2D Hybrid
1. **Download top ~100 common pesticide labels** (manual)
2. **Use Tavily for rare/new products** (automated)

---

### Phase 3: Populate Qdrant with CDMS Labels (1-2 hours)

#### Step 3.1: Organize Label Files
```bash
data/
├── cdms_labels/
│   ├── herbicides/
│   │   ├── roundup_label.pdf
│   │   ├── 24d_label.pdf
│   │   └── atrazine_label.pdf
│   ├── insecticides/
│   │   ├── permethrin_label.pdf
│   │   └── malathion_label.pdf
│   └── fungicides/
│       └── chlorothalonil_label.pdf
└── metadata.json  # Track label info
```

#### Step 3.2: Create Label Metadata
```json
{
  "roundup_label.pdf": {
    "product_name": "Roundup PowerMax",
    "active_ingredient": "glyphosate",
    "epa_reg_number": "524-549",
    "manufacturer": "Bayer",
    "category": "herbicide",
    "crops": ["corn", "soybean", "wheat"],
    "cdms_url": "https://..."
  }
}
```

#### Step 3.3: Process Labels into Qdrant
```python
# Use existing PDF ingestion pipeline
from src.data.pdf_processor import process_pdfs

# Process CDMS labels
process_pdfs(
    pdf_directory="data/cdms_labels/",
    collection_name="cdms_pesticide_labels",
    metadata_file="data/metadata.json"
)
```

**What this does:**
1. Reads PDF labels
2. Chunks into searchable segments
3. Creates embeddings
4. Stores in Qdrant with metadata
5. Enables semantic search

---

### Phase 4: Update RAG Tool (1 hour)

#### Step 4.1: Focus RAG on CDMS
**File:** `src/tools/rag_tool.py`

**Update collection name:**
```python
# Before
COLLECTION_NAME = "agriculture_docs"

# After
COLLECTION_NAME = "cdms_pesticide_labels"
```

**Update documentation:**
```python
"""
RAG Tool - CDMS Pesticide Label Database

Searches California Department of Pesticide Regulation's
Chemical Database for pesticide product labels.

Use for:
- Product label information
- Safety precautions
- Application instructions
- Active ingredients
- Regulatory compliance

Examples:
- "What's on the Roundup label?"
- "Safety info for glyphosate?"
- "Application rate for 2,4-D on corn?"
"""
```

#### Step 4.2: Add Label-Specific Formatting
```python
def format_label_response(qdrant_results):
    """Format CDMS label results"""
    
    formatted = {
        "success": True,
        "source": "CDMS Pesticide Labels",
        "products": []
    }
    
    for result in qdrant_results:
        product = {
            "product_name": result.metadata.get("product_name"),
            "active_ingredient": result.metadata.get("active_ingredient"),
            "epa_number": result.metadata.get("epa_reg_number"),
            "content": result.text,
            "relevance": result.score
        }
        formatted["products"].append(product)
    
    return formatted
```

---

### Phase 5: Add Web Search Tool (1-2 hours)

#### Step 5.1: Create Tavily Client
**File:** `src/api_clients/tavily_client.py`

```python
from tavily import TavilyClient as TavilySDK

class TavilyClient:
    """
    Tavily Web Search Client
    
    For general agriculture questions and current information
    """
    
    def __init__(self, api_key: str):
        self.client = TavilySDK(api_key=api_key)
    
    def search(self, query: str, max_results: int = 5):
        """Search the web"""
        try:
            results = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced"  # More thorough
            )
            
            return {
                "success": True,
                "results": results.get("results", []),
                "answer": results.get("answer", "")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

#### Step 5.2: Create Web Search Tool
**File:** `src/tools/web_search_tool.py`

```python
def execute_web_search_tool(question: str):
    """
    Execute web search for general agriculture questions
    
    Use for:
    - General agriculture information
    - Current events/news
    - Topics not in CDMS labels
    - Latest research/regulations
    """
    try:
        from src.api_clients.tavily_client import TavilyClient
        from src.config.credentials import CredentialsManager
        
        # Get API key
        creds = CredentialsManager()
        api_key = creds.get_api_key("tavily")
        
        if not api_key:
            return {
                "success": False,
                "error": "Tavily API key not configured"
            }
        
        # Search
        client = TavilyClient(api_key=api_key)
        results = client.search(question, max_results=5)
        
        if not results["success"]:
            return results
        
        # Format for LLM
        return {
            "success": True,
            "tool": "web_search",
            "query": question,
            "data": {
                "answer": results.get("answer"),
                "sources": results.get("results", [])
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "tool": "web_search",
            "error": str(e)
        }
```

---

### Phase 6: Update Tool Matcher (30 min)

#### Step 6.1: Add Keywords
**File:** `src/tools/tool_matcher.py`

```python
TOOL_KEYWORDS = {
    "weather": ["weather", "temperature", "rain", "forecast", ...],
    "soil": ["soil", "clay", "sand", "pH", "organic matter", ...],
    
    # RAG = CDMS Labels (pesticide-specific)
    "rag": [
        "label", "pesticide", "herbicide", "insecticide", "fungicide",
        "active ingredient", "application rate", "safety", "precaution",
        "EPA", "registration", "manufacturer", "product name",
        "glyphosate", "2,4-D", "atrazine", "permethrin",  # Common pesticides
        "Roundup", "Weed-B-Gon", "Sevin",  # Common brands
    ],
    
    # Web Search = General agriculture
    "web_search": [
        "agriculture", "farming", "crop", "organic", "sustainable",
        "latest", "current", "recent", "news", "research",
        "what are", "how to", "explain", "general",
    ]
}
```

#### Step 6.2: Scoring Logic
```python
def match_tool(keywords, query):
    """Match query to appropriate tool"""
    
    # Check for specific label requests
    if any(word in query.lower() for word in ["label", "epa", "registration"]):
        return {"tool_name": "rag", "confidence": 0.95}
    
    # Check for specific pesticides/products
    pesticide_names = ["roundup", "glyphosate", "2,4-d", "atrazine", ...]
    if any(pest in query.lower() for pest in pesticide_names):
        return {"tool_name": "rag", "confidence": 0.90}
    
    # Check for general questions (use web search)
    if query.lower().startswith(("what are", "what is", "explain", "tell me about")):
        return {"tool_name": "web_search", "confidence": 0.85}
    
    # Default scoring...
```

---

### Phase 7: Update Tool Executor (15 min)

**File:** `src/tools/tool_executor.py`

```python
def execute(self, tool_name: str, user_question: str):
    """Execute the selected tool"""
    
    if tool_name == "weather":
        from src.tools.weather_tool import execute_weather_tool
        return execute_weather_tool(user_question)
    
    elif tool_name == "soil":
        from src.tools.soil_tool import execute_soil_tool
        return execute_soil_tool(user_question)
    
    elif tool_name == "rag":
        # CDMS Pesticide Labels
        from src.tools.rag_tool import execute_rag_tool
        return execute_rag_tool(user_question)
    
    elif tool_name == "web_search":  # NEW
        from src.tools.web_search_tool import execute_web_search_tool
        return execute_web_search_tool(user_question)
    
    else:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }
```

---

### Phase 8: Update UI (30 min)

#### Step 8.1: Update Example Queries
**File:** `src/streamlit_app_conversational.py`

```python
with st.expander("💡 Example Questions", expanded=False):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🌤️ Weather**")
        if st.button("Weather Example"):
            st.session_state.example = "What's the weather in London?"
    
    with col2:
        st.markdown("**🌱 Soil Data**")
        if st.button("Soil Example"):
            st.session_state.example = "Show me soil data for Iowa"
    
    with col3:
        st.markdown("**🏷️ Pesticide Labels**")
        if st.button("Label Example"):
            st.session_state.example = "What's on the Roundup label?"
    
    # Second row
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.markdown("**🌐 Web Search**")
        if st.button("Web Search"):
            st.session_state.example = "What are pesticides?"
    
    with col5:
        st.markdown("**⚠️ Safety Info**")
        if st.button("Safety"):
            st.session_state.example = "Safety precautions for glyphosate?"
    
    with col6:
        st.markdown("**📏 Application**")
        if st.button("Application"):
            st.session_state.example = "Application rate for 2,4-D on corn?"
```

#### Step 8.2: Update Description
```python
st.markdown(
    '<div class="subtitle">Ask me about weather, soil data, pesticide labels (CDMS), or general agriculture information!</div>',
    unsafe_allow_html=True
)
```

---

## 📊 Query Routing Examples

### Queries → Tools Mapping:

| User Query | Tool Selected | Reason |
|------------|---------------|--------|
| "What's on the Roundup label?" | RAG | Specific product label |
| "Safety info for glyphosate?" | RAG | Pesticide safety = label info |
| "Application rate for 2,4-D?" | RAG | Application = label info |
| "What are pesticides?" | Web Search | General knowledge question |
| "Latest pesticide regulations?" | Web Search | "Latest" = current info |
| "Organic farming practices?" | Web Search | General agriculture, not labels |
| "Weather in Iowa?" | Weather | Weather keyword |
| "Soil data for California?" | Soil | Soil keyword |
| "EPA registration for Sevin?" | RAG | EPA + product name = label |
| "How to apply herbicides?" | Web Search | General "how to" |

---

## 🎯 Success Criteria

### For RAG Tool (CDMS Labels):
- [ ] Qdrant collection contains CDMS labels
- [ ] Can retrieve label information by product name
- [ ] Can retrieve by active ingredient
- [ ] Returns EPA numbers and safety info
- [ ] Includes manufacturer details
- [ ] Response time < 2 seconds

### For Web Search Tool:
- [ ] Tavily API configured
- [ ] Returns results for general questions
- [ ] Includes source citations
- [ ] Handles current events queries
- [ ] Response time < 4 seconds

### For Tool Matching:
- [ ] Correctly routes label queries to RAG
- [ ] Correctly routes general queries to web search
- [ ] High confidence scores (>0.8) for clear queries
- [ ] No mis-routing between tools

---

## 💰 Cost Estimate

### One-Time Setup:
- **Time:** 6-8 hours
- **Cost:** $0 (assuming free tiers)

### Ongoing Costs:
- **Qdrant:** FREE (self-hosted Docker)
- **Tavily:** FREE tier (1,000 searches/month)
- **OpenAI:** ~$0.002 per query (LLM responses)

### If You Exceed Free Tiers:
- **Tavily:** $1 per 1,000 searches
- **Total:** ~$5-10/month for moderate use

**Very affordable!**

---

## 🚀 Quick Start Checklist

### Immediate Actions:
1. [ ] Decide: Which CDMS labels do you need?
2. [ ] Check: Do you already have CDMS PDFs?
3. [ ] Get: Tavily API key (https://tavily.com)
4. [ ] Review: Current Qdrant collection content

### Next Steps:
1. [ ] Download priority CDMS labels
2. [ ] Process labels into Qdrant
3. [ ] Update RAG tool for labels
4. [ ] Implement Tavily web search
5. [ ] Update tool matcher
6. [ ] Test with example queries

---

## 📋 Questions to Answer

Before implementing, clarify:

1. **Label Collection:**
   - Do you already have CDMS label PDFs?
   - Which pesticides are priority? (top 10? 50? 100?)
   - Categories needed? (herbicides, insecticides, both?)

2. **Current RAG Content:**
   - What's currently in your Qdrant database?
   - Is it agriculture docs or something else?
   - Should we keep it or replace with labels?

3. **Implementation Approach:**
   - Manual label downloads or automated?
   - Tavily as primary for non-label questions?
   - Hybrid RAG (labels + web search) or separate?

4. **Scope:**
   - Just CDMS or other pesticide databases too?
   - US only or international products?
   - Current products or historical too?

---

## 🎉 Recommended Final Architecture

```
Agentic AI Assistant
    ↓
User: "What's on the Roundup label?"
    ↓
Tool Matcher → "rag" (high confidence: 0.95)
    ↓
RAG Tool → Searches Qdrant "cdms_pesticide_labels"
    ↓
Returns: Roundup label excerpt with EPA number, safety info, application rates
    ↓
LLM: Formats natural response with citations


User: "What are pesticides?"
    ↓
Tool Matcher → "web_search" (high confidence: 0.90)
    ↓
Web Search Tool → Calls Tavily API
    ↓
Returns: General pesticide information from web sources
    ↓
LLM: Formats educational response with citations
```

**Clean, focused, and effective!**

---

## ✅ Summary

### Recommended Strategy:
1. **RAG Tool** = CDMS pesticide labels (focused, authoritative)
2. **Web Search Tool** = General agriculture (broad, current)
3. **Clear routing** = Labels vs. general questions

### Benefits:
- ✅ Specialized label database (high quality)
- ✅ Web search for everything else (comprehensive)
- ✅ Clear tool purposes (easy to maintain)
- ✅ Best tool for each question type

### Next Steps:
1. Answer the clarifying questions above
2. Gather/download CDMS labels
3. Process into Qdrant
4. Implement Tavily integration
5. Update tool matcher
6. Test thoroughly

**Ready to proceed?** Let me know:
- Which labels you need
- What's currently in Qdrant
- Any questions about the approach

I can help with any phase of implementation! 🚀


