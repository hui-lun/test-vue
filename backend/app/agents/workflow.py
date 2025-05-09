import os
import logging
from app.agents.nodes import parse_email,select_tool_agent, generate_email_reply
from app.agents.chatstate import ChatState

from langgraph.graph import StateGraph
from langchain_core.runnables.graph import MermaidDrawMethod
from langchain_core.runnables.graph_mermaid import draw_mermaid_png

# Setting logging
logger = logging.getLogger(__name__)


def run_agent_workflow(email_content: str):
    state: ChatState = {
        "email_content": email_content,
        "user_query": email_content,  
        "summary": "",
        "next_node": ""
    }
    logger.info("[Workflow] Initial state: %s", state)    
    try:
        result = workflow.invoke(state)
        logger.info("[Workflow] Final result: %s", result)  
        return result
    except Exception as e:
        logger.error("[Workflow] Exception in workflow.invoke:", exc_info=True)
        return {
            "email_content": email_content,
            "user_query": state.get("user_query", ""),
            "summary": f"Exception: {e}",
            "next_node": "generate_email_reply"
        }

# === Graph Construction ===
graph = StateGraph(ChatState)

# Add nodes
graph.add_node("parse_email", parse_email)
graph.add_node("select_tool_agent", select_tool_agent)
graph.add_node("generate_email_reply", generate_email_reply)
# Set entry point
graph.set_entry_point("parse_email")

graph.add_edge("parse_email", "select_tool_agent")
graph.add_conditional_edges(
    "select_tool_agent",
    lambda state: state["next_node"]
)

workflow = graph.compile()

# Create directory
os.makedirs("/app/graphs", exist_ok=True)

# Saved graph
# dot = workflow.get_graph()
# logger.info("[Workflow] Graph saved to /app/graphs/workflow.png")
# try:
#     mermaid_syntax = dot.draw_mermaid()
#     png_data = draw_mermaid_png(
#         mermaid_syntax=mermaid_syntax,
#         output_file_path='/app/graphs/workflow.png',
#         draw_method=MermaidDrawMethod.API,
#         background_color='white',
#         padding=10
#     )
#     logger.info("[Workflow] Graph saved to /app/graphs/workflow.png")
# except Exception as e:
#     logger.error(f"[Workflow] Error saving graph: {e}")





