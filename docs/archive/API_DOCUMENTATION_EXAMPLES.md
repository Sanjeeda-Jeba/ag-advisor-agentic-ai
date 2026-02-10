# API Documentation - Example Questions

## 📚 Your PDFs Contain

Based on your CDMS labels about "how to use API", here are example questions users can ask:

---

## 🎯 Example Questions for RAG/Documentation Tool

### **API Usage Questions:**
- "How do I use the weather API?"
- "How do I use the API?"
- "Show me how to use the weather API"
- "What's the weather API usage?"

### **API Authentication Questions:**
- "How do I authenticate with the API?"
- "What API key do I need?"
- "How to get API credentials?"
- "API authentication guide"

### **API Parameters Questions:**
- "What parameters does the weather API need?"
- "What are the required parameters for the API?"
- "What parameters do I need to pass?"
- "API parameter requirements"

### **API Documentation Questions:**
- "Show me the API documentation"
- "What's the weather API documentation?"
- "API documentation"
- "Tell me about the API"

### **API Examples Questions:**
- "Show me an example of using the API"
- "API usage example"
- "How to call the API?"
- "API call example"

---

## 🔄 Updated UI Examples

The Streamlit app now includes these example buttons:
- 🌤️ Weather Example
- 🌱 Soil Example  
- 📚 API Documentation
- 🔑 API Authentication
- 📋 API Parameters
- 📖 API Guide

---

## 💡 Tips

When users ask documentation questions:
1. RAG tool searches your PDFs
2. Finds relevant API documentation
3. LLM generates response based on PDF content
4. Cites source document and page

---

## 📝 What the System Will Do

For questions like "How do I use the weather API?":

1. Tool Matcher → Detects "rag" intent
2. RAG Tool → Searches PDFs for API usage info
3. Returns → Relevant excerpts from your PDFs
4. LLM → Generates natural response like:
   > "Based on the documentation, to use the weather API you need to... 
   > (Source: api_documentation.pdf, Page 5)"

---

**The system is ready to answer API documentation questions from your PDFs!** 📚

