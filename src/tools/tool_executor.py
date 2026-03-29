"""
Tool Executor with LLM Response Generation
This is the main execution pipeline that coordinates tools and LLM response generation
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Dict, Optional
import inspect

from src.tools.weather_tool import execute_weather_tool
from src.tools.llm_response_generator import LLMResponseGenerator
# Soil tool imported lazily in __init__ to avoid circular dependencies

_CDMS_TOOL_NAMES = frozenset(
    {"cdms_label", "cdms", "pesticide_label", "rag", "documentation"}
)


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

    def _invoke_tool(
        self,
        tool_name: str,
        user_question: str,
        conversation_context: Optional[list],
    ) -> Dict:
        """Call the registered tool function with optional conversation_context."""
        tool_function = self.tools[tool_name]
        sig = inspect.signature(tool_function)
        if "conversation_context" in sig.parameters:
            return tool_function(
                user_question, conversation_context=conversation_context or []
            )
        return tool_function(user_question)

    def fetch_tool_data(
        self,
        tool_name: str,
        user_question: str,
        conversation_context: Optional[list] = None,
    ) -> Dict:
        """
        Run tool pipeline only (no LLM). Used by the UI to show a distinct
        "gathering data" phase before answer synthesis.
        """
        conversation_context = conversation_context or []
        if tool_name not in self.tools:
            return {
                "success": False,
                "tool_used": tool_name,
                "error": f"Unknown tool: {tool_name}",
                "fallback_used": False,
            }

        try:
            tool_result = self._invoke_tool(
                tool_name, user_question, conversation_context
            )
            effective_tool = tool_name

            if tool_name in _CDMS_TOOL_NAMES:
                cdms_data = tool_result.get("data", {})
                total_chunks = cdms_data.get("total_chunks_found", 0)
                should_fallback = tool_result.get("should_fallback", False)

                print("🔍 CDMS Tool Result Debug:")
                print(f"   success: {tool_result.get('success')}")
                print(f"   total_chunks: {total_chunks}")
                print(f"   should_fallback: {should_fallback}")
                _chunks = cdms_data.get("rag_chunks") or []
                print(f"   has_rag_chunks: {len(_chunks)}")

                if should_fallback:
                    print(
                        "⚠️  CDMS explicitly requested fallback, trying agriculture_web..."
                    )
                    fb = self._fetch_agriculture_web_data_only(
                        user_question, conversation_context
                    )
                    if fb.get("success"):
                        print("✅ Fallback to agriculture_web (data fetch) successful")
                        return {
                            "success": True,
                            "tool_used": "agriculture_web",
                            "data": fb.get("data", {}),
                            "fallback_used": True,
                            "raw_tool_result": fb,
                        }
                    print(
                        "⚠️  Fallback to agriculture_web failed, continuing with CDMS"
                    )
                elif total_chunks == 0:
                    print(
                        "ℹ️  CDMS found 0 chunks, but continuing (may be processing PDFs or have Tavily results)"
                    )

            if not tool_result.get("success"):
                return {
                    "success": False,
                    "tool_used": effective_tool,
                    "error": tool_result.get("error", "Tool execution failed"),
                    "raw_data": tool_result,
                    "fallback_used": False,
                }

            return {
                "success": True,
                "tool_used": effective_tool,
                "data": tool_result.get("data", {}),
                "fallback_used": False,
                "raw_tool_result": tool_result,
            }

        except Exception as e:
            return {
                "success": False,
                "tool_used": tool_name,
                "error": f"Execution error: {str(e)}",
                "fallback_used": False,
            }

    def compose_llm_response(
        self,
        user_question: str,
        tool_used: str,
        tool_data: Dict,
        conversation_context: Optional[list] = None,
    ) -> str:
        """Turn structured tool output into the assistant reply (LLM call)."""
        return self.llm_generator.generate_response(
            user_question=user_question,
            tool_name=tool_used,
            tool_result=tool_data,
            conversation_context=conversation_context or [],
        )

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
        try:
            fetched = self.fetch_tool_data(
                tool_name, user_question, conversation_context
            )
            if not fetched.get("success"):
                return {
                    "success": False,
                    "tool_used": fetched.get("tool_used", tool_name),
                    "error": fetched.get("error", "Tool execution failed"),
                    "raw_data": fetched.get("raw_data"),
                }

            used = fetched["tool_used"]
            data = fetched.get("data", {})
            try:
                llm_response = self.compose_llm_response(
                    user_question, used, data, conversation_context
                )
            except Exception as e:
                return {
                    "success": False,
                    "tool_used": used,
                    "error": str(e),
                    "raw_data": data,
                }

            out = {
                "success": True,
                "tool_used": used,
                "raw_data": data,
                "llm_response": llm_response,
            }
            if fetched.get("fallback_used"):
                out["fallback_used"] = True
            return out

        except Exception as e:
            return {
                "success": False,
                "tool_used": tool_name,
                "error": f"Execution error: {str(e)}",
            }

    def _fetch_agriculture_web_data_only(
        self, user_question: str, conversation_context: Optional[list] = None
    ) -> Dict:
        """Run agriculture_web tool without LLM (for phased UI / fetch_tool_data)."""
        from src.tools.agriculture_web_tool import execute_agriculture_web_tool

        try:
            return execute_agriculture_web_tool(
                user_question, conversation_context=conversation_context or []
            )
        except Exception as e:
            return {"success": False, "error": str(e), "data": {}}

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
            tool_result = self._fetch_agriculture_web_data_only(
                user_question, conversation_context
            )

            if tool_result.get("success"):
                llm_response = self.compose_llm_response(
                    user_question=user_question,
                    tool_used="agriculture_web",
                    tool_data=tool_result.get("data", {}),
                    conversation_context=conversation_context,
                )

                return {
                    "success": True,
                    "tool_used": "agriculture_web",
                    "raw_data": tool_result.get("data", {}),
                    "llm_response": llm_response,
                    "fallback_used": True,
                }
            return {
                "success": False,
                "tool_used": "agriculture_web",
                "error": tool_result.get("error", "Agriculture web search failed"),
            }
        except Exception as e:
            return {
                "success": False,
                "tool_used": "agriculture_web",
                "error": f"Fallback error: {str(e)}",
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

