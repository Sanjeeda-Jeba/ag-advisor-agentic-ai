# API Integration Enhancement Plan

## 🎯 Overview

**Current State:** The app matches natural language queries to API names from a catalog.

**Goal:** Enable the app to actually CALL real APIs (Weather API, OpenAI API, USDA Soil API, etc.) and display real results.

---

## 🌟 Key Features to Add

1. **Real API Integration** - Call actual external APIs
2. **Parameter Extraction** - Extract parameters from user queries (location, date, etc.)
3. **API Key Management** - Secure storage and handling of API credentials
4. **Request Handling** - Make HTTP requests to external APIs
5. **Response Parsing** - Process and format API responses
6. **Result Display** - Show real data in the UI
7. **Error Handling** - Handle API failures gracefully
8. **Rate Limiting** - Prevent API quota exhaustion
9. **Caching** - Cache results to reduce API calls

---

## 📋 APIs to Integrate

### 1. Weather API (OpenWeatherMap)
**Use Case:** "What's the weather in New York?"
- **Endpoint:** `https://api.openweathermap.org/data/2.5/weather`
- **Parameters:** `city`, `country_code`, `units`
- **Authentication:** API Key
- **Free Tier:** Yes (60 calls/minute)

### 2. OpenAI API (GPT-3.5/GPT-4)
**Use Case:** "Generate a summary of customer feedback"
- **Endpoint:** `https://api.openai.com/v1/chat/completions`
- **Parameters:** `prompt`, `model`, `max_tokens`
- **Authentication:** Bearer Token (API Key)
- **Free Tier:** No (pay-as-you-go)

### 3. USDA Soil Data API
**Use Case:** "Get soil data for Iowa"
- **Endpoint:** `https://sdmdataaccess.sc.egov.usda.gov/Tabular/SDMTabularService.asmx`
- **Parameters:** `location`, `query_type`
- **Authentication:** None (public API)
- **Free Tier:** Yes

### 4. Customer/Product APIs (Mock/Custom)
**Use Case:** "Get customer details for ID 12345"
- **Endpoint:** Custom internal APIs or mock APIs
- **Parameters:** `customer_id`, `product_id`
- **Authentication:** API Key or OAuth

---

## 🏗️ Architecture Changes

### Current Architecture:
```
User Query → Parser → Fuzzy Matcher → Display Matched API Names
```

### New Architecture:
```
User Query → Parser → Parameter Extractor → API Router → API Caller → Response Parser → Display Results
                ↓
         Fuzzy Matcher
                ↓
         Select Best API
```

---

## 📁 New File Structure

```
agentic_ai_project/
├── .streamlit/
│   └── config.toml
├── src/
│   ├── agent_graph.py (existing - will be enhanced)
│   ├── parser.py (existing - will be enhanced)
│   ├── api_catalog.json (existing - will be expanded)
│   ├── streamlit_app.py (existing - will be enhanced)
│   ├── api_clients/  (NEW)
│   │   ├── __init__.py
│   │   ├── base_client.py         # Base class for all API clients
│   │   ├── weather_client.py      # OpenWeatherMap client
│   │   ├── openai_client.py       # OpenAI API client
│   │   ├── usda_client.py         # USDA Soil API client
│   │   └── mock_client.py         # Mock APIs for testing
│   ├── utils/  (NEW)
│   │   ├── __init__.py
│   │   ├── parameter_extractor.py # Extract params from queries
│   │   ├── api_router.py          # Route to correct API
│   │   ├── response_formatter.py  # Format API responses
│   │   └── cache_manager.py       # Cache API responses
│   └── config/  (NEW)
│       ├── __init__.py
│       ├── api_config.json        # API configurations
│       └── credentials.py         # API key management
├── .env  (NEW - for API keys, GITIGNORED)
├── .env.example  (NEW - template for API keys)
├── requirements.txt (NEW - for pip dependencies)
└── README.md (update with new instructions)
```

---

## 🔧 Required Changes to Existing Files

### 1. `src/api_catalog.json` (EXPAND)

**Current:**
```json
{
  "apis": [
    {
      "name": "get_customer_details",
      "description": "Retrieves detailed information about a customer.",
      "tags": ["customer", "details", "info"],
      "keywords": ["customer details", "customer info", "get customer"]
    }
  ]
}
```

**Enhanced:**
```json
{
  "apis": [
    {
      "name": "get_weather",
      "description": "Get current weather for a location",
      "tags": ["weather", "temperature", "forecast"],
      "keywords": ["weather", "temperature", "forecast", "climate"],
      "api_type": "weather",
      "endpoint": "https://api.openweathermap.org/data/2.5/weather",
      "method": "GET",
      "auth_type": "api_key",
      "required_params": ["city"],
      "optional_params": ["country_code", "units"],
      "param_mapping": {
        "city": ["location", "city", "place", "where"],
        "units": ["metric", "imperial", "fahrenheit", "celsius"]
      },
      "rate_limit": "60/minute",
      "cost": "free"
    },
    {
      "name": "openai_completion",
      "description": "Generate text completions using OpenAI GPT models",
      "tags": ["ai", "gpt", "text", "generation"],
      "keywords": ["generate", "write", "summarize", "ai", "gpt"],
      "api_type": "openai",
      "endpoint": "https://api.openai.com/v1/chat/completions",
      "method": "POST",
      "auth_type": "bearer",
      "required_params": ["prompt"],
      "optional_params": ["model", "max_tokens", "temperature"],
      "param_mapping": {
        "prompt": ["text", "query", "request", "generate"]
      },
      "rate_limit": "3500/minute",
      "cost": "paid"
    },
    {
      "name": "usda_soil_data",
      "description": "Get soil data from USDA database",
      "tags": ["soil", "agriculture", "usda"],
      "keywords": ["soil", "agriculture", "farm", "crop"],
      "api_type": "usda",
      "endpoint": "https://sdmdataaccess.sc.egov.usda.gov/Tabular/SDMTabularService.asmx",
      "method": "POST",
      "auth_type": "none",
      "required_params": ["location"],
      "optional_params": ["query_type"],
      "param_mapping": {
        "location": ["location", "state", "area", "region"]
      },
      "rate_limit": "unlimited",
      "cost": "free"
    }
  ]
}
```

### 2. `src/parser.py` (ENHANCE)

**Add parameter extraction capability:**

```python
def extract_parameters(query: str, api_config: dict):
    """
    Extract parameters from query based on API requirements.
    
    Example:
    Query: "What's the weather in New York?"
    API: get_weather
    Extracted: {"city": "New York"}
    """
    # Implementation using spaCy NER and pattern matching
    pass
```

### 3. `src/agent_graph.py` (ENHANCE)

**Add new nodes to the graph:**

```python
# New nodes:
# 1. parameter_extraction_node
# 2. api_selection_node
# 3. api_call_node
# 4. response_formatting_node

# New graph flow:
START → parser_node → parameter_extraction_node → api_selection_node → api_call_node → response_formatting_node → END
```

### 4. `src/streamlit_app.py` (ENHANCE)

**Add:**
- API call execution button
- Results display for real API data
- Error handling UI
- API selection dropdown (if multiple APIs match)
- Parameter confirmation/editing UI

---

## 🆕 New Files to Create

### 1. `src/api_clients/base_client.py`

**Purpose:** Base class for all API clients

```python
from abc import ABC, abstractmethod
import requests
from typing import Dict, Any, Optional

class BaseAPIClient(ABC):
    """Base class for all API clients."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()
    
    @abstractmethod
    def call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make the API call."""
        pass
    
    @abstractmethod
    def format_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Format the API response for display."""
        pass
    
    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle API errors gracefully."""
        return {
            "success": False,
            "error": str(error),
            "message": "API call failed"
        }
```

### 2. `src/api_clients/weather_client.py`

**Purpose:** OpenWeatherMap API client

```python
from .base_client import BaseAPIClient
import requests

class WeatherAPIClient(BaseAPIClient):
    """Client for OpenWeatherMap API."""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    
    def call(self, params):
        """
        Call the weather API.
        
        Required params: city
        Optional params: country_code, units
        """
        try:
            query_params = {
                "q": params.get("city"),
                "appid": self.api_key,
                "units": params.get("units", "metric")
            }
            
            response = self.session.get(self.BASE_URL, params=query_params)
            response.raise_for_status()
            return self.format_response(response.json())
            
        except Exception as e:
            return self.handle_error(e)
    
    def format_response(self, response):
        """Format weather API response."""
        return {
            "success": True,
            "location": response.get("name"),
            "temperature": response["main"]["temp"],
            "description": response["weather"][0]["description"],
            "humidity": response["main"]["humidity"],
            "wind_speed": response["wind"]["speed"]
        }
```

