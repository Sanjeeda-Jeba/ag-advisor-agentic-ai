# 🎨 Updated UI with Tavily Integration

## ✅ What's New in the UI

The Streamlit conversational interface has been updated to showcase the new **Tavily-powered** features!

---

## 🚀 How to Run

```bash
# Activate environment
conda activate agentic

# Run the Streamlit app
streamlit run src/streamlit_app_conversational.py
```

The app will open in your browser at `http://localhost:8501`

---

## ✨ New Features

### 1. **Updated Title & Description**
- **New Title:** "Agriculture AI Assistant"
- **New Tagline:** Mentions CDMS labels and citations

### 2. **CDMS Label Search Examples** 🏷️
Three new quick buttons:
- 🌿 **Roundup Label** - "Find me the Roundup pesticide label"
- 🐛 **Sevin Label** - "Show me the Sevin insecticide label"
- 🌾 **2,4-D Label** - "Get the 2,4-D herbicide label"

### 3. **Agriculture Web Search Examples** 🌐
Three new quick buttons:
- 🐜 **Pest Control** - "How to control aphids on tomato plants?"
- 🌱 **Fertilization** - "Best practices for corn fertilization timing"
- 🌍 **Soil Health** - "How to improve soil organic matter?"

### 4. **Citation Badges** 📚
New purple badge appears when responses include citations:
- Shows "📚 X Source(s)" for results with citations
- Appears for both CDMS label searches and web searches

### 5. **Updated Footer**
Now mentions:
- Tavily (web search engine)
- CDMS Labels
- USDA Soil Data
- Web Search with Citations

---

## 🎯 Example Queries to Try

### CDMS Label Searches (with Citations):
```
Find me the Roundup pesticide label
Show me the Sevin insecticide label
Get the 2,4-D herbicide label
Find Atrazine label from CDMS
```

### Agriculture Web Searches (with Citations):
```
How to control aphids on tomato plants?
Best practices for corn fertilization timing
How to improve soil organic matter in sandy soils?
When to apply nitrogen fertilizer for soybeans?
What are integrated pest management strategies?
```

### Traditional Queries (still work):
```
What's the weather in Paris?
Show me soil data for Iowa
Tell me about pesticides (RAG search)
```

---

## 📊 What You'll See

### For CDMS Label Searches:
1. **AI Answer:** Natural language response with key information
2. **Labels List:** Direct PDF download links
3. **Citations:** Full formatted citations with URLs
4. **Badges:**
   - 🔧 Tool used (cdms_label)
   - 📊 Confidence score
   - 🔑 Keywords matched
   - 📚 Number of sources (NEW!)

### For Agriculture Web Searches:
1. **AI Answer:** Based on Tavily's AI + multiple sources
2. **Sources List:** Relevant web pages with URLs
3. **Citations:** Full formatted citations
4. **Badges:**
   - 🔧 Tool used (agriculture_web)
   - 📊 Confidence score
   - 🔑 Keywords matched
   - 📚 Number of sources (NEW!)

---

## 🎨 UI Layout

```
┌─────────────────────────────────────────────────┐
│   🤖 Agriculture AI Assistant                   │
│   Your intelligent farming assistant!           │
├─────────────────────────────────────────────────┤
│                                                 │
│   💡 Example Questions [Expandable]             │
│   ┌─────────────────────────────────────────┐  │
│   │ 🔍 Quick Search Tools                   │  │
│   │ [Weather] [Soil Data] [RAG Search]      │  │
│   │                                         │  │
│   │ 🏷️ CDMS Pesticide Labels               │  │
│   │ [Roundup] [Sevin] [2,4-D]              │  │
│   │                                         │  │
│   │ 🌐 Agriculture Web Search               │  │
│   │ [Pest Control] [Fertilization] [Soil]  │  │
│   └─────────────────────────────────────────┘  │
│                                                 │
│   [Ask your question...]                        │
│                                                 │
│   [🔍 Ask]                                      │
│                                                 │
├─────────────────────────────────────────────────┤
│   💬 Conversation                               │
│   ┌─────────────────────────────────────────┐  │
│   │ 👤 You: Find Roundup label              │  │
│   └─────────────────────────────────────────┘  │
│                                                 │
│   ┌─────────────────────────────────────────┐  │
│   │ 🤖 AgAdvisor:                           │  │
│   │ Based on CDMS database, I found 3       │  │
│   │ label(s) for Roundup...                 │  │
│   │                                         │  │
│   │ **Labels Available:**                   │  │
│   │ 1. Roundup QuikPRO - Download: [URL]   │  │
│   │ 2. Roundup PRO - Download: [URL]       │  │
│   │                                         │  │
│   │ **Citations:**                          │  │
│   │ 1. "Roundup QuikPRO..." [URL]          │  │
│   │                                         │  │
│   │ [🔧 cdms_label] [📊 95%] [📚 3 Sources]│  │
│   └─────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## 🔍 Features Explained

### Conversation History
- All messages are saved in session
- User messages: Blue background with 👤
- Assistant messages: Gray background with 🤖
- [Clear Conversation] button to start fresh

### Metadata Badges
Every response shows:
- **Tool Badge** (🔧 green): Which tool was used
- **Confidence Badge** (📊 blue): How confident the matching was
- **Keyword Badge** (🔑 orange): Keywords that triggered the tool
- **Citation Badge** (📚 purple): NEW! Shows number of sources

### Processing Status
When you ask a question, you'll see:
```
🤔 Processing your question...
  1️⃣ Parsing query and extracting keywords...
  2️⃣ Matching keywords with available tools...
  3️⃣ Calling [tool_name] tool...
