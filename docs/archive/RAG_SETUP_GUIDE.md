# RAG System Setup Guide

## ✅ RAG System is Complete!

All components have been built. Here's how to set it up:

---

## 🚀 Quick Setup (3 Steps)

### **Step 1: Install Dependencies**
```bash
conda activate agentic
pip install pdfplumber langchain qdrant-client openai tiktoken
```

Or update environment:
```bash
conda env update -f environment.yml --prune
```

### **Step 2: Setup Qdrant (Optional but Recommended)**

**Option A: Docker (Recommended)**
```bash
docker run -d -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/data/qdrant_storage:/qdrant/storage \
    --name qdrant_demo \
    qdrant/qdrant
```

**Option B: Skip Docker**
- System will use in-memory mode automatically
- Less persistent, but works without Docker

### **Step 3: Add PDF Documents**
```bash
# Create folder
mkdir -p data/pdfs

# Add your PDF files
# Copy API docs, guides, manuals, etc. to data/pdfs/
```

---

## 📚 Processing PDFs

### **Process All PDFs:**
```bash
python src/cdms/document_loader.py
```

This will:
1. ✅ Scan `data/pdfs/` folder
2. ✅ Extract text from each PDF
3. ✅ Chunk the content
4. ✅ Generate OpenAI embeddings
5. ✅ Store in Qdrant vector database
6. ✅ Save metadata in SQLite

**Expected output:**
```
📚 Found 3 PDF file(s)
──────────────────────────────────────────────────────────────
📄 Processing: weather_api_docs.pdf
✅ Success!
   Chunks: 45
   Embeddings: 45

📄 Processing: user_guide.pdf
...
```

---

## 🧪 Testing

### **Test Individual Components:**

```bash
# Test PDF processor
python src/cdms/pdf_processor.py

# Test document loader
python src/cdms/document_loader.py

# Test RAG tool
python src/tools/rag_tool.py

# Test full system with LLM
python src/tools/tool_executor.py
```

---

## 💡 Example Usage

### **In Your Code:**
```python
from src.tools.tool_executor import ToolExecutor

executor = ToolExecutor()

# Ask documentation questions
result = executor.execute("rag", "How do I use the weather API?")

if result["success"]:
    print(result["llm_response"])
    # Output: Natural language response based on your PDFs!
```

---

## 📊 What RAG Does

### **For Questions Like:**
- "How do I use the weather API?"
- "What parameters does the API need?"
- "Show me API documentation"
- "How to authenticate?"

### **It Will:**
1. Search your API catalog (fuzzy matching)
2. Search your PDF documents (semantic search)
3. Return relevant matches
4. LLM generates natural language response

---

## 🎯 File Structure

```
data/
├── pdfs/                    # Put your PDFs here
│   ├── api_docs.pdf
│   ├── user_guide.pdf
│   └── ...
├── qdrant_storage/         # Qdrant data (auto-created)
└── cdms_metadata.db        # SQLite database (auto-created)

src/
├── cdms/
│   ├── pdf_processor.py    ✅ PDF extraction
│   ├── schema.py           ✅ Database schema
│   └── document_loader.py   ✅ Main loader
├── rag/
│   ├── embeddings.py       ✅ OpenAI embeddings
│   ├── vector_store.py     ✅ Qdrant integration
│   └── hybrid_retriever.py ✅ Search engine
└── tools/
    └── rag_tool.py         ✅ RAG tool wrapper
```

---

## ✅ Checklist

- [ ] Install dependencies (`pip install pdfplumber langchain qdrant-client`)
- [ ] Setup Qdrant (Docker or skip for in-memory)
- [ ] Add PDF files to `data/pdfs/`
- [ ] Process PDFs (`python src/cdms/document_loader.py`)
- [ ] Test RAG tool (`python src/tools/rag_tool.py`)

---

## 🎉 Ready!

Your RAG system is complete and ready to use! Just add PDFs and process them. 🚀

