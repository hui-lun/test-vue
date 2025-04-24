# LangGraph 實作 BDM Chatbot 工作流程（使用 LLM Agent 呼叫 SQL Tool）
import os
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
# from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict
from langchain_core.agents import AgentFinish
# from langchain.agents import create_sql_agent
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.agents.agent_types import AgentType
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain.tools import Tool
from pydantic import BaseModel

from .agent_search import search_and_summarize

# === 定義對話狀態 Schema ===
class ChatState(TypedDict):
    email_content: str
    user_query: str
    summary: str

# === LLM 設定（改用 Gemma-3-27B 本地模型） ===
from .llm_config import llm

# === 工具設定 ===
DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
db = SQLDatabase.from_uri(DATABASE_URL)
toolkit = SQLDatabaseToolkit(llm=llm, db=db)
table_info = db.get_table_info()
table_info += """
try:
    result = agent.invoke({"input": query})
except Exception as e:
    if "operator does not exist" in str(e) and "text > integer" in str(e):
        # 嘗試自動修正 query，將 memoryslotcount cast 成 int
        fixed_query = query.replace("memoryslotcount >", "memoryslotcount::int >")
        result = agent.invoke({"input": fixed_query})
    else:
        raise
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

    # 強化：檢查 summary 是否為空或常見查無資料訊息
    if not summary or "查無資料" in summary or "no data" in summary.lower():
        summary = "查無符合條件的資料，請確認您的查詢內容或換個方式再試一次。"

    return ChatState(
        email_content=state.get("email_content", ""),
        user_query=query,
        summary=summary
    )

import requests

# === 節點定義 ===
def fetch_and_analyze_web_html(state: ChatState) -> ChatState:
    url = state.get("user_query", "")
    if not url or not isinstance(url, str):
        return ChatState(
            email_content=state.get("email_content", ""),
            user_query=url,
            summary="請提供正確的網址"
        )
    try:
        html = requests.get(url, timeout=10).text
    except Exception as e:
        return ChatState(
            email_content=state.get("email_content", ""),
            user_query=url,
            summary=f"無法取得網頁內容: {e}"
        )
    # 讓 LLM 分析 HTML 並產生回應
    prompt = f"請閱讀以下 HTML 並摘要這個網頁的重點內容：\n\n{html[:8000]}"  # 避免 prompt 太長
    try:
        analysis = llm.invoke(prompt)
        if hasattr(analysis, "content"):
            summary = analysis.content
        else:
            summary = str(analysis)
    except Exception as e:
        summary = f"LLM 分析失敗: {e}"
    return ChatState(
        email_content=state.get("email_content", ""),
        user_query=url,
        summary=summary
    )

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
def fetch_and_analyze_web_html_node(state: ChatState) -> ChatState:
    query = state.get("user_query", "")
    summary = search_and_summarize(query)
    return ChatState(
        email_content=state.get("email_content", ""),
        user_query=query,
        summary=summary
    )

graph = StateGraph(ChatState)

# === 將流程圖存成 PDF ===

graph.add_node("parse_email", parse_email)
graph.add_node("run_sql_agent", run_sql_agent)
graph.add_node("generate_email_reply", generate_email_reply)
graph.add_node("fetch_and_analyze_web_html_node", fetch_and_analyze_web_html_node)

graph.set_entry_point("parse_email")
graph.add_edge("parse_email", "run_sql_agent")
graph.add_edge("parse_email", "fetch_and_analyze_web_html_node")
graph.add_edge("run_sql_agent", "generate_email_reply")

workflow = graph.compile()

# try:
#     graph.get_graph().draw_png("my_langgraph.png")
#     print("流程圖已儲存為 my_langgraph.png")
# except Exception as e:
#     print("流程圖儲存失敗。")
#     print(e)

def run_agent_workflow(email_content: str):
    state: ChatState = {
        "email_content": str(email_content),
        "user_query": "",
        "summary": ""
    }
    result = workflow.invoke(state)
    return result