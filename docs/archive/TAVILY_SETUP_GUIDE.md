# Tavily Setup Guide - Quick Start

## Step 1: Sign Up for Tavily

1. **Go to:** https://tavily.com
2. **Click:** "Sign Up" or "Get Started"
3. **Create account** with your email
4. **Verify email** (check inbox)

## Step 2: Get Your API Key

1. **Log in** to Tavily dashboard
2. **Navigate to:** API Keys section
3. **Copy your API key** (starts with `tvly-`)
4. **Save it** - you'll need it in a moment

Example key format: `tvly-abc123xyz456def789...`

## Step 3: Add to .env File

Your API key goes in the `.env` file at project root.

**If .env doesn't exist yet:**
```bash
cd /Users/sanjeedajeba/agentic_ai_project
touch .env
```

**Add this line to .env:**
```
TAVILY_API_KEY=tvly-your-actual-key-here
```

**Example .env file:**
```env
# Weather & Geocoding
OPENWEATHER_API_KEY=your_openweather_key

# OpenAI for LLM
OPENAI_API_KEY=your_openai_key

# Tavily for Web Search (NEW!)
TAVILY_API_KEY=tvly-abc123xyz456def789
```

## Step 4: Install Tavily Package

```bash
conda activate agentic
pip install tavily-python
```

## Step 5: Verify Setup

Quick test to make sure it works:

```bash
python -c "from tavily import TavilyClient; print('✅ Tavily installed!')"
```

---

## 🎯 You're Ready!

Once you've completed these steps, you're ready to test CDMS searches!

**Next:** Run the test script to see which query format works best.

---

## 🔍 Domain Filtering Feature (Important!)

Tavily has a powerful **`include_domains`** parameter that lets you target specific websites!

### For CDMS Searches:
```python
response = client.search(
    query="Roundup glyphosate pesticide label",
    include_domains=["cdms.net"],  # ONLY search CDMS website!
    max_results=5
)
```

### Why This Is Great:
- ✅ **100% CDMS results** (no random websites)
- ✅ **Faster searches** (smaller search space)
- ✅ **More accurate** (targeted domain)
- ✅ **No false positives** (only official CDMS data)

### CDMS Domain:
The official CDMS (Crop Data Management Systems) label database is at:
- **Domain:** `cdms.net`
- **Website:** https://www.cdms.net/LabelsSDS/home
- **What it contains:** Pesticide product labels and Safety Data Sheets (SDS)

Our test script (Formats 5, 6, and 7) will test this domain filtering approach!

