"""
LLM Intent Classifier
Uses LLM to classify user intent and select appropriate tool
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import openai
import json
import hashlib
from typing import Dict, List, Optional
from src.config.credentials import CredentialsManager
import os


class LLMIntentClassifier:
    """
    Classifies user queries using LLM to determine intent and select tool
    """
    
    def __init__(self, api_key: str = None, model: str = None):
        """
        Initialize LLM Intent Classifier
        
        Args:
            api_key: OpenAI API key (optional, loads from .env if not provided)
            model: OpenAI model to use (default: gpt-4o-mini for cost efficiency)
        """
        if api_key is None:
            creds = CredentialsManager()
            api_key = creds.get_api_key("openai")
        
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model or os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
        self.cache = {}  # Simple in-memory cache (can be upgraded to Redis later)
        self.cache_size_limit = 1000  # Limit cache size
    
    def classify_intent(
        self, 
        query: str, 
        conversation_context: list = None
    ) -> Dict:
        """
        Classify user intent and select appropriate tool using LLM
        
        Args:
            query: User's query
            conversation_context: Optional conversation history
        
        Returns:
            Dict with tool_name, confidence, reasoning, method
        """
        # Check cache first
        cache_key = self._generate_cache_key(query, conversation_context)
        if cache_key in self.cache:
            cached_result = self.cache[cache_key].copy()
            cached_result["method"] = "llm_cached"
            return cached_result
        
        # Build prompt
        prompt = self._build_classification_prompt(query, conversation_context)
        
        # Call LLM
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent classification
                max_tokens=200,
                response_format={"type": "json_object"}  # Force JSON response
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate and normalize result
            result = self._validate_result(result)
            
            # Cache result (with size limit)
            if len(self.cache) >= self.cache_size_limit:
                # Remove oldest entry (simple FIFO)
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            
            self.cache[cache_key] = result.copy()
            result["method"] = "llm"
            
            return result
            
        except json.JSONDecodeError as e:
            # If LLM doesn't return valid JSON, fallback
            print(f"⚠️  LLM returned invalid JSON: {e}")
            return {
                "tool_name": "agriculture_web",
                "confidence": 0.5,
                "reasoning": "LLM classification failed: invalid JSON response",
                "method": "fallback"
            }
        except Exception as e:
            # Fallback to default
            print(f"⚠️  LLM classification error: {e}")
            return {
                "tool_name": "agriculture_web",
                "confidence": 0.5,
                "reasoning": f"LLM classification failed: {str(e)}",
                "method": "fallback"
            }
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for tool classification"""
        return """You are an expert at classifying user queries and selecting the appropriate tool.

Available tools:
1. weather - For weather, temperature, forecast, climate queries (e.g., "What's the weather in London?", "Temperature in Tokyo")
2. soil - For soil data, soil properties, agricultural soil information (e.g., "Show me soil data for Iowa", "Soil pH in California")
3. cdms_label - For pesticide labels, herbicide labels, product labels, safety data sheets (e.g., "Find Roundup label", "What's the application rate for Sevin?", "Safety precautions for 2,4-D")
4. agriculture_web - For general agriculture questions, best practices, farming advice (e.g., "How to control aphids?", "Best practices for corn fertilization")

Return a JSON object with:
- tool_name: one of the tool names above (exactly as listed)
- confidence: float between 0.0 and 1.0 indicating how confident you are
- reasoning: brief explanation (1-2 sentences) of why this tool was selected

Be especially careful with follow-up questions - use the conversation context to understand what the user is asking about."""
    
    def _build_classification_prompt(
        self, 
        query: str, 
        context: list = None
    ) -> str:
        """Build classification prompt"""
        prompt = f"Classify this user query and select the best tool:\n\n"
        prompt += f"Query: {query}\n\n"
        
        if context:
            prompt += "Conversation context:\n"
            for i, msg in enumerate(context[-3:], 1):  # Last 3 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")[:200]  # Truncate long messages
                prompt += f"{i}. {role}: {content}\n"
            prompt += "\n"
            prompt += "Consider the conversation context when classifying. If this is a follow-up question, use context to understand what the user is asking about.\n\n"
        
        prompt += "Return your response as JSON with tool_name, confidence, and reasoning fields."
        
        return prompt
    
    def _validate_result(self, result: Dict) -> Dict:
        """Validate and normalize LLM result"""
        valid_tools = ["weather", "soil", "cdms_label", "agriculture_web"]
        
        tool_name = result.get("tool_name", "agriculture_web")
        if tool_name not in valid_tools:
            # Try to map common variations
            tool_name_lower = tool_name.lower()
            if "weather" in tool_name_lower or "temperature" in tool_name_lower:
                tool_name = "weather"
            elif "soil" in tool_name_lower:
                tool_name = "soil"
            elif "cdms" in tool_name_lower or "label" in tool_name_lower or "pesticide" in tool_name_lower:
                tool_name = "cdms_label"
            else:
                tool_name = "agriculture_web"  # Default fallback
        
        confidence = float(result.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1
        
        reasoning = result.get("reasoning", "No reasoning provided")
        
        return {
            "tool_name": tool_name,
            "confidence": confidence,
            "reasoning": reasoning
        }
    
    def _generate_cache_key(self, query: str, context: list = None) -> str:
        """Generate cache key for query"""
        # Normalize query
        query_normalized = query.lower().strip()
        
        # Include context if present (last message only for cache key to keep it simple)
        if context:
            last_msg = context[-1].get("content", "")[:50] if context else ""
            cache_str = f"{query_normalized}||{last_msg}"
        else:
            cache_str = query_normalized
        
        # Generate hash
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def clear_cache(self):
        """Clear the classification cache"""
        self.cache.clear()
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            "cache_size": len(self.cache),
            "cache_limit": self.cache_size_limit,
            "cache_usage": len(self.cache) / self.cache_size_limit
        }


# Test function
if __name__ == "__main__":
    print("=" * 80)
    print("Testing LLM Intent Classifier")
    print("=" * 80)
    
    classifier = LLMIntentClassifier()
    
    test_queries = [
        "What's the weather in London?",
        "Show me soil data for Iowa",
        "Find the Roundup pesticide label",
        "How to control aphids on tomato plants?",
        "What about safety?",  # Follow-up (needs context)
    ]
    
    # Test with context
    context = [
        {
            "role": "user",
            "content": "What's the application rate for Roundup?"
        },
        {
            "role": "assistant",
            "content": "The application rate for Roundup is 1.5-2.5 quarts per acre..."
        }
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 80)
        
        # Test without context
        result = classifier.classify_intent(query)
        print(f"   Tool: {result['tool_name']}")
        print(f"   Confidence: {result['confidence']:.0%}")
        print(f"   Reasoning: {result['reasoning']}")
        print(f"   Method: {result.get('method', 'unknown')}")
        
        # Test with context for follow-up
        if "What about" in query:
            print(f"\n   With context:")
            result_with_context = classifier.classify_intent(query, context)
            print(f"   Tool: {result_with_context['tool_name']}")
            print(f"   Confidence: {result_with_context['confidence']:.0%}")
            print(f"   Reasoning: {result_with_context['reasoning']}")
    
    print("\n" + "=" * 80)
    print("Cache Stats:", classifier.get_cache_stats())
    print("=" * 80)
