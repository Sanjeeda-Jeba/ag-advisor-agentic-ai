"""
Tool Matcher
Routes user questions to appropriate tools based on keyword matching
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Dict, List, Tuple
import re
from rapidfuzz import fuzz


class ToolMatcher:
    """
    Matches user queries to appropriate tools using hybrid approach
    
    Uses keyword-based matching (fast path) and LLM classification (smart path):
    - weather: weather, temperature, forecast, etc.
    - soil: soil, agriculture, farming, pH, etc.
    - rag/documentation: how, what, explain, documentation, etc.
    """
    
    def __init__(
        self, 
        use_llm_fallback: bool = True,
        confidence_threshold: float = 0.85,
        llm_threshold: float = 0.6
    ):
        """
        Initialize tool matcher with hybrid routing
        
        Args:
            use_llm_fallback: Enable LLM fallback for low confidence queries
            confidence_threshold: High confidence threshold (use fast path if above)
            llm_threshold: Low confidence threshold (use LLM if below)
        """
        # Configuration
        self.use_llm_fallback = use_llm_fallback
        self.confidence_threshold = confidence_threshold
        self.llm_threshold = llm_threshold
        
        # Lazy load LLM classifier (only if needed)
        self._llm_classifier = None
        
        # Define tool patterns and keywords
        self.tool_patterns = {
            "weather": {
                "keywords": [
                    "weather", "temperature", "forecast", "climate", "rain", 
                    "sunny", "cloudy", "wind", "humid", "hot", "cold", 
                    "degrees", "celsius", "fahrenheit", "precipitation", 
                    "humidity", "pressure"
                ],
                "description": "Get weather information for any location",
                "priority": 1
            },
            "soil": {
                "keywords": [
                    "soil data", "soil composition", "usda soil", "soil properties",
                    "soil type", "soil texture", "soil ph", "soil nutrient"
                ],
                "description": "Get soil properties and agricultural data",
                "priority": 1
            },
            "cdms_label": {
                "keywords": [
                    "label", "pesticide label", "herbicide label", "insecticide label",
                    "fungicide label", "cdms label", "product label", "epa label",
                    "roundup", "sevin", "2,4-d", "atrazine", "glyphosate", "carbaryl",
                    "find label", "get label", "show label", "download label",
                    "chemical label", "safety data sheet", "sds", "pesticide",
                    "herbicide", "insecticide", "fungicide", "application rate",
                    "safety precautions", "mixing instructions", "re-entry interval"
                ],
                "description": "Search CDMS database for pesticide labels (first priority)",
                "priority": 3  # Highest priority for pesticide/label queries
            },
            "agriculture_web": {
                "keywords": [
                    "how to", "best practices", "pest control", "control pests",
                    "fertilizer", "fertilization", "organic matter", "crop management",
                    "aphids", "tomato", "corn", "wheat", "soybean",
                    "nitrogen", "phosphorus", "potassium", "growing", "planting",
                    "improve soil", "increase yield", "disease control"
                ],
                "description": "Search web for agriculture information",
                "priority": 1
            },
            "rag": {
                "keywords": [
                    "what is", "explain", "tell me about", "information about",
                    "documentation", "guide", "tutorial", "pesticide", "herbicide",
                    "insecticide", "label", "safety"
                ],
                "description": "Search CDMS database for pesticide labels (RAG)",
                "priority": 0  # Lowest priority, fallback option - redirects to CDMS
            }
        }
    
    def _get_llm_classifier(self):
        """Lazy load LLM classifier"""
        if self._llm_classifier is None:
            try:
                from src.tools.llm_intent_classifier import LLMIntentClassifier
                self._llm_classifier = LLMIntentClassifier()
            except Exception as e:
                print(f"⚠️  Could not initialize LLM classifier: {e}")
                return None
        return self._llm_classifier
    
    def _fuzzy_match(self, keywords: List[str], full_query: str, conversation_context: list = None) -> Dict:
        """
        Fast path: Fuzzy keyword matching (existing logic)
        
        Returns:
            Dict with tool_name, confidence, matched_keywords, etc.
        """
        scores = {}
        query_lower = full_query.lower()
        
        # Check if this is a follow-up question
        previous_tool = None
        if conversation_context:
            # Look for tool indicators in previous messages
            for msg in reversed(conversation_context):
                content = msg.get("content", "").lower()
                
                # Check for tool-specific keywords in previous messages
                if any(kw in content for kw in ["roundup", "sevin", "pesticide", "herbicide", 
                                                 "label", "application rate", "safety", "mixing"]):
                    previous_tool = "cdms_label"
                    break
                elif any(kw in content for kw in ["soil", "soil data", "soil properties"]):
                    previous_tool = "soil"
                    break
                elif any(kw in content for kw in ["weather", "temperature", "forecast"]):
                    previous_tool = "weather"
                    break
                elif any(kw in content for kw in ["aphid", "pest", "crop", "fertilizer", "organic"]):
                    previous_tool = "agriculture_web"
                    break
        
        # First, check if this is a pesticide/label question (highest priority)
        pesticide_keywords = [
            "pesticide", "herbicide", "insecticide", "fungicide", "label",
            "roundup", "sevin", "2,4-d", "atrazine", "glyphosate", "carbaryl",
            "application rate", "safety precautions", "mixing instructions",
            "re-entry interval", "chemical", "sds", "safety data sheet"
        ]
        
        is_pesticide_query = any(kw in query_lower for kw in pesticide_keywords)
        
        # If this is a follow-up and query is vague, boost previous tool
        is_vague_followup = (
            previous_tool and 
            (len(full_query.split()) <= 5 or 
             any(phrase in query_lower for phrase in ["what about", "how about", "tell me", "it", "this"]))
        )
        
        # Score each tool based on keyword overlap
        for tool_id, tool_info in self.tool_patterns.items():
            score = 0
            matched_keywords = []
            tool_keywords = tool_info["keywords"]
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                for tool_keyword in tool_keywords:
                    # Use fuzzy matching
                    similarity = fuzz.ratio(keyword_lower, tool_keyword)
                    if similarity > 80:  # 80% similarity threshold
                        score += similarity
                        matched_keywords.append(tool_keyword)
            
            # Also check full query against tool keywords
            for tool_keyword in tool_keywords:
                if tool_keyword in query_lower:
                    score += 50  # Bonus for exact matches in query
                    if tool_keyword not in matched_keywords:
                        matched_keywords.append(tool_keyword)
            
            # Special boost for CDMS if it's a pesticide query
            if tool_id == "cdms_label" and is_pesticide_query:
                score += 200  # Large boost for pesticide queries
            
            # Boost previous tool for follow-up questions
            if is_vague_followup and tool_id == previous_tool:
                score += 150  # Large boost for follow-up to previous tool
            
            # Add priority bonus
            priority = tool_info.get("priority", 0)
            priority_bonus = priority * 10
            
            scores[tool_id] = {
                "score": score + priority_bonus,
                "raw_score": score,
                "priority": priority,
                "matched_keywords": list(set(matched_keywords))
            }
        
        # Get best matching tool
        if not scores or max(s["raw_score"] for s in scores.values()) == 0:
            # If it's a pesticide query, default to CDMS; otherwise agriculture_web
            if is_pesticide_query:
                best_tool = "cdms_label"
                confidence = 0.5
            else:
                best_tool = "agriculture_web"
                confidence = 0.3
        else:
            # Sort by score (includes priority), then by priority if tied
            best_tool = max(scores, key=lambda x: (scores[x]["score"], scores[x]["priority"]))
            max_score = scores[best_tool]["raw_score"]
            # Normalize confidence to 0-1
            confidence = min(max_score / 300, 1.0)
            # Boost confidence if it's a clear match
            if max_score > 100:
                confidence = min(confidence + 0.2, 1.0)
        
        return {
            "tool_name": best_tool,
            "tool_display_name": self.tool_patterns[best_tool]["description"],
            "confidence": confidence,
            "matched_keywords": scores[best_tool]["matched_keywords"],
            "all_scores": scores,
            "raw_score": scores[best_tool]["raw_score"]
        }
    
    def match_tool(
        self, 
        keywords: List[str], 
        full_query: str,
        conversation_context: list = None
    ) -> Dict:
        """
        Match extracted keywords to the best tool using hybrid approach
        
        Flow:
        1. Try fast path (fuzzy matching)
        2. If confidence > threshold: return immediately
        3. If confidence < llm_threshold: use LLM
        4. If in between: combine both results
        
        Args:
            keywords: List of extracted keywords from query
            full_query: Original user question
            conversation_context: Optional list of previous messages for context
        
        Returns:
            Dict with tool_name, confidence, matched_keywords, method, etc.
        """
        # Step 1: Fast path (existing fuzzy matching logic)
        fast_result = self._fuzzy_match(keywords, full_query, conversation_context)
        fast_confidence = fast_result.get("confidence", 0.0)
        
        # Step 2: High confidence - return fast path result immediately
        if fast_confidence >= self.confidence_threshold:
            return {
                **fast_result,
                "method": "fast_path",
                "llm_used": False
            }
        
        # Step 3: Low confidence - use LLM
        if fast_confidence < self.llm_threshold and self.use_llm_fallback:
            llm_classifier = self._get_llm_classifier()
            if llm_classifier:
                llm_result = llm_classifier.classify_intent(
                    full_query, 
                    conversation_context
                )
                
                return {
                    "tool_name": llm_result["tool_name"],
                    "tool_display_name": self.tool_patterns[llm_result["tool_name"]]["description"],
                    "confidence": llm_result["confidence"],
                    "matched_keywords": [],
                    "method": llm_result.get("method", "llm_path"),
                    "llm_used": True,
                    "llm_reasoning": llm_result.get("reasoning", ""),
                    "fast_path_confidence": fast_confidence
                }
            else:
                # LLM not available, return fast path
                return {
                    **fast_result,
                    "method": "fast_path_fallback",
                    "llm_used": False
                }
        
        # Step 4: Medium confidence - hybrid approach
        # Combine fast path and LLM results
        if self.use_llm_fallback:
            llm_classifier = self._get_llm_classifier()
            if llm_classifier:
                llm_result = llm_classifier.classify_intent(
                    full_query,
                    conversation_context
                )
                
                # Weighted combination
                fast_weight = fast_confidence
                llm_weight = llm_result.get("confidence", 0.5)
                
                # If both agree, boost confidence
                if fast_result["tool_name"] == llm_result["tool_name"]:
                    combined_confidence = min(1.0, (fast_weight + llm_weight) / 2 + 0.1)
                    selected_tool = fast_result["tool_name"]
                else:
                    # Disagreement - trust LLM more for ambiguous cases
                    if llm_weight > fast_weight + 0.2:
                        selected_tool = llm_result["tool_name"]
                        combined_confidence = llm_weight
                    else:
                        selected_tool = fast_result["tool_name"]
                        combined_confidence = fast_weight
                
                return {
                    "tool_name": selected_tool,
                    "tool_display_name": self.tool_patterns[selected_tool]["description"],
                    "confidence": combined_confidence,
                    "matched_keywords": fast_result.get("matched_keywords", []),
                    "method": "hybrid",
                    "llm_used": True,
                    "fast_path_result": {
                        "tool": fast_result["tool_name"],
                        "confidence": fast_confidence
                    },
                    "llm_result": {
                        "tool": llm_result["tool_name"],
                        "confidence": llm_weight,
                        "reasoning": llm_result.get("reasoning", "")
                    }
                }
        
        # Fallback: return fast path even if low confidence
        return {
            **fast_result,
            "method": "fast_path_fallback",
            "llm_used": False
        }
    
    def execute_tool(self, tool_name: str, question: str, keywords: List[str]) -> Dict:
        """
        Execute the selected tool (delegates to ToolExecutor)
        
        This is kept for backward compatibility, but ToolExecutor
        should be used directly in the UI
        """
        from src.tools.tool_executor import ToolExecutor
        
        executor = ToolExecutor()
        return executor.execute(tool_name, question)


# Test function
if __name__ == "__main__":
    print("Testing Tool Matcher...")
    print("-" * 70)
    
    from src.utils.parameter_extractor import extract_keywords_from_query
    
    matcher = ToolMatcher()
    
    test_queries = [
        "What's the weather in London?",
        "Show me soil data for Iowa",
        "Find me the Roundup pesticide label",
        "How to control aphids on tomato plants?",
        "Get the Sevin insecticide label",
        "Best practices for corn fertilization",
        "What's the temperature in Tokyo?",
        "Tell me about soil pH in California",
        "Show me 2,4-D herbicide label",
        "How to improve soil organic matter?",
        "Explain the API documentation"
    ]
    
    for query in test_queries:
        keywords = extract_keywords_from_query(query)
        match = matcher.match_tool(keywords, query)
        
        print(f"\n📝 Query: {query}")
        print(f"   Keywords: {keywords}")
        print(f"   → Tool: {match['tool_name']} ({match['confidence']:.0%})")
        print(f"   Matched: {match['matched_keywords'][:3]}")

