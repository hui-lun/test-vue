import os
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict
from langchain_core.agents import AgentFinish
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.agents.agent_types import AgentType
from langchain.prompts import PromptTemplate
from langchain.tools import tool
from langchain_core.runnables.graph import CurveStyle, MermaidDrawMethod, NodeStyles
from langchain_core.runnables.graph_mermaid import draw_mermaid_png
import traceback

# === Define Chat State Schema ===
class ChatState(TypedDict):
    email_content: str
    user_query: str
    summary: str
    next_node: str

llm = ChatOpenAI(
    model="gemma-3-27b-it",
    openai_api_key="EMPTY",
    openai_api_base=os.getenv("VLLM_API_BASE")
)

# === Tool Configuration ===
DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
db = SQLDatabase.from_uri(DATABASE_URL)
toolkit = SQLDatabaseToolkit(llm=llm, db=db)

# Add table info and foreign key hints
table_info = db.get_table_info()
table_info += """
-- Foreign key relationships:
- systeminfo.id → server.system_id
- lan_system_map.lan → system_lan_info.lan_key
- lan_system_map.id → systeminfo.id
- mlan_system_map.mlan → system_mlan_info.mlan_key
- mlan_system_map.id → systeminfo.id
- psu_system_map.psu → system_psu_info.psu_key
- psu_system_map.id → systeminfo.id
- server_pcie_map.pcieinfo → pcie_info.pcie_key
- server_pcie_map.(projectmodel, gbtsn) ↔ server.(projectmodel, gbtsn)
- storage_connector_map.connector → connector_info.connector_key
- storage_connector_map.id → storageinfo.id
- server_storage_map.id → storageinfo.id
- server_storage_map.(projectmodel, gbtsn) ↔ server.(projectmodel, gbtsn)
"""
# === Agent Configuration ===
agent_sql = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
)

def is_natural_query(text: str) -> bool:
    email_indicators = ["subject:", "dear", "regards", "best", "sincerely", "message", "thank you"]
    if any(word in text.lower() for word in email_indicators) or len(text.split("\n")) > 5:
        return False  # It's likely an email
    return True  # It's likely a direct query

# Import tools from agent_tools.py
from .agent_tools import run_sql_agent, fetch_and_analyze_web_html_node

# === Email-to-Query Prompt Template ===
email_parse_prompt = PromptTemplate.from_template("""
From the email below, extract a clear and concise query intention in English that describes what information the user wants from the database.
===
{email}
===
Only respond with the query intention.
""")

parse_chain = email_parse_prompt | llm


# === Node Definitions ===
def parse_email(state: ChatState) -> ChatState:
    # print("[DEBUG] parse_email - input state:", state)
    email = state.get("email_content", "").strip()
    if is_natural_query(email):
        user_query = email
    else:
        response = parse_chain.invoke({"email": email})
        user_query = response.content.strip()
    new_state: ChatState = {
        "email_content": email,
        "user_query": user_query,
        "summary": state.get("summary", ""),
        "next_node": "select_tool"
    }
    # print("[DEBUG] parse_email - output state:", new_state)
    return new_state

def select_tool(state: ChatState) -> ChatState:
    prompt = (
        f"Given the question: '{state['user_query']}', decide which tool to use:\n"
        "1. If the question is about retrieving data from the database, return 'sql_query'.\n"
        "2. If the question requires analyzing web content, return 'web_analysis'.\n"
        "ONLY return the exact tool name without explanation."
    )
    predicted_label = llm.invoke(prompt).content.strip().lower()

    new_state = state.copy()
    if predicted_label == "sql_query":
        new_state["next_node"] = "sql_agent"
    elif predicted_label == "web_analysis":
        new_state["next_node"] = "web_analysis"
    else:
        new_state["next_node"] = "generate_email_reply"
    
    return new_state

def sql_agent_node(state: ChatState) -> ChatState:
    try:
        result = agent_sql.invoke({"input": state["user_query"]})
        if isinstance(result, dict):
            summary = result.get("output", "")
            if not summary:
                summary = str(result)
        else:
            summary = str(result)
    except Exception as e:
        summary = f"Error occurred during SQL query: {e}"
    
    new_state = state.copy()
    new_state["summary"] = summary
    new_state["next_node"] = "generate_email_reply"
    return new_state

def web_analysis_node(state: ChatState) -> ChatState:
    try:
        result = fetch_and_analyze_web_html_node.invoke({"query": state["user_query"]})
        if isinstance(result, dict):
            summary = result.get("summary", str(result))
        else:
            summary = str(result)
    except Exception as e:
        summary = f"Error occurred during web analysis: {e}"
    
    new_state = state.copy()
    new_state["summary"] = summary
    new_state["next_node"] = "generate_email_reply"
    return new_state

def generate_email_reply(state: ChatState) -> ChatState:
    reply = f"""
    Dear Client,

    Thank you for your inquiry. Below is the summarized information based on your request:
    {state.get('summary', '')}

    If you have any further questions, feel free to reach out.

    This email was automatically generated by BDM.chat assistant.
    """
    print("\n=== Generated Email Response ===\n")
    print(reply)
    return state

# === Graph Construction ===
graph = StateGraph(ChatState)

# Add nodes
graph.add_node("parse_email", parse_email)
graph.add_node("select_tool", select_tool)
graph.add_node("sql_agent", sql_agent_node)
graph.add_node("web_analysis", web_analysis_node)
graph.add_node("generate_email_reply", generate_email_reply)

# Set entry point
graph.set_entry_point("parse_email")

# Add edges
graph.add_edge("parse_email", "select_tool")

# Add conditional edges
graph.add_conditional_edges(
    "select_tool",
    lambda state: state["next_node"]
)

# Add edges
graph.add_edge("sql_agent", "generate_email_reply")
graph.add_edge("web_analysis", "generate_email_reply")

# Compile the graph
workflow = graph.compile()

# Create directory
os.makedirs("/app/graphs", exist_ok=True)

# Saved graph
dot = workflow.get_graph()
print('=====================Generate Graph=====================')
try:
    mermaid_syntax = dot.draw_mermaid()
    png_data = draw_mermaid_png(
        mermaid_syntax=mermaid_syntax,
        output_file_path='/app/graphs/workflow.png',
        draw_method=MermaidDrawMethod.API,
        background_color='white',
        padding=10
    )
    print("Graph saved to /app/graphs/workflow.png")
except Exception as e:
    print(f"Error saving graph: {e}")
print('=====================Generate Graph=====================')


def run_agent_workflow(email_content: str):
    state: ChatState = {
        "email_content": email_content,
        "user_query": "",
        "summary": "",
        "next_node": ""
    }
    # print("[DEBUG] Initial workflow state:", state)
    try:
        result = workflow.invoke(state)
        # print("[DEBUG] Final workflow result:", result)
        return result
    except Exception as e:
        print("[ERROR] Exception in workflow.invoke:")
        traceback.print_exc()
        return {
            "email_content": email_content,
            "user_query": state.get("user_query", ""),
            "summary": f"Exception: {e}",
            "next_node": "generate_email_reply"
        }

