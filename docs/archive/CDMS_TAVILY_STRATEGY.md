# 🏷️ CDMS Label Access via Tavily - Strategic Plan

## 🎯 Goal
Use **Tavily web search** to access CDMS pesticide labels on-demand, avoiding the need to download and store thousands of PDFs locally.

**Date Created:** November 18, 2025  
**Status:** 📋 Strategic Planning

---

## 📊 Situation Analysis

### Constraints:
- ❌ **CDMS database too large** - Can't download all labels
- ❌ **CDMS API unavailable** - No direct API access (yet)
- ✅ **CDMS labels are public** - Available online at cdpr.ca.gov
- ✅ **Tavily can find them** - Web search can locate labels

### Opportunity:
✅ Use **Tavily as a real-time CDMS search engine**
- No storage needed
- Access to entire CDMS database
- Always up-to-date
- Simpler architecture

---

## 🎯 Recommended Architecture

### New Tool Structure:

```
User Query
    ↓
Tool Matcher
    ↓
    ├─→ Weather Tool → OpenWeatherMap
    ├─→ Soil Tool → USDA API
    ├─→ CDMS Label Tool → Tavily (search CDMS specifically)
    └─→ General Agriculture Tool → Tavily (general knowledge)
```

### Key Insight:
**Split Tavily usage into TWO tools with different purposes:**

1. **CDMS Label Tool** (focused)
   - Searches specifically for CDMS labels
   - Optimized queries like "CDMS label Roundup glyphosate"
   - Returns label information

2. **General Agriculture Tool** (broad)
   - General agriculture questions
   - Current events, news, research
   - Not label-specific

---

## 🔍 Strategy: Query Crafting for CDMS

### The Secret: Smart Query Templates

Instead of just passing user query to Tavily, **craft specialized search queries** that target CDMS:

```python
# User asks: "What's on the Roundup label?"

# Bad query:
tavily.search("What's on the Roundup label?")
# → May return general Roundup info, not the label

# Good query:
tavily.search("CDMS California Roundup glyphosate product label EPA")
# → More likely to find official CDMS label

# Even better:
tavily.search("site:cdpr.ca.gov Roundup product label glyphosate")
# → Targets CDMS website specifically (if Tavily supports site: operator)
```

---

## 📋 Implementation Plan

### Phase 1: Test Tavily with CDMS (30 min)

#### Step 1.1: Get Tavily API Key
```bash
# Sign up at https://tavily.com
# Get API key
# Add to .env
TAVILY_API_KEY=tvly-your-key-here
```

#### Step 1.2: Quick Test
```python
from tavily import TavilyClient

client = TavilyClient(api_key="your_key")

# Test 1: General search
result1 = client.search("Roundup label")

# Test 2: Specific CDMS search
result2 = client.search("CDMS California Roundup glyphosate product label")

# Test 3: With site targeting (if supported)
result3 = client.search("site:cdpr.ca.gov Roundup product label")

# Compare which works best
```

**Goal:** Figure out which query format returns CDMS labels most reliably

---

### Phase 2: Create CDMS Label Tool (1-2 hours)

#### Step 2.1: Extract Product Info from Query
**File:** `src/tools/cdms_label_tool.py`

```python
import re
from typing import Dict, Any

def extract_product_info(query: str) -> Dict[str, str]:
    """
    Extract product name and active ingredient from user query
    
    Examples:
        "What's on the Roundup label?" → {"product": "Roundup"}
        "Safety info for glyphosate" → {"ingredient": "glyphosate"}
        "2,4-D application rate" → {"ingredient": "2,4-D", "info_type": "application"}
    """
    info = {}
    
    # Extract product names (capitalize words that might be products)
    # Common products: Roundup, Sevin, Weed-B-Gon, etc.
    products = ["roundup", "sevin", "spectracide", "ortho", "bayer"]
    for product in products:
        if product in query.lower():
            info["product"] = product.title()
    
    # Extract active ingredients
    ingredients = ["glyphosate", "2,4-d", "atrazine", "permethrin", "malathion"]
    for ingredient in ingredients:
        if ingredient in query.lower():
            info["ingredient"] = ingredient
    
    # Extract info type
    if any(word in query.lower() for word in ["safety", "precaution", "hazard"]):
        info["info_type"] = "safety"
    elif any(word in query.lower() for word in ["application", "rate", "use"]):
        info["info_type"] = "application"
    elif any(word in query.lower() for word in ["epa", "registration"]):
        info["info_type"] = "registration"
    
    return info
```

#### Step 2.2: Craft CDMS-Specific Query
```python
def craft_cdms_query(user_query: str, product_info: Dict) -> str:
    """
    Craft optimized Tavily query to find CDMS labels
    
    Strategy:
    1. Include "CDMS" or "California pesticide label"
    2. Include product name or active ingredient
    3. Include "EPA" or "registration" for official docs
    4. Include "site:cdpr.ca.gov" if Tavily supports it
    """
    base_terms = ["CDMS", "California pesticide label"]
    
    query_parts = []
    
    # Add product or ingredient
    if "product" in product_info:
        query_parts.append(product_info["product"])
    if "ingredient" in product_info:
        query_parts.append(product_info["ingredient"])
    
    # Add info type context
    if "info_type" in product_info:
        if product_info["info_type"] == "safety":
            query_parts.append("safety precautions")
        elif product_info["info_type"] == "application":
            query_parts.append("application instructions")
    
    # Add EPA for official docs
    query_parts.append("EPA")
    
    # Combine
    if query_parts:
        optimized_query = f"CDMS California {' '.join(query_parts)} product label"
    else:
        # Fallback to original query with CDMS prefix
        optimized_query = f"CDMS California {user_query}"
    
    return optimized_query
```

#### Step 2.3: Execute Search and Format
```python
def execute_cdms_label_tool(question: str) -> Dict[str, Any]:
    """
    Search for CDMS pesticide labels using Tavily
    
    Args:
        question: User's natural language question
    
    Returns:
        Dict with label information
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
        
        # Extract product info
        product_info = extract_product_info(question)
        
        # Craft optimized query
        search_query = craft_cdms_query(question, product_info)
        
        print(f"🔍 Searching CDMS: {search_query}")
        
        # Search via Tavily
        client = TavilyClient(api_key=api_key)
        results = client.search(
            query=search_query,
            max_results=5,
            search_depth="advanced"  # More thorough
        )
        
        if not results.get("success"):
            return {
                "success": False,
                "error": "Failed to search CDMS labels"
            }
        
        # Format results
        return format_cdms_results(results, question, product_info)
        
    except Exception as e:
        return {
            "success": False,
            "tool": "cdms_label",
            "error": str(e)
        }


def format_cdms_results(tavily_results: Dict, original_question: str, product_info: Dict) -> Dict:
    """Format Tavily results as CDMS label information"""
    
    search_results = tavily_results.get("results", [])
    
    if not search_results:
        return {
            "success": False,
            "error": "No CDMS labels found for this product"
        }
    
    # Extract relevant information
    formatted = {
        "success": True,
        "tool": "cdms_label",
        "source": "CDMS via Tavily Web Search",
        "query": original_question,
        "product_info": product_info,
        "labels": []
    }
    
    for result in search_results:
        label_info = {
            "title": result.get("title", ""),
            "url": result.get("url", ""),
            "content": result.get("content", ""),
            "score": result.get("score", 0)
        }
        
        # Check if result is actually from CDMS
        if "cdpr.ca.gov" in label_info["url"].lower() or "cdms" in label_info["title"].lower():
            label_info["verified_cdms"] = True
        else:
            label_info["verified_cdms"] = False
        
        formatted["labels"].append(label_info)
    
    # Add Tavily's answer if available
    if "answer" in tavily_results:
        formatted["summary"] = tavily_results["answer"]
    
    return formatted
```

---

### Phase 3: Create General Agriculture Tool (30 min)

