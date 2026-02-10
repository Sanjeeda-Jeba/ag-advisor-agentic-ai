# 🌾 AgAdvisor - Agentic AI Assistant for Agriculture

An intelligent conversational AI assistant that helps farmers and agricultural professionals access real-time weather data, soil information, pesticide labels, and agricultural best practices through natural language queries.

## 🎯 Overview

AgAdvisor is a multi-tool agentic AI system that combines:
- **Real-time Weather Data** - Get current weather conditions for any location
- **USDA Soil Surveys** - Access official soil data and properties
- **CDMS Pesticide Labels** - Search and download official pesticide product labels
- **Agriculture Knowledge Base** - General agriculture information and best practices
- **Conversational Interface** - ChatGPT-style UI with context-aware follow-up questions
- **Hybrid Parsing** - Fast keyword matching + LLM-based intent classification

## ✨ Key Features

### 🤖 Intelligent Tool Selection
- **Hybrid Parsing System**: Combines fast keyword matching (10-50ms) with LLM classification (200-500ms) for optimal accuracy and speed
- **Context-Aware Follow-ups**: Understands follow-up questions using conversation history
- **Smart Routing**: Automatically selects the right tool based on user intent

### 🌤️ Weather Tool
- Real-time weather data from OpenWeatherMap
- Temperature, humidity, wind speed, conditions
- Supports city names or coordinates

### 🌱 Soil Tool
- Official USDA NRCS soil survey data
- Soil properties: pH, texture, organic matter, nutrients
- Location-based queries with context support

### 🏷️ CDMS Label Tool
- Search California Department of Pesticide Regulation (CDMS) database
- Download official pesticide product labels (PDFs)
- RAG-based search with page citations
- Automatic PDF indexing and vector storage

### 🌐 Agriculture Web Tool
- General agriculture information and best practices
- Pest control strategies, fertilization, crop management
- Web search with full citations

### 💬 Conversational UI
- ChatGPT-style interface with Streamlit
- Multi-chat session support
- Real-time processing status
- Context-aware responses
- Follow-up question handling

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Streamlit Conversational UI                 │
│         (ChatGPT-style interface with history)           │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Hybrid Tool Matcher                          │
│  ┌──────────────┐         ┌──────────────┐             │
│  │ Fast Path    │         │ LLM Path     │             │
│  │ (Keywords)   │◄───────►│ (Intent)     │             │
│  └──────────────┘         └──────────────┘             │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Tool Executor                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Weather  │  │  Soil    │  │  CDMS    │  │  Ag Web │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ OpenWeather │ │ USDA NRCS   │ │   Tavily    │
│    Map      │ │   API       │ │   Search    │
└─────────────┘ └─────────────┘ └─────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       ▼
              ┌─────────────────┐
              │  LLM Response   │
              │   Generator     │
              │   (OpenAI)      │
              └─────────────────┘
```

## 📋 Prerequisites

- Python 3.9+
- Conda (recommended) or pip
- Docker (for Qdrant vector database)
- API Keys:
  - OpenAI API key
  - Tavily API key
  - OpenWeatherMap API key (optional, for weather tool)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd agentic_ai_project
```

### 2. Create Conda Environment

```bash
conda env create -f environment.yml
conda activate agentic
```

### 3. Install Additional Dependencies

```bash
pip install pdfplumber qdrant-client openai tavily-python
python -m spacy download en_core_web_sm
```

### 4. Set Up Environment Variables

```bash
cp env_template.txt .env
```

Edit `.env` and add your API keys:

```env
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here
OPENAI_MODEL_NAME=gpt-4o-mini  # Optional, defaults to gpt-4o-mini
```

### 5. Start Qdrant Vector Database

```bash
# Using Docker
docker run -d -p 6333:6333 qdrant/qdrant

# Or use the provided script
./start_qdrant.sh
```

### 6. (Optional) Index PDFs

```bash
# Download and index CDMS pesticide labels
python src/cdms/document_loader.py
```

## 🎮 Usage

### Start the Application

```bash
streamlit run src/streamlit_app_conversational.py
```

The application will open in your browser at `http://localhost:8501`

### Example Queries

**Weather:**
- "What's the weather in London?"
- "Temperature in Tokyo"
- "Is it raining in New York?"

**Soil Data:**
- "Show me soil data for Iowa"
- "What's the soil pH in California?"
- "Soil properties for Ames, Iowa"

**Pesticide Labels:**
- "Find Roundup label"
- "What's the application rate for Sevin?"
- "Show me Actagro 10% Boron label"
- "Safety precautions for 2,4-D"

**Agriculture Information:**
- "How to control aphids on tomato plants?"
- "Best practices for corn fertilization"
- "Organic pest control methods"

**Follow-up Questions:**
- Q1: "Find Roundup label"
- Q2: "What about safety?" (uses context)
- Q3: "How do I mix it?" (uses context)

## 📁 Project Structure

