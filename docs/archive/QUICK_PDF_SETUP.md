# Quick PDF Setup Guide

## 🔍 Check if PDFs are Processed

### **Step 1: Check if PDFs Exist**
```bash
ls -la data/pdfs/
```

You should see your PDF files listed.

---

### **Step 2: Process PDFs (RUN THIS!)**

If PDFs exist but haven't been processed, run:

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
📄 Processing: api_documentation.pdf
✅ Success!
   Chunks: 45
   Embeddings: 45
```

---

### **Step 3: Verify Processing**

Check if PDFs were processed:

```bash
# Check database
python -c "
from src.cdms.schema import DatabaseManager
db = DatabaseManager()
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=db.engine)
session = Session()
from src.cdms.schema import Document
docs = session.query(Document).all()
print(f'Documents processed: {len(docs)}')
for d in docs:
    print(f'  - {d.filename}: {d.num_chunks} chunks')
"
```

---

### **Step 4: Test RAG Tool**

After processing, test if RAG works:

```bash
python src/tools/rag_tool.py
```

Or test in the UI:
```bash
streamlit run src/streamlit_app_conversational.py
```

Then ask: "How do I use the weather API?"

---

## ⚠️ Common Issues

### **Issue: "No PDFs found"**
**Solution:** Add PDFs to `data/pdfs/` folder first

### **Issue: "No relevant documentation found"**
**Solution:** Run document loader:
```bash
python src/cdms/document_loader.py
```

### **Issue: "Qdrant not available"**
**Solution:** 
- Start Qdrant: `docker run -d -p 6333:6333 qdrant/qdrant`
- Or it will use in-memory mode (data lost on restart)

### **Issue: "OpenAI API error"**
**Solution:** 
- Check `OPENAI_API_KEY` in `.env`
- Make sure key is valid

---

## 🚀 Quick Command

**One command to process all PDFs:**
```bash
python src/cdms/document_loader.py
```

**Then test:**
```bash
python src/tools/rag_tool.py
```

---

## ✅ Success Indicators

After running document loader, you should see:
- ✅ "Documents processed: X"
- ✅ "Total chunks: X"
- ✅ "Embeddings generated: X"

Then RAG questions will work!