✅ Complete!
```

### Debug Mode
In the sidebar:
- Toggle "Show Debug Info"
- See session state
- View conversation count
- Inspect last message

---

## 🎯 Tool Matching

The UI uses intelligent tool matching based on keywords:

### CDMS Label Tool (`cdms_label`)
**Triggered by:**
- "label", "pesticide label", "CDMS"
- Product names: "Roundup", "Sevin", "2,4-D", "Atrazine"
- "herbicide label", "insecticide label", "fungicide label"

### Agriculture Web Tool (`agriculture_web`)
**Triggered by:**
- "how to", "best practices", "pest control"
- "fertilizer", "fertilization"
- "soil", "organic matter"
- Agriculture-related questions

### Weather Tool (`weather`)
**Triggered by:**
- "weather", "temperature", "forecast"
- Location names with weather context

### Soil Tool (`soil`)
**Triggered by:**
- "soil data", "soil composition"
- US location names with soil context

### RAG Tool (`rag`)
**Triggered by:**
- General questions not matching other tools
- "tell me about", "what is"
- Default fallback

---

## 💡 Tips for Best Results

### For CDMS Labels:
1. **Include product name:** "Roundup", "Sevin", "2,4-D"
2. **Add "label":** "Find [product] label"
3. **Be specific:** Use brand names, not just active ingredients

### For Agriculture Info:
1. **Ask specific questions:** "How to..." works best
2. **Include crop name:** "for tomatoes", "for corn"
3. **Mention context:** pest name, growth stage, etc.

### For Weather:
1. **Include city name:** "Paris", "London", "New York"
2. **Use weather keywords:** "weather", "temperature"

### For Soil:
1. **US locations work best:** "Iowa", "California"
2. **Include "soil":** "soil data for Iowa"

---

## 🐛 Troubleshooting

### Citations Not Showing?
- Check that you're using CDMS or web search tools
- Weather and soil tools don't include citations (not needed)
- Try a specific CDMS product: "Find Roundup label"

### Wrong Tool Selected?
- Make your query more specific
- Include tool-specific keywords
- Try example buttons to see what works

### App Won't Start?
```bash
# Make sure environment is activated
conda activate agentic

# Check if Streamlit is installed
streamlit --version

# If not, install it
conda env update -f environment.yml
```

### API Errors?
- Verify all API keys in `.env`:
  - `OPENWEATHER_API_KEY`
  - `OPENAI_API_KEY`
  - `TAVILY_API_KEY`
- Check API quotas (especially Tavily: 1000/month free)

---

## 📸 Screenshots (Expected Behavior)

### Before (Old UI):
- Basic example buttons
- No citation badges
- Generic subtitle

### After (New UI):
- 9 organized example buttons (3 sections)
- Purple citation badges
- Specific subtitle mentioning CDMS and citations
- Updated footer with Tavily

---

## ✅ Testing the UI

Try these to verify everything works:

1. **Click "Roundup Label" button**
   - Should show CDMS labels with PDF links
   - Should see purple "📚 3 Source(s)" badge
   - Should see citations in response

2. **Click "Pest Control" button**
   - Should show web search results
   - Should see purple "📚 X Source(s)" badge
   - Should see citations with URLs

3. **Click "Weather" button**
   - Should show weather data
   - No citation badge (not applicable)

4. **Type custom query:** "Find Sevin label"
   - Should match `cdms_label` tool
   - Should return CDMS results with citations

---

## 🎉 Summary

The UI now has:
- ✅ 9 organized example queries (3 categories)
- ✅ CDMS label search examples
- ✅ Agriculture web search examples
- ✅ Citation badge indicator
- ✅ Updated branding and messaging
- ✅ Better user experience

**All Tavily features are now accessible via the UI!** 🚀

---

**Run it now:**
```bash
conda activate agentic
streamlit run src/streamlit_app_conversational.py
```

**Then click any example button to see citations in action!** 🎯