### 3. `src/api_clients/openai_client.py`

**Purpose:** OpenAI API client

```python
from .base_client import BaseAPIClient
import openai

class OpenAIClient(BaseAPIClient):
    """Client for OpenAI API."""
    
    def __init__(self, api_key):
        super().__init__(api_key)
        openai.api_key = api_key
    
    def call(self, params):
        """
        Call OpenAI API.
        
        Required params: prompt
        Optional params: model, max_tokens, temperature
        """
        try:
            response = openai.ChatCompletion.create(
                model=params.get("model", "gpt-3.5-turbo"),
                messages=[
                    {"role": "user", "content": params["prompt"]}
                ],
                max_tokens=params.get("max_tokens", 150),
                temperature=params.get("temperature", 0.7)
            )
            
            return self.format_response(response)
            
        except Exception as e:
            return self.handle_error(e)
    
    def format_response(self, response):
        """Format OpenAI API response."""
        return {
            "success": True,
            "text": response.choices[0].message.content,
            "model": response.model,
            "tokens_used": response.usage.total_tokens
        }
```

### 4. `src/api_clients/usda_client.py`

**Purpose:** USDA Soil API client

```python
from .base_client import BaseAPIClient
import requests

class USDAClient(BaseAPIClient):
    """Client for USDA Soil Data API."""
    
    BASE_URL = "https://sdmdataaccess.sc.egov.usda.gov/Tabular/SDMTabularService.asmx"
    
    def call(self, params):
        """Call USDA Soil API."""
        # Implementation for USDA soil data queries
        pass
    
    def format_response(self, response):
        """Format USDA API response."""
        pass
```

### 5. `src/utils/parameter_extractor.py`

**Purpose:** Extract parameters from natural language queries

```python
import spacy
from typing import Dict, Any, List

nlp = spacy.load("en_core_web_sm")

class ParameterExtractor:
    """Extract parameters from queries using NLP."""
    
    def extract(self, query: str, api_config: dict) -> Dict[str, Any]:
        """
        Extract parameters based on API configuration.
        
        Example:
        Query: "What's the weather in Tokyo, Japan?"
        API Config: { "required_params": ["city"], "param_mapping": {...} }
        Result: {"city": "Tokyo", "country": "Japan"}
        """
        doc = nlp(query)
        extracted_params = {}
        
        # Extract entities (GPE = Geopolitical Entity)
        for ent in doc.ents:
            if ent.label_ == "GPE":
                extracted_params["city"] = ent.text
            elif ent.label_ == "DATE":
                extracted_params["date"] = ent.text
            elif ent.label_ == "PERSON":
                extracted_params["person"] = ent.text
        
        # Extract units (metric/imperial)
        if "fahrenheit" in query.lower() or "imperial" in query.lower():
            extracted_params["units"] = "imperial"
        elif "celsius" in query.lower() or "metric" in query.lower():
            extracted_params["units"] = "metric"
        
        return extracted_params
    
    def validate_params(self, params: Dict, required_params: List[str]) -> tuple:
        """
        Validate that required parameters are present.
        
        Returns: (is_valid, missing_params)
        """
        missing = [p for p in required_params if p not in params]
        return len(missing) == 0, missing
```

### 6. `src/utils/api_router.py`

**Purpose:** Route queries to the correct API client

```python
from typing import Dict, Any
from ..api_clients.weather_client import WeatherAPIClient
from ..api_clients.openai_client import OpenAIClient
from ..api_clients.usda_client import USDAClient
from ..config.credentials import get_api_key

class APIRouter:
    """Route API calls to the appropriate client."""
    
    def __init__(self):
        self.clients = {
            "weather": WeatherAPIClient(get_api_key("OPENWEATHER_API_KEY")),
            "openai": OpenAIClient(get_api_key("OPENAI_API_KEY")),
            "usda": USDAClient()
        }
    
    def call_api(self, api_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route the API call to the correct client.
        
        Args:
            api_type: Type of API (weather, openai, usda)
            params: Parameters for the API call
        
        Returns:
            API response
        """
        if api_type not in self.clients:
            return {
                "success": False,
                "error": f"Unknown API type: {api_type}"
            }
        
        client = self.clients[api_type]
        return client.call(params)
```

