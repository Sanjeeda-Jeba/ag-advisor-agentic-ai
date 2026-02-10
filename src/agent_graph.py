from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from .parser import parse_query

# Define the state of our graph.
class AgentState(TypedDict):
    """Represents the state of our graph."""
    query: str
    parsed_results: dict

def parser_node(state: AgentState):
    """A LangGraph node that performs the query parsing."""
    query = state["query"]
    parsed_results = parse_query(query)
    return {"parsed_results": parsed_results}

# Build the LangGraph
graph_builder = StateGraph(AgentState)

# Add the parser node
graph_builder.add_node("parser_node", parser_node)

# Set the entry and finish points for this simple graph
graph_builder.add_edge(START, "parser_node")
graph_builder.add_edge("parser_node", END)

# Compile the graph
agent_parser = graph_builder.compile()

# Example usage
if __name__ == "__main__":
    user_query = "What's the product stock for the new laptop model?"
    # The LangGraph stream method allows us to see intermediate steps
    for event in agent_parser.stream({"query": user_query}):
        print(event)