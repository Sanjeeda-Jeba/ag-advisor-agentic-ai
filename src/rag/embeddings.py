"""
OpenAI Embedding Service
Generates embeddings for text using OpenAI API
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import openai
from typing import List
import tiktoken
import time


class OpenAIEmbeddingService:
    """
    OpenAI Embedding Service using text-embedding-3-small
    
    Usage:
        service = OpenAIEmbeddingService(api_key="your-key")
        embedding = service.generate_embedding("Some text")
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize embedding service
        
        Args:
            api_key: OpenAI API key (optional, loads from .env if not provided)
        """
        if api_key is None:
            from src.config.credentials import CredentialsManager
            creds = CredentialsManager()
            api_key = creds.get_api_key("openai")
        
        self.client = openai.OpenAI(api_key=api_key)
        self.model = "text-embedding-3-small"
        self.encoding = tiktoken.encoding_for_model(self.model)
        self.max_tokens = 8191  # Max tokens per request
        self.dimension = 1536  # Embedding dimension
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
        
        Returns:
            List of floats (embedding vector)
        """
        # Truncate if too long
        tokens = self.encoding.encode(text)
        if len(tokens) > self.max_tokens:
            tokens = tokens[:self.max_tokens]
            text = self.encoding.decode(tokens)
        
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        
        return response.data[0].embedding
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with batching
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch
        
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Truncate each text if needed
            processed_batch = []
            for text in batch:
                tokens = self.encoding.encode(text)
                if len(tokens) > self.max_tokens:
                    tokens = tokens[:self.max_tokens]
                    text = self.encoding.decode(tokens)
                processed_batch.append(text)
            
            response = self.client.embeddings.create(
                model=self.model,
                input=processed_batch
            )
            
            embeddings.extend([item.embedding for item in response.data])
            
            # Rate limiting
            if i + batch_size < len(texts):
                time.sleep(0.1)
        
        return embeddings
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))


# Test function
if __name__ == "__main__":
    print("Testing OpenAI Embedding Service...")
    print("-" * 70)
    
    try:
        service = OpenAIEmbeddingService()
        
        test_text = "This is a test sentence for embedding generation."
        print(f"📝 Text: {test_text}")
        
        embedding = service.generate_embedding(test_text)
        
        print(f"✅ Embedding generated!")
        print(f"   Dimension: {len(embedding)}")
        print(f"   First 5 values: {embedding[:5]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure:")
        print("   1. OPENAI_API_KEY is in .env file")
        print("   2. You have internet connection")
        print("   3. OpenAI API key is valid")