### 7. `src/utils/response_formatter.py`

**Purpose:** Format API responses for beautiful UI display

```python
from typing import Dict, Any

class ResponseFormatter:
    """Format API responses for display."""
    
    @staticmethod
    def format_weather_response(data: Dict[str, Any]) -> str:
        """Format weather data as readable text."""
        if not data.get("success"):
            return f"❌ Error: {data.get('error', 'Unknown error')}"
        
        return f"""
        🌤️ **Weather in {data['location']}**
        
        - **Temperature:** {data['temperature']}°C
        - **Conditions:** {data['description']}
        - **Humidity:** {data['humidity']}%
        - **Wind Speed:** {data['wind_speed']} m/s
        """
    
    @staticmethod
    def format_openai_response(data: Dict[str, Any]) -> str:
        """Format OpenAI response."""
        if not data.get("success"):
            return f"❌ Error: {data.get('error', 'Unknown error')}"
        
        return f"""
        🤖 **AI Response:**
        
        {data['text']}
        
        ---
        *Model: {data['model']} | Tokens: {data['tokens_used']}*
        """
    
    @staticmethod
    def format_usda_response(data: Dict[str, Any]) -> str:
        """Format USDA soil data."""
        # Implementation
        pass
```

### 8. `src/utils/cache_manager.py`

**Purpose:** Cache API responses to reduce API calls and costs

```python
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class CacheManager:
    """Manage caching of API responses."""
    
    def __init__(self, cache_dir: str = ".cache", ttl_minutes: int = 60):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def _get_cache_key(self, api_name: str, params: Dict[str, Any]) -> str:
        """Generate a unique cache key."""
        param_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(f"{api_name}:{param_str}".encode()).hexdigest()
    
    def get(self, api_name: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached response if available and not expired."""
        cache_key = self._get_cache_key(api_name, params)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        with open(cache_file, 'r') as f:
            cached_data = json.load(f)
        
        # Check if expired
        cached_time = datetime.fromisoformat(cached_data['timestamp'])
        if datetime.now() - cached_time > self.ttl:
            cache_file.unlink()  # Delete expired cache
            return None
        
        return cached_data['response']
    
    def set(self, api_name: str, params: Dict[str, Any], response: Dict[str, Any]):
        """Cache an API response."""
        cache_key = self._get_cache_key(api_name, params)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        cached_data = {
            'timestamp': datetime.now().isoformat(),
            'api_name': api_name,
            'params': params,
            'response': response
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cached_data, f, indent=2)
```

### 9. `src/config/credentials.py`

**Purpose:** Secure API key management

```python
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

def get_api_key(key_name: str) -> str:
    """
    Get API key from environment variables.
    
    Args:
        key_name: Name of the environment variable
    
    Returns:
        API key value
    
    Raises:
        ValueError: If API key is not found
    """
    api_key = os.getenv(key_name)
    
    if not api_key:
        raise ValueError(
            f"API key '{key_name}' not found in environment variables. "
            f"Please set it in the .env file."
        )
    
    return api_key

def get_all_api_keys() -> dict:
    """Get all configured API keys."""
    return {
        "openweather": os.getenv("OPENWEATHER_API_KEY"),
        "openai": os.getenv("OPENAI_API_KEY"),
        # Add more as needed
    }

def validate_api_keys() -> dict:
    """Validate that all required API keys are present."""
    required_keys = [
        "OPENWEATHER_API_KEY",
        # "OPENAI_API_KEY",  # Optional
    ]
    
    validation = {}
    for key in required_keys:
        validation[key] = os.getenv(key) is not None
    
    return validation
```

### 10. `.env.example`

**Purpose:** Template for API keys (committed to git)