#### Step 3.1: Simple Web Search Tool
**File:** `src/tools/agriculture_web_tool.py`

```python
def execute_agriculture_web_tool(question: str) -> Dict[str, Any]:
    """
    General agriculture knowledge via web search
    
    Use for:
    - "What are pesticides?"
    - "Latest farming news"
    - "Organic farming practices"
    - Questions not about specific labels
    """
    try:
        from src.api_clients.tavily_client import TavilyClient
        from src.config.credentials import CredentialsManager
        
        creds = CredentialsManager()
        api_key = creds.get_api_key("tavily")
        
        if not api_key:
            return {
                "success": False,
                "error": "Tavily API key not configured"
            }
        
        # Direct search (no query crafting needed)
        client = TavilyClient(api_key=api_key)
        results = client.search(
            query=question,
            max_results=5,
            search_depth="basic"  # Faster for general queries
        )
        
        return {
            "success": True,
            "tool": "agriculture_web",
            "source": "Web Search",
            "data": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "tool": "agriculture_web",
            "error": str(e)
        }
```

---

### Phase 4: Update Tool Matcher (45 min)

#### Step 4.1: Add New Tool Keywords
**File:** `src/tools/tool_matcher.py`

```python
TOOL_KEYWORDS = {
    "weather": [
        "weather", "temperature", "rain", "forecast", "sunny", "cloudy"
    ],
    
    "soil": [
        "soil", "clay", "sand", "silt", "pH", "organic matter", "texture"
    ],
    
    # NEW: CDMS Label Tool (pesticide-specific)
    "cdms_label": [
        "label", "EPA", "registration", "product",
        # Pesticide types
        "herbicide", "insecticide", "fungicide", "pesticide",
        # Common products
        "roundup", "sevin", "spectracide", "ortho", "bayer",
        # Common active ingredients
        "glyphosate", "2,4-d", "atrazine", "permethrin", "malathion",
        "chlorpyrifos", "imidacloprid", "bifenthrin",
        # Label-specific terms
        "safety", "precaution", "application rate", "active ingredient",
        "manufacturer", "hazard", "PPE", "protective equipment"
    ],
    
    # NEW: General Agriculture Tool
    "agriculture_web": [
        "what are", "what is", "explain", "tell me about",
        "agriculture", "farming", "crop", "organic", "sustainable",
        "latest", "current", "recent", "news", "research",
        "how to", "best practices", "guide", "tips"
    ]
}
```

#### Step 4.2: Smart Routing Logic
```python
def match_tool(keywords: list, query: str) -> Dict[str, Any]:
    """
    Match query to appropriate tool with confidence score
    """
    query_lower = query.lower()
    
    # Priority 1: Weather (very specific)
    if any(word in query_lower for word in ["weather", "temperature", "forecast"]):
        return {"tool_name": "weather", "confidence": 0.95}
    
    # Priority 2: Soil (very specific)
    if "soil" in query_lower:
        return {"tool_name": "soil", "confidence": 0.95}
    
    # Priority 3: CDMS Labels (pesticide-specific)
    # Check for label-specific terms
    label_indicators = ["label", "epa", "registration", "safety", "precaution"]
    if any(indicator in query_lower for indicator in label_indicators):
        return {"tool_name": "cdms_label", "confidence": 0.90}
    
    # Check for specific pesticide products
    products = ["roundup", "sevin", "spectracide", "ortho"]
    if any(product in query_lower for product in products):
        return {"tool_name": "cdms_label", "confidence": 0.85}
    
    # Check for active ingredients
    ingredients = ["glyphosate", "2,4-d", "atrazine", "permethrin"]
    if any(ingredient in query_lower for ingredient in ingredients):
        return {"tool_name": "cdms_label", "confidence": 0.85}
    
    # Check for pesticide types with action words
    if any(pest_type in query_lower for pest_type in ["herbicide", "insecticide", "fungicide"]):
        # If asking about a specific product/action → CDMS
        if any(action in query_lower for action in ["use", "apply", "rate", "how much"]):
            return {"tool_name": "cdms_label", "confidence": 0.80}
        # If asking "what is" → General web
        elif query_lower.startswith(("what is", "what are", "explain")):
            return {"tool_name": "agriculture_web", "confidence": 0.85}
    
    # Priority 4: General Agriculture (fallback)
    # Questions starting with "what", "how", "explain"
    if query_lower.startswith(("what", "how", "explain", "tell me")):
        return {"tool_name": "agriculture_web", "confidence": 0.75}
    
    # Default to agriculture web search
    return {"tool_name": "agriculture_web", "confidence": 0.60}
```

