# LangGraph 實作 BDM Chatbot 工作流程（使用 LLM Agent 呼叫 SQL Tool）
import os
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict
from langchain_core.agents import AgentFinish
from langchain.agents import create_sql_agent
from langchain.agents.agent_types import AgentType


# === 定義對話狀態 Schema ===
class ChatState(TypedDict):
    email_content: str
    user_query: str
    summary: str

# === LLM 設定（改用 Gemma-3-27B 本地模型） ===
llm = ChatOpenAI(
    model="gemma-3-27b-it",
    openai_api_key="EMPTY",
    openai_api_base=os.getenv("VLLM_API_BASE")
)

# === 工具設定 ===
DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
db = SQLDatabase.from_uri(DATABASE_URL)
toolkit = SQLDatabaseToolkit(llm=llm, db=db)
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
# === Agent 設定 ===
agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
)

# === 節點定義 ===
def parse_email(state: ChatState) -> ChatState:
    user_query = state.get("email_content", "")
    return ChatState(
        email_content=state.get("email_content", ""),
        user_query=user_query,
        summary=state.get("summary", "")
    )

def run_sql_agent(state: ChatState) -> ChatState:
    query = state.get("user_query", "")
    if not isinstance(query, str):
        raise ValueError("user_query must be a string")

    result = agent.invoke({"input": query})

    if isinstance(result, AgentFinish):
        summary = result.return_values.get("output", "")
    elif isinstance(result, dict) and "output" in result:
        summary = result["output"]
    else:
        summary = str(result)

    return ChatState(
        email_content=state.get("email_content", ""),
        user_query=query,
        summary=summary
    )

def generate_email_reply(state: ChatState) -> ChatState:
    reply = f"""
    Dear Client,

    感謝您的詢問。以下是符合條件的伺服器資訊摘要：
    {state.get('summary', '')}

    若有其他問題，歡迎隨時聯繫。

    本信件由 BDM.chat 智能助理自動生成。
    """
    print("\n=== 準備寄出 Email ===\n")
    print(reply)
    return state

# === LangGraph 定義 ===
graph = StateGraph(ChatState)
graph.add_node("parse_email", parse_email)
graph.add_node("run_sql_agent", run_sql_agent)
graph.add_node("generate_email_reply", generate_email_reply)

graph.set_entry_point("parse_email")
graph.add_edge("parse_email", "run_sql_agent")
graph.add_edge("run_sql_agent", "generate_email_reply")

workflow = graph.compile()

def run_agent_workflow(email_content: str):
    state: ChatState = {
        "email_content": str(email_content),
        "user_query": "",
        "summary": ""
    }
    result = workflow.invoke(state)
    return result