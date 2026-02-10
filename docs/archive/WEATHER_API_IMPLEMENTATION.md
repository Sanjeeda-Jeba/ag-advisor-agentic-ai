# Weather API Implementation Guide

## 🎯 Goal
Integrate OpenWeatherMap API so users can ask "What's the weather in [city]?" and get real weather data.

---

## 📋 Step-by-Step Implementation Plan

### Step 1: Get OpenWeatherMap API Key (5 minutes)

**Actions:**
1. Go to https://openweathermap.org/api
2. Click "Sign Up" (top right)
3. Create a free account
4. Go to "API Keys" section
5. Copy your API key (looks like: `abc123xyz456...`)

**Free Tier Includes:**
- 60 calls per minute
- 1,000,000 calls per month
- Current weather data
- 5 day forecast

**Note:** API key activation can take up to 2 hours (usually instant)

---

### Step 2: Create Environment Files (5 minutes)

**2.1 Create `.env.example`** (template - will be committed to git)
**2.2 Create `.env`** (actual keys - will NOT be committed)
**2.3 Update `.gitignore`**

---

### Step 3: Install Dependencies (5 minutes)

**3.1 Add new packages to environment.yml:**
- `requests` (for HTTP calls)
- `python-dotenv` (for .env file loading)

**3.2 Update conda environment**

---

### Step 4: Create Directory Structure (2 minutes)

**Create these directories:**
```
src/
├── api_clients/
│   └── __init__.py
├── utils/
│   └── __init__.py
└── config/
    └── __init__.py
```

---

### Step 5: Implement Credentials Manager (10 minutes)

**File:** `src/config/credentials.py`

**Purpose:** Load API keys from .env file securely

---

### Step 6: Implement Base API Client (15 minutes)

**File:** `src/api_clients/base_client.py`

**Purpose:** Abstract base class for all API clients

---

### Step 7: Implement Weather API Client (20 minutes)

**File:** `src/api_clients/weather_client.py`

**Purpose:** Call OpenWeatherMap API and format responses

---

### Step 8: Implement Parameter Extractor (20 minutes)

**File:** `src/utils/parameter_extractor.py`

**Purpose:** Extract city names from natural language queries

---

### Step 9: Update API Catalog (10 minutes)

**File:** `src/api_catalog.json`

**Purpose:** Add weather API configuration

---

### Step 10: Implement API Router (15 minutes)

**File:** `src/utils/api_router.py`

**Purpose:** Route queries to the correct API client

---

### Step 11: Update Streamlit App (30 minutes)

**File:** `src/streamlit_app.py`

**Purpose:** Add UI for calling APIs and displaying results

---

### Step 12: Test Everything (15 minutes)

**Test queries:**
- "What's the weather in London?"
- "Show me the temperature in Tokyo"
- "Weather in New York City"

---

## ⏱️ Total Time: ~2.5 hours

---

## 🚀 Let's Start!

Ready to begin? We'll go through each step together.

**First up: Step 1 - Getting your API key!**

Have you already signed up for OpenWeatherMap, or should I guide you through it?