---

### Phase 5: Create Tavily Client (30 min)

**File:** `src/api_clients/tavily_client.py`

```python
"""
Tavily Web Search Client
"""

from tavily import TavilyClient as TavilySDK
from typing import Dict, Any, Optional

class TavilyClient:
    """
    Tavily API Client for web search
    
    Used for:
    1. CDMS label searches (optimized queries)
    2. General agriculture questions
    """
    
    def __init__(self, api_key: str):
        """Initialize Tavily client"""
        self.client = TavilySDK(api_key=api_key)
        self.api_key = api_key
    
    def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic"
    ) -> Dict[str, Any]:
        """
        Search the web using Tavily
        
        Args:
            query: Search query
            max_results: Number of results to return (default: 5)
            search_depth: "basic" or "advanced" (default: "basic")
        
        Returns:
            Dict with search results
        """
        try:
            # Call Tavily API
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_answer=True,  # Get Tavily's AI-generated answer
                include_raw_content=False  # Don't need full HTML
            )
            
            return {
                "success": True,
                "query": query,
                "results": response.get("results", []),
                "answer": response.get("answer", ""),
                "response_time": response.get("response_time", 0)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    def search_cdms(self, product: str, info_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Specialized search for CDMS labels
        
        Args:
            product: Product name or active ingredient
            info_type: Type of info needed (safety, application, etc.)
        
        Returns:
            CDMS label search results
        """
        # Craft CDMS-specific query
        query_parts = ["CDMS California", product, "pesticide label EPA"]
        
        if info_type == "safety":
            query_parts.append("safety precautions")
        elif info_type == "application":
            query_parts.append("application instructions rate")
        
        query = " ".join(query_parts)
        
        # Use advanced search for better results
        return self.search(query=query, max_results=5, search_depth="advanced")
```

---

### Phase 6: Update Tool Executor (15 min)

**File:** `src/tools/tool_executor.py`

```python
def execute(self, tool_name: str, user_question: str) -> Dict[str, Any]:
    """Execute the selected tool"""
    
    if tool_name == "weather":
        from src.tools.weather_tool import execute_weather_tool
        return execute_weather_tool(user_question)
    
    elif tool_name == "soil":
        from src.tools.soil_tool import execute_soil_tool
        return execute_soil_tool(user_question)
    
    elif tool_name == "cdms_label":  # NEW
        from src.tools.cdms_label_tool import execute_cdms_label_tool
        return execute_cdms_label_tool(user_question)
    
    elif tool_name == "agriculture_web":  # NEW
        from src.tools.agriculture_web_tool import execute_agriculture_web_tool
        return execute_agriculture_web_tool(user_question)
    
    else:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }
```

---

### Phase 7: Update UI (20 min)

**File:** `src/streamlit_app_conversational.py`

```python
# Update subtitle
st.markdown(
    '<div class="subtitle">Ask me about weather, soil data, pesticide labels (CDMS), or general agriculture!</div>',
    unsafe_allow_html=True
)

# Update example queries
with st.expander("💡 Example Questions", expanded=False):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🌤️ Weather", use_container_width=True):
            st.session_state.example_input = "What's the weather in London?"
    
    with col2:
        if st.button("🌱 Soil Data", use_container_width=True):
            st.session_state.example_input = "Show me soil data for Iowa"
    
    with col3:
        if st.button("🏷️ Product Label", use_container_width=True):
            st.session_state.example_input = "What's on the Roundup label?"
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        if st.button("⚠️ Safety Info", use_container_width=True):
            st.session_state.example_input = "Safety precautions for glyphosate?"
    
    with col5:
        if st.button("📏 Application", use_container_width=True):
            st.session_state.example_input = "Application rate for 2,4-D?"
    
    with col6:
        if st.button("🌐 General Info", use_container_width=True):
            st.session_state.example_input = "What are pesticides?"
```