```env
# API Keys Configuration
# Copy this file to .env and fill in your actual API keys

# OpenWeatherMap API Key
# Get yours at: https://openweathermap.org/api
OPENWEATHER_API_KEY=your_openweather_api_key_here

# OpenAI API Key (Optional - for GPT features)
# Get yours at: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# USDA API (No key required - public API)
```

### 11. `.env` (ACTUAL - NOT COMMITTED)

**Purpose:** Actual API keys (add to .gitignore!)

```env
OPENWEATHER_API_KEY=abc123xyz456...
OPENAI_API_KEY=sk-proj-...
```

---

## 🔐 Security Considerations

### 1. API Key Storage

**DO:**
- ✅ Use `.env` file for local development
- ✅ Add `.env` to `.gitignore`
- ✅ Provide `.env.example` as template
- ✅ Use environment variables in production
- ✅ Encrypt keys if storing in database

**DON'T:**
- ❌ Hardcode API keys in source code
- ❌ Commit API keys to git
- ❌ Share API keys in screenshots or demos
- ❌ Log API keys in error messages

### 2. `.gitignore` Updates

Add to `.gitignore`:
```
.env
.cache/
*.pyc
__pycache__/
```

### 3. Rate Limiting

Implement rate limiting to prevent API abuse:
```python
from functools import wraps
import time

def rate_limit(calls_per_minute):
    def decorator(func):
        last_called = [0.0]
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            wait_time = 60.0 / calls_per_minute
            
            if elapsed < wait_time:
                time.sleep(wait_time - elapsed)
            
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        
        return wrapper
    return decorator
```

---

## 🎨 UI Enhancements for Streamlit App

### 1. API Selection Interface

```python
# If multiple APIs match, let user choose
if len(matched_apis) > 1:
    st.markdown("### 🎯 Multiple APIs matched. Select one:")
    selected_api = st.selectbox(
        "Choose API to call:",
        options=[api["api_name"] for api in matched_apis],
        format_func=lambda x: f"{x} ({get_api_description(x)})"
    )
```

### 2. Parameter Review/Edit Interface

```python
st.markdown("### 📝 Extracted Parameters")
st.info("Review and edit the parameters before calling the API:")

# Allow user to edit extracted parameters
edited_params = {}
for param_name, param_value in extracted_params.items():
    edited_params[param_name] = st.text_input(
        param_name.capitalize(),
        value=param_value,
        help=f"Parameter: {param_name}"
    )
```

### 3. API Call Button

```python
if st.button("🚀 Call API", type="primary"):
    with st.spinner("Calling API..."):
        response = api_router.call_api(api_type, edited_params)
        
        if response.get("success"):
            st.success("✅ API call successful!")
            st.json(response)
        else:
            st.error(f"❌ API call failed: {response.get('error')}")
```

### 4. Results Display

```python
if api_response:
    st.markdown("---")
    st.markdown("## 📊 API Response")
    
    # Display formatted response
    formatted_response = response_formatter.format(
        api_type, 
        api_response
    )
    st.markdown(formatted_response)
    
    # Show raw JSON in expander
    with st.expander("🔍 View Raw Response"):
        st.json(api_response)
    
    # Download button
    st.download_button(
        label="💾 Download Response",
        data=json.dumps(api_response, indent=2),
        file_name=f"api_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )
```

### 5. Error Handling Display

```python
try:
    response = call_api(...)
except APIKeyError:
    st.error("""
    ❌ **API Key Missing**
    
    Please configure your API keys in the `.env` file:
    1. Copy `.env.example` to `.env`
    2. Add your API keys
    3. Restart the app
    """)
except RateLimitError:
    st.warning("""
    ⚠️ **Rate Limit Exceeded**
    
    You've hit the API rate limit. Please wait a moment and try again.
    """)
except Exception as e:
    st.error(f"❌ Unexpected error: {str(e)}")
```

---

## 📦 New Dependencies

Add to `environment.yml` or create `requirements.txt`:

```txt
# HTTP Requests
requests>=2.31.0
httpx>=0.25.0

# API Clients
openai>=1.3.0
python-dotenv>=1.0.0

# Caching
diskcache>=5.6.3

# Rate Limiting
ratelimit>=2.2.1

# Additional
python-dateutil>=2.8.2
```

---

## 🔄 Implementation Steps

### Phase 1: Foundation (Week 1)

