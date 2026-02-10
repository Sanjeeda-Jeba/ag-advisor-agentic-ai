#!/usr/bin/env python3
"""
Re-process PDFs to store embeddings in Qdrant
Run this if Qdrant was empty when PDFs were first processed
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("🔄 Re-processing PDFs to store embeddings in Qdrant...")
print("=" * 70)
print("\n⚠️  This will:")
print("   - Process all PDFs in data/pdfs/")
print("   - Generate embeddings using OpenAI API")
print("   - Store embeddings in Qdrant")
print("   - May take a few minutes and use API credits")
print("\n" + "=" * 70)

# Check if Qdrant is running
try:
    from qdrant_client import QdrantClient
    client = QdrantClient(host='localhost', port=6333, timeout=5)
    _ = client.get_collections()
    print("✅ Qdrant is running!")
except Exception as e:
    print(f"❌ Qdrant is not running!")
    print(f"   Error: {e}")
    print("\n💡 Start Qdrant first:")
    print("   ./start_qdrant.sh")
    print("   or")
    print("   docker run -d --name qdrant -p 6333:6333 qdrant/qdrant")
    sys.exit(1)

# Check OpenAI key
try:
    from src.config.credentials import CredentialsManager
    creds = CredentialsManager()
    api_key = creds.get_api_key("openai")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env file!")
        sys.exit(1)
    print("✅ OpenAI API key found")
except Exception as e:
    print(f"❌ Error checking OpenAI key: {e}")
    sys.exit(1)

# Process PDFs
print("\n" + "=" * 70)
print("📚 Processing PDFs...")
print("=" * 70)

try:
    from src.cdms.document_loader import DocumentLoader
    
    loader = DocumentLoader()
    result = loader.load_all_pdfs(force_reprocess=True)  # Force re-process even if already processed
    
    if result.get("success"):
        print("\n" + "=" * 70)
        print("✅ SUCCESS!")
        print("=" * 70)
        print(f"   Files processed: {result['successful']}/{result['total_files']}")
        print(f"   Total chunks: {result['total_chunks']}")
        print(f"   Embeddings generated: {result['total_embeddings']}")
        
        if result['total_embeddings'] > 0:
            print("\n🎉 PDFs are now searchable in Qdrant!")
            print("\n💡 Test it:")
            print("   python src/tools/rag_tool.py")
            print("   or")
            print("   streamlit run src/streamlit_app_conversational.py")
        else:
            print("\n⚠️  No embeddings were generated!")
            print("   Check if OpenAI API key is valid")
    else:
        print(f"\n❌ Error: {result.get('error')}")
        sys.exit(1)
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