---

## 📊 Query Routing Examples

| User Query | Tool | Tavily Query | Reason |
|------------|------|--------------|--------|
| "What's on the Roundup label?" | cdms_label | "CDMS California Roundup glyphosate product label EPA" | Specific product |
| "Safety info for glyphosate?" | cdms_label | "CDMS California glyphosate safety precautions EPA" | Ingredient + safety |
| "Application rate for 2,4-D?" | cdms_label | "CDMS California 2,4-D application instructions rate EPA" | Ingredient + application |
| "What are pesticides?" | agriculture_web | "What are pesticides?" | General question |
| "Latest farming news" | agriculture_web | "Latest farming news" | Current events |
| "Organic farming tips" | agriculture_web | "Organic farming tips" | General knowledge |
| "Weather in Iowa?" | weather | N/A | Weather API |
| "Soil data California?" | soil | N/A | USDA API |

---

## 💡 Optimization Strategies

### 1. Query Templates
Pre-define search templates for common patterns:

```python
CDMS_QUERY_TEMPLATES = {
    "product_label": "CDMS California {product} pesticide product label EPA",
    "safety": "CDMS {product} {ingredient} safety precautions hazards EPA",
    "application": "CDMS {product} {ingredient} application rate instructions",
    "registration": "CDMS {product} EPA registration number manufacturer"
}
```

### 2. Result Validation
Check if results are actually from CDMS:

```python
def validate_cdms_result(result: Dict) -> bool:
    """Check if result is from CDMS"""
    url = result.get("url", "").lower()
    title = result.get("title", "").lower()
    
    # Check if from official CDMS site
    if "cdpr.ca.gov" in url:
        return True
    
    # Check if mentions CDMS
    if "cdms" in title or "california pesticide" in title:
        return True
    
    return False
```

### 3. Fallback Strategy
```python
# If no CDMS results found, try alternative query
if not has_cdms_results(results):
    # Try without "CDMS" to get general pesticide info
    fallback_query = f"{product} pesticide label EPA registration"
    results = tavily.search(fallback_query)
```

---

## 💰 Cost Analysis

### Tavily Free Tier:
- **1,000 searches/month** = FREE
- ~33 searches/day
- Perfect for development/testing

### Cost Per Query:
- CDMS Label Search: **1 Tavily call** = $0.001 (after free tier)
- General Agriculture: **1 Tavily call** = $0.001

### Monthly Estimates:
| Usage Level | Searches/Month | Cost |
|-------------|----------------|------|
| Light (100/month) | 100 | FREE |
| Medium (500/month) | 500 | FREE |
| Heavy (2000/month) | 2000 | $1 |
| Very Heavy (5000/month) | 5000 | $4 |

**Very affordable!**

---

## ✅ Advantages of This Approach

### Pros:
1. ✅ **No storage needed** - Don't download thousands of PDFs
2. ✅ **Access entire CDMS** - All products available
3. ✅ **Always current** - Labels automatically up-to-date
4. ✅ **Simple maintenance** - No PDF management
5. ✅ **Cost-effective** - Only pay for searches used
6. ✅ **Scalable** - Works for any number of products

### Cons:
1. ⚠️ **Requires internet** - No offline access
2. ⚠️ **API dependency** - Relies on Tavily being up
3. ⚠️ **Slightly slower** - 2-4s vs. <1s for local
4. ⚠️ **Search quality varies** - May not always find exact label
5. ⚠️ **Costs add up** - If usage is very high

---