**Step 1.1: Set up Environment**
- [ ] Create `.env.example` file
- [ ] Update `.gitignore`
- [ ] Install new dependencies
- [ ] Set up API key configuration

**Step 1.2: Create Base Infrastructure**
- [ ] Create `api_clients/` directory
- [ ] Implement `base_client.py`
- [ ] Create `utils/` directory
- [ ] Implement `credentials.py`

**Step 1.3: Expand API Catalog**
- [ ] Update `api_catalog.json` with real API configurations
- [ ] Add parameter mappings
- [ ] Add authentication details

### Phase 2: Weather API Integration (Week 1-2)

**Step 2.1: Weather Client**
- [ ] Sign up for OpenWeatherMap API key
- [ ] Implement `weather_client.py`
- [ ] Test API calls manually

**Step 2.2: Parameter Extraction**
- [ ] Implement `parameter_extractor.py`
- [ ] Add location extraction from queries
- [ ] Test with various query formats

**Step 2.3: Integration**
- [ ] Implement `api_router.py`
- [ ] Connect to Streamlit app
- [ ] Add UI for displaying weather data

### Phase 3: Additional APIs (Week 2-3)

**Step 3.1: OpenAI Integration**
- [ ] Get OpenAI API key (optional)
- [ ] Implement `openai_client.py`
- [ ] Add prompt extraction
- [ ] Test with sample queries

**Step 3.2: USDA Integration**
- [ ] Research USDA API documentation
- [ ] Implement `usda_client.py`
- [ ] Add location-based queries
- [ ] Test with soil data queries

### Phase 4: Enhancement Features (Week 3-4)

**Step 4.1: Caching**
- [ ] Implement `cache_manager.py`
- [ ] Add cache to all API clients
- [ ] Test cache expiration

**Step 4.2: Rate Limiting**
- [ ] Implement rate limiting decorator
- [ ] Add to all API clients
- [ ] Test rate limit handling

**Step 4.3: Response Formatting**
- [ ] Implement `response_formatter.py`
- [ ] Create beautiful displays for each API type
- [ ] Add charts/visualizations where appropriate

### Phase 5: Testing & Polish (Week 4)

**Step 5.1: Testing**
- [ ] Unit tests for all clients
- [ ] Integration tests
- [ ] Error handling tests
- [ ] UI testing

**Step 5.2: Documentation**
- [ ] Update README
- [ ] Add API setup guides
- [ ] Create troubleshooting section
- [ ] Add example queries

**Step 5.3: Polish**
- [ ] Improve error messages
- [ ] Add loading animations
- [ ] Optimize performance
- [ ] Final UI improvements

---

## 🧪 Testing Strategy

### 1. Unit Tests

```python
# tests/test_weather_client.py
import pytest
from src.api_clients.weather_client import WeatherAPIClient

def test_weather_client_success():
    client = WeatherAPIClient(api_key="test_key")
    params = {"city": "London"}
    response = client.call(params)
    assert response["success"] is True
    assert "temperature" in response

def test_weather_client_missing_param():
    client = WeatherAPIClient(api_key="test_key")
    params = {}  # Missing city
    response = client.call(params)
    assert response["success"] is False
```

### 2. Integration Tests

```python
# tests/test_integration.py
def test_end_to_end_weather_query():
    query = "What's the weather in Tokyo?"
    
    # Parse query
    parsed = parse_query(query)
    
    # Extract parameters
    params = extract_parameters(query, api_config)
    assert params["city"] == "Tokyo"
    
    # Call API
    response = api_router.call_api("weather", params)
    assert response["success"] is True
```

### 3. Mock API Testing

```python
# src/api_clients/mock_client.py
class MockWeatherClient(BaseAPIClient):
    """Mock weather client for testing."""
    
    def call(self, params):
        return {
            "success": True,
            "location": params.get("city", "Unknown"),
            "temperature": 20,
            "description": "Clear sky",
            "humidity": 50,
            "wind_speed": 5
        }
```

---

## 📊 Example Use Cases

### Use Case 1: Weather Query

**User Input:**
```
What's the weather like in San Francisco?
```

