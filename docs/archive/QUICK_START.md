# 🚀 Quick Start: CDMS + Tavily Integration

## 📋 What We're Doing

Adding real-time CDMS pesticide label search via Tavily web API.

**Phase 1:** Test & validate approach (30 minutes)  
**Phase 2:** Full implementation (6-8 hours)

---

## ✅ Phase 1: Testing (Do This Now!)

### 1. Get Tavily API Key (5 minutes)

```
1. Go to: https://tavily.com
2. Sign up (free account)
3. Get API key (starts with tvly-)
4. Save it somewhere safe
```

### 2. Add to .env File (2 minutes)

```bash
# Open your .env file (create if doesn't exist)
cd /Users/sanjeedajeba/agentic_ai_project
nano .env  # or use your preferred editor

# Add this line:
TAVILY_API_KEY=tvly-your-actual-key-here

# Save and exit
```

### 3. Install Tavily Package (2 minutes)

```bash
# Activate environment
conda activate agentic

# Install Tavily
pip install tavily-python

# Verify
python -c "from tavily import TavilyClient; print('✅ Installed!')"
```

### 4. Run Test Script (5-10 minutes)

```bash
python test_cdms_tavily.py
```

**This will:**
- Test 5 different query formats
- Show which finds CDMS labels best
- Recommend optimal approach
- Show example results

**Expected Output:**
```
🧪 Testing CDMS Label Search via Tavily
✅ Tavily API key loaded
✅ Tavily client initialized

Testing different query formats...
[Results for each format]

🏆 RECOMMENDED FORMAT:
   Format 4: Full Context
   Query: "CDMS California Roundup glyphosate pesticide product label EPA"
   Reason: Found 3 CDMS results
```

---

## 🎯 After Testing

Once testing is complete, you'll know:
- ✅ Which query format works best for CDMS
- ✅ Whether Tavily can reliably find labels
- ✅ If the approach is viable

Then we proceed to **Phase 2: Full Implementation!**

---

## 📞 Need Help?

**If Tavily API key doesn't work:**
- Check it's in .env file
- Check no extra spaces
- Check it starts with `tvly-`

**If test script fails:**
- Make sure conda environment is activated
- Make sure tavily-python is installed
- Check error message

**If no CDMS results found:**
- Try different products (2,4-D, Sevin, etc.)
- Check if Tavily free tier has limits
- Results may vary by product availability

---

## 🚀 Phase 2 Preview

After successful testing, we'll implement:

1. **Tavily Client** (`src/api_clients/tavily_client.py`)
2. **CDMS Label Tool** (`src/tools/cdms_label_tool.py`)
3. **Agriculture Web Tool** (`src/tools/agriculture_web_tool.py`)
4. **Tool Matcher Updates** (routing logic)
5. **Tool Executor Updates** (new tools)
6. **UI Updates** (example queries)

**Timeline:** 6-8 hours total

---

## ✅ Action Items

- [ ] Sign up for Tavily
- [ ] Get API key
- [ ] Add to .env file
- [ ] Install tavily-python
- [ ] Run test_cdms_tavily.py
- [ ] Review results
- [ ] Proceed to Phase 2!

**Let's start! Get your Tavily API key and run the test!** 🎯