```
agentic_ai_project/
├── src/
│   ├── streamlit_app_conversational.py  # Main UI application
│   ├── agent_graph.py                   # LangGraph workflow
│   ├── parser.py                        # Query parsing
│   ├── api_clients/                     # API client implementations
│   │   ├── base_client.py              # Base API client
│   │   ├── weather_client.py           # OpenWeatherMap client
│   │   ├── usda_soil_client.py         # USDA NRCS client
│   │   └── tavily_client.py            # Tavily search client
│   ├── tools/                          # Tool implementations
│   │   ├── tool_matcher.py            # Hybrid tool matching
│   │   ├── tool_executor.py           # Tool execution coordinator
│   │   ├── llm_intent_classifier.py   # LLM-based intent classification
│   │   ├── llm_response_generator.py  # LLM response formatting
│   │   ├── weather_tool.py            # Weather tool wrapper
│   │   ├── soil_tool.py               # Soil tool wrapper
│   │   ├── cdms_label_tool.py         # CDMS label search tool
│   │   └── agriculture_web_tool.py    # Agriculture web search
│   ├── cdms/                          # CDMS label system
│   │   ├── document_loader.py        # PDF loader and indexer
│   │   ├── pdf_downloader.py         # PDF downloader
│   │   ├── pdf_processor.py          # PDF text extraction
│   │   ├── rag_search.py             # RAG search implementation
│   │   └── schema.py                  # Database schema
│   ├── rag/                           # RAG system
│   │   ├── embeddings.py             # Embedding generation
│   │   ├── vector_store.py           # Qdrant vector store
│   │   └── hybrid_retriever.py       # Hybrid retrieval
│   ├── utils/                         # Utility functions
│   │   ├── parameter_extractor.py    # Extract params from queries
│   │   └── api_router.py             # API routing
│   └── config/                        # Configuration
│       └── credentials.py            # API key management
├── data/
│   ├── pdfs/                         # Downloaded PDFs
│   │   └── cdms/                     # CDMS labels
│   └── cdms_metadata.db              # SQLite metadata database
├── qdrant_storage/                   # Qdrant vector database storage
├── tests/                            # Test files
├── environment.yml                    # Conda environment
├── env_template.txt                  # Environment variables template
└── README.md                         # This file
```

## 🔧 Configuration

### API Keys

All API keys are stored in `.env` file (not committed to git):

| Service | Required | Free Tier | Sign Up |
|---------|----------|-----------|---------|
| OpenAI | ✅ Yes | Pay-as-you-go | [platform.openai.com](https://platform.openai.com) |
| Tavily | ✅ Yes | 1000 searches/month | [tavily.com](https://tavily.com) |
| OpenWeatherMap | ⚠️ Optional | 60 calls/min | [openweathermap.org](https://openweathermap.org) |

### Hybrid Parsing Configuration

You can configure the hybrid parsing system in `src/tools/tool_matcher.py`:

```python
matcher = ToolMatcher(
    use_llm_fallback=True,        # Enable LLM fallback
    confidence_threshold=0.85,    # High confidence threshold
    llm_threshold=0.6            # Low confidence threshold
)
```

## 🧪 Testing

### Run Individual Tests

```bash
# Test CDMS label search
python test_cdms_tavily.py

# Test follow-up questions
python test_followup_questions_enhanced.py

# Test hybrid parsing
python test_hybrid_parsing.py

# Test soil tool
python test_soil_tool.py

# Test weather tool
python test_weather_tool.py
```

### Test Database Integrity

```bash
# Fix corrupted database if needed
python fix_corrupted_database.py
```

## 🛠️ Technologies Used

- **Streamlit** - Web UI framework
- **OpenAI GPT** - LLM for responses and intent classification
- **Tavily** - Web search API for CDMS labels and agriculture info
- **Qdrant** - Vector database for RAG
- **OpenWeatherMap** - Weather data API
- **USDA NRCS** - Soil survey data API
- **spaCy** - NLP for keyword extraction
- **rapidfuzz** - Fuzzy string matching
- **SQLAlchemy** - Database ORM
- **pdfplumber** - PDF text extraction
- **LangChain** - LLM framework

## 📊 Features in Detail

### Hybrid Parsing System

The system uses a three-tier routing approach:

1. **Fast Path** (>85% confidence): Instant keyword matching (10-50ms, free)
2. **LLM Path** (<60% confidence): LLM intent classification (200-500ms, ~$0.0001)
3. **Hybrid Path** (60-85% confidence): Combines both approaches

**Benefits:**
- 70% of queries use fast path (instant, free)
- 20% use hybrid (100-300ms, minimal cost)
- 10% use LLM (200-500ms, minimal cost)
- Average latency: ~50-150ms
- Cost: ~$0.03-0.30 per 1000 queries

### Follow-up Question Support

All tools support context-aware follow-up questions:

- **Soil Tool**: "soil data for ames" → "Ames iowa" (combines locations)
- **CDMS Tool**: "Roundup label" → "What about safety?" (uses product context)
- **Agriculture Web**: "How to control aphids?" → "What about organic?" (uses topic context)

### CDMS Label System

- **Tavily Search**: Finds CDMS labels via web search
- **PDF Download**: Automatically downloads relevant PDFs
- **Vector Indexing**: Indexes PDFs in Qdrant for RAG
- **Page Citations**: Provides accurate page numbers in responses
- **URL Tracking**: Maintains source URLs for all chunks

## 🐛 Troubleshooting

### Database Corruption

If you see "database disk image is malformed":

```bash
python fix_corrupted_database.py
```

### Qdrant Not Running

```bash
# Check if Qdrant is running
docker ps | grep qdrant

# Start Qdrant
docker run -d -p 6333:6333 qdrant/qdrant
```

### Missing API Keys

Ensure all required API keys are in `.env` file:
- `OPENAI_API_KEY` (required)
- `TAVILY_API_KEY` (required)
- `OPENWEATHER_API_KEY` (optional)

### PDF Processing Issues

If PDFs aren't being indexed:

```bash
# Re-index all PDFs
python src/cdms/document_loader.py
```