**System Flow:**
1. Parse query → Extract keywords: ["weather", "san francisco"]
2. Match API → `get_weather` (95% confidence)
3. Extract parameters → `{"city": "San Francisco"}`
4. Call API → OpenWeatherMap
5. Display result:
   ```
   🌤️ Weather in San Francisco
   - Temperature: 18°C
   - Conditions: Partly cloudy
   - Humidity: 65%
   - Wind Speed: 4.5 m/s
   ```

### Use Case 2: AI Generation

**User Input:**
```
Generate a product description for wireless headphones
```

**System Flow:**
1. Parse query → Match `openai_completion`
2. Extract parameters → `{"prompt": "Generate a product description for wireless headphones"}`
3. Call OpenAI API
4. Display AI-generated text

### Use Case 3: Soil Data

**User Input:**
```
Get soil data for Iowa farmland
```

**System Flow:**
1. Parse query → Match `usda_soil_data`
2. Extract parameters → `{"location": "Iowa"}`
3. Call USDA API
4. Display soil composition data

---

## 🎯 Success Metrics

### Functionality
- [ ] Successfully call at least 3 different API types
- [ ] 95%+ success rate for parameter extraction
- [ ] <2 second response time for cached queries
- [ ] <5 seconds for live API calls

### User Experience
- [ ] Clear error messages for all failure cases
- [ ] Beautiful, formatted results
- [ ] Easy parameter editing
- [ ] Intuitive UI flow

### Reliability
- [ ] Graceful handling of API failures
- [ ] Rate limiting prevents quota exhaustion
- [ ] Caching reduces unnecessary API calls
- [ ] Secure API key management

---

## 💰 Cost Considerations

### Free Tier Limits

**OpenWeatherMap (Free):**
- 60 calls/minute
- 1,000,000 calls/month
- **Cost:** $0

**OpenAI (Paid):**
- GPT-3.5-Turbo: $0.002/1K tokens
- Typical query: ~500 tokens = $0.001
- **Estimated Cost:** $1-5/month for moderate use

**USDA (Free):**
- Unlimited calls
- **Cost:** $0

### Cost Optimization

1. **Implement Caching:** Save 50-80% of API calls
2. **Rate Limiting:** Prevent accidental overuse
3. **User Confirmation:** Ask before expensive API calls
4. **Usage Tracking:** Monitor and alert on high usage

---

## 🚀 Quick Start Guide (After Implementation)

### 1. Get API Keys

```bash
# OpenWeatherMap (Required)
# Sign up at: https://openweathermap.org/api
# Free tier: 60 calls/min

# OpenAI (Optional)
# Sign up at: https://platform.openai.com/
# Paid: ~$0.002/1K tokens
```

### 2. Configure Environment

```bash
# Copy example file
cp .env.example .env

# Edit .env and add your keys
nano .env
```

### 3. Install Dependencies

```bash
# Update conda environment
conda env update -f environment.yml --prune

# Or install via pip
pip install -r requirements.txt
```

### 4. Run the App

```bash
streamlit run src/streamlit_app.py
```

### 5. Test It

Try these queries:
- "What's the weather in London?"
- "Generate a summary of customer feedback"
- "Get soil data for California"

---

## 📚 Additional Resources

### API Documentation

- **OpenWeatherMap:** https://openweathermap.org/api
- **OpenAI:** https://platform.openai.com/docs
- **USDA Soil Data:** https://sdmdataaccess.sc.egov.usda.gov/

### Tutorials

- [Building API Clients in Python](https://realpython.com/api-integration-in-python/)
- [Streamlit API Reference](https://docs.streamlit.io/)
- [spaCy Named Entity Recognition](https://spacy.io/usage/linguistic-features#named-entities)

---

## ✅ Summary

This plan transforms your app from an **API matcher** to a **full-fledged API integration platform**:

1. **Match** queries to APIs (existing ✅)
2. **Extract** parameters from queries (new)
3. **Call** real external APIs (new)
4. **Display** actual results (new)
5. **Cache** responses for efficiency (new)
6. **Secure** API keys properly (new)

**Estimated Timeline:** 3-4 weeks for full implementation

**Complexity:** Intermediate to Advanced

**Impact:** High - transforms the app into a truly useful tool!

---

Ready to start implementation? Let me know which API you want to integrate first! 🚀