## 🎯 Success Criteria

### Phase 1-3 (Core Implementation):
- [ ] Tavily API configured
- [ ] Tavily client tested with CDMS searches
- [ ] CDMS label tool created
- [ ] Query crafting optimized
- [ ] Can find common product labels

### Phase 4-5 (Integration):
- [ ] Tool matcher updated
- [ ] Routes label queries to cdms_label tool
- [ ] Routes general queries to agriculture_web tool
- [ ] Tool executor handles both tools

### Phase 6-7 (Polish):
- [ ] UI updated with examples
- [ ] Source badges show "CDMS via Web" vs "Web Search"
- [ ] Error handling complete
- [ ] Test with 10+ products

---

## 🧪 Testing Plan

### Test Queries:

**CDMS Labels (Should use cdms_label tool):**
```
✅ "What's on the Roundup label?"
✅ "Safety information for glyphosate"
✅ "Application rate for 2,4-D on corn"
✅ "EPA registration for Sevin insecticide"
✅ "Active ingredients in Spectracide"
```

**General Agriculture (Should use agriculture_web tool):**
```
✅ "What are pesticides?"
✅ "How do insecticides work?"
✅ "Latest farming regulations"
✅ "Organic pest control methods"
✅ "Best practices for crop rotation"
```

**Edge Cases:**
```
✅ Obscure product (not in database)
✅ Misspelled product name
✅ No results found
✅ Tavily API down
✅ Rate limit exceeded
```

---

## 🚀 Implementation Timeline

### Day 1 (3-4 hours):
- ✅ Get Tavily API key
- ✅ Install tavily-python
- ✅ Test CDMS searches
- ✅ Optimize query crafting
- ✅ Create Tavily client

### Day 2 (3-4 hours):
- ✅ Create CDMS label tool
- ✅ Create agriculture web tool
- ✅ Update tool matcher
- ✅ Update tool executor
- ✅ Test routing logic

### Day 3 (2-3 hours):
- ✅ Update UI
- ✅ Add example queries
- ✅ Test with real queries
- ✅ Fix any issues
- ✅ Documentation

**Total: 8-11 hours over 3 days**

---

## 🎉 Final Architecture

```
User: "What's on the Roundup label?"
    ↓
Tool Matcher → "cdms_label" (confidence: 0.90)
    ↓
CDMS Label Tool:
    1. Extract: product="Roundup", ingredient="glyphosate"
    2. Craft query: "CDMS California Roundup glyphosate product label EPA"
    3. Call Tavily API
    4. Return: Label information with sources
    ↓
LLM formats natural response:
    "According to the CDMS database, Roundup contains glyphosate as 
     the active ingredient. Safety precautions include... [source]"


User: "What are pesticides?"
    ↓
Tool Matcher → "agriculture_web" (confidence: 0.85)
    ↓
Agriculture Web Tool:
    1. Direct Tavily search: "What are pesticides?"
    2. Return: General information with sources
    ↓
LLM formats educational response
```

**Clean, focused, and effective!**

---

## ✅ Summary & Recommendation

### Strategy: **Pure Tavily Approach**
- No local PDF storage
- Use Tavily for both CDMS labels AND general agriculture
- Two separate tools with different query strategies

### Why This Works:
1. ✅ **Solves storage problem** - No need to download all PDFs
2. ✅ **Solves API problem** - Works without CDMS API access
3. ✅ **Simple architecture** - Just Tavily + smart queries
4. ✅ **Cost-effective** - Free tier covers most usage
5. ✅ **Always current** - No manual updates needed

### Next Steps:
1. Get Tavily API key
2. Test CDMS searches (find optimal query format)
3. Implement cdms_label tool
4. Implement agriculture_web tool
5. Update tool matcher
6. Test thoroughly

---

**Ready to implement? I can help with each phase!** 🚀

Let me know if you want to:
- Start with Phase 1 (testing Tavily with CDMS)
- Implement the full solution
- Modify the approach

This is the best strategy given your constraints! 🎯


