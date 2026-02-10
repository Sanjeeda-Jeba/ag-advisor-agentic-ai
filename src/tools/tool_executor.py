"""
Tool Executor with LLM Response Generation
This is the main execution pipeline that coordinates tools and LLM response generation
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Dict
from src.tools.weather_tool import execute_weather_tool
from src.tools.llm_response_generator import LLMResponseGenerator
# Soil tool imported lazily in __init__ to avoid circular dependencies


class ToolExecutor:
    """
    Executes tools and generates natural language responses using LLM
    
    This is the complete pipeline:
    User Question → Tool Execution → LLM Response Generation → User
    """
    
    def __init__(self):
        """Initialize tool executor with LLM response generator"""
        self.llm_generator = LLMResponseGenerator()
        
        # Import tools (lazy import to avoid circular dependencies)
        from src.tools.soil_tool import execute_soil_tool
        from src.tools.cdms_label_tool import execute_cdms_label_tool
        from src.tools.agriculture_web_tool import execute_agriculture_web_tool
        
        # Map of tool names to execution functions
        # Note: RAG tool removed - CDMS is now the RAG tool for pesticide labels
        self.tools = {
            "weather": execute_weather_tool,
            "soil": execute_soil_tool,
            "rag": execute_cdms_label_tool,  # Redirect old RAG to CDMS
            "documentation": execute_cdms_label_tool,  # Redirect to CDMS
            "cdms_label": execute_cdms_label_tool,
            "cdms": execute_cdms_label_tool,  # Alias for cdms_label
            "pesticide_label": execute_cdms_label_tool,  # Alias
            "agriculture_web": execute_agriculture_web_tool,
            "ag_web": execute_agriculture_web_tool,  # Alias
        }
    
    def execute(self, tool_name: str, user_question: str, conversation_context: list = None) -> Dict:
        """
        Execute a tool and generate LLM response
        
        Args:
            tool_name: Name of the tool to execute
            user_question: Original user question
            conversation_context: Optional list of previous messages for context
                Format: [{"role": "user/assistant", "content": "..."}, ...]
        
        Returns:
            Dict with:
            {
                "success": True/False,
                "tool_used": "weather",
                "raw_data": {...},
                "llm_response": "Natural language response from LLM",
                "error": "error message if failed"
            }
        """
        # Check if tool exists
        if tool_name not in self.tools:
            return {
                "success": False,
                "tool_used": tool_name,
                "error": f"Unknown tool: {tool_name}"
            }
        
        try:
            # Step 1: Execute the tool (pass context if tool supports it)
            tool_function = self.tools[tool_name]
            
            # Check if tool function accepts context parameter
            import inspect
            sig = inspect.signature(tool_function)
            if 'conversation_context' in sig.parameters:
                tool_result = tool_function(user_question, conversation_context=conversation_context)
            else:
                tool_result = tool_function(user_question)
            
            # Special handling: If CDMS fails or finds no results, try agriculture_web as fallback
            if tool_name in ["cdms_label", "cdms", "pesticide_label", "rag", "documentation"]:
                cdms_data = tool_result.get("data", {})
                rag_chunks = cdms_data.get("rag_chunks", [])
                total_chunks = cdms_data.get("total_chunks_found", 0)
                should_fallback = tool_result.get("should_fallback", False)
                
                # Debug logging
                print(f"🔍 CDMS Tool Result Debug:")
                print(f"   success: {tool_result.get('success')}")
                print(f"   total_chunks: {total_chunks}")
                print(f"   should_fallback: {should_fallback}")
                print(f"   has_rag_chunks: {len(rag_chunks) if rag_chunks else 0}")
                
                # PHASE 2 FIX: Only fallback if explicitly requested
                # Don't fallback just because no chunks were found - CDMS might still have Tavily results
                # or be processing new PDFs. Only fallback if explicitly requested.
                
                if should_fallback:
                    # Explicitly requested fallback - try agriculture_web
                    print(f"⚠️  CDMS explicitly requested fallback, trying agriculture_web...")
                    fallback_result = self._try_agriculture_web_fallback(
                        user_question, conversation_context
                    )
                    if fallback_result.get("success"):
                        print(f"✅ Fallback to agriculture_web successful")
                        return fallback_result
                    else:
                        print(f"⚠️  Fallback to agriculture_web failed, continuing with CDMS")
                    # If fallback also fails, continue with CDMS error
                else:
                    # No explicit fallback requested - continue with CDMS even if no chunks
                    # CDMS might be downloading/processing PDFs, or Tavily results might be available
                    if total_chunks == 0:
                        print(f"ℹ️  CDMS found 0 chunks, but continuing (may be processing PDFs or have Tavily results)")
            
            # Check if tool execution was successful
            if not tool_result.get("success"):
                return {
                    "success": False,
                    "tool_used": tool_name,
                    "error": tool_result.get("error", "Tool execution failed"),
                    "raw_data": tool_result
                }
            
            # Step 2: Generate LLM response from tool result (with context)
            llm_response = self.llm_generator.generate_response(
                user_question=user_question,
                tool_name=tool_name,
                tool_result=tool_result.get("data", {}),
                conversation_context=conversation_context
            )
            
            # Step 3: Return complete result
            return {
                "success": True,
                "tool_used": tool_name,
                "raw_data": tool_result.get("data", {}),
                "llm_response": llm_response
            }
        
        except Exception as e:
            return {
                "success": False,
                "tool_used": tool_name,
                "error": f"Execution error: {str(e)}"
            }
    
    def _try_agriculture_web_fallback(self, user_question: str, conversation_context: list = None) -> Dict:
        """
        Fallback to agriculture_web tool when CDMS finds no results
        
        Args:
            user_question: User's question
            conversation_context: Optional conversation context
        
        Returns:
            Dict with tool result or failure
        """
        try:
            from src.tools.agriculture_web_tool import execute_agriculture_web_tool
            
            # Try agriculture_web tool (with context for follow-ups)
            tool_result = execute_agriculture_web_tool(user_question, conversation_context=conversation_context)
            
            if tool_result.get("success"):
                # Generate LLM response
                llm_response = self.llm_generator.generate_response(
                    user_question=user_question,
                    tool_name="agriculture_web",
                    tool_result=tool_result.get("data", {}),
                    conversation_context=conversation_context
                )
                
                return {
                    "success": True,
                    "tool_used": "agriculture_web",
                    "raw_data": tool_result.get("data", {}),
                    "llm_response": llm_response,
                    "fallback_used": True  # Indicate this was a fallback
                }
            else:
                return {
                    "success": False,
                    "tool_used": "agriculture_web",
                    "error": tool_result.get("error", "Agriculture web search failed")
                }
        except Exception as e:
            return {
                "success": False,
                "tool_used": "agriculture_web",
                "error": f"Fallback error: {str(e)}"
            }


# Test function
if __name__ == "__main__":
    print("Testing Tool Executor with LLM Response...")
    print("=" * 70)
    
    try:
        executor = ToolExecutor()
        
        test_questions = [
            ("weather", "What's the weather in London?"),
            ("weather", "Is it hot in Dubai today?"),
            ("soil", "Show me soil data for Iowa"),
            ("soil", "What's the soil composition in California?"),
            ("rag", "How do I use the weather API?"),
            ("documentation", "What's the weather API documentation?"),
        ]
        
        for tool_name, question in test_questions:
            print(f"\n{'─' * 70}")
            print(f"📝 Question: {question}")
            print(f"🔧 Tool: {tool_name}")
            print("─" * 70)
            
            result = executor.execute(tool_name, question)
            
            if result["success"]:
                print("✅ Success!")
                print(f"\n🤖 LLM Response:")
                print(f"   {result['llm_response']}")
                
                print(f"\n📊 Raw Data:")
                data = result["raw_data"]
                print(f"   Location: {data.get('city', 'N/A')}")
                print(f"   Temperature: {data.get('temperature', 'N/A')}°C")
                print(f"   Conditions: {data.get('description', 'N/A')}")
            else:
                print(f"❌ Failed: {result['error']}")
        
        print("\n" + "=" * 70)
        print("✅ Testing complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

