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
from langchain.tools import tool
import traceback
from .agent_search import search_and_summarize

# === 定義對話狀態 Schema ===
class ChatState(TypedDict):
    email_content: str
    user_query: str
    summary: str

llm = ChatOpenAI(
    model="gemma-3-27b-it",
    openai_api_key="EMPTY",
    openai_api_base=os.getenv("VLLM_API_BASE")
)

# === 工具設定 ===
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
# === Agent 設定 ===
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


@tool("run_sql_agent", return_direct=True)
def run_sql_agent(query: str) -> dict:
    """
    查詢 SQL 資料庫並回傳摘要。
    適用於：需要查詢資料庫、統計數據、分析報表等需求。
    """
    print("[DEBUG] run_sql_agent - input query:", query)
    if not isinstance(query, str) or not query.strip():
        summary = "請提供明確的查詢內容。"
    else:
        try:
            print("[DEBUG] agent_sql.invoke input:", {"input": query})
            result = agent_sql.invoke({"input": query})
            if isinstance(result, AgentFinish):
                summary = result.return_values.get("output", "")
            elif isinstance(result, dict) and "output" in result:
                summary = result["output"]
            else:
                summary = str(result)
        except Exception as e:
            summary = f"SQL 查詢時發生錯誤: {e}"
    new_state = {
        "email_content": "",
        "user_query": query,
        "summary": summary
    }
    print("[DEBUG] run_sql_agent - output state:", new_state)
    return new_state
@tool("fetch_and_analyze_web_html_node", return_direct=True)
def fetch_and_analyze_web_html_node(query: str) -> dict:
    """
    用於網頁分析與外部搜尋，回傳小部分摘要。
    """
    print("[DEBUG] fetch_and_analyze_web_html_node - input query:", query)
    print("[Tool Branch] 執行 fetch_and_analyze_web_html_node (Web 分析/搜尋)")
    if not isinstance(query, str) or not query.strip():
        summary = "請提供要分析或搜尋的網頁內容或關鍵字。"
    else:
        try:
            summary = search_and_summarize(query)
        except Exception as e:
            summary = f"網頁分析時發生錯誤: {e}"
    new_state = {
        "email_content": "",
        "user_query": query,
        "summary": summary
    }
    print("[DEBUG] fetch_and_analyze_web_html_node - output state:", new_state)
    return new_state

# === 節點定義 ===
def parse_email(state: ChatState) -> ChatState:
    print("[DEBUG] parse_email - input state:", state)
    email = state.get("email_content", "").strip()
    if is_natural_query(email):
        user_query = email
    else:
        response = parse_chain.invoke({"email": email})
        user_query = response.content.strip()
    new_state: ChatState = {
        "email_content": email,
        "user_query": user_query,
        "summary": state.get("summary", "")
    }
    print("[DEBUG] parse_email - output state:", new_state)
    return new_state


def generate_email_reply(state: ChatState) -> ChatState:
    print("[DEBUG] generate_email_reply - input state:", state)
    reply = f"""
    Dear Client,

    Thank you for your inquiry. Below is the summarized server information based on your request:
    {state.get('summary', '')}

    If you have any further questions, feel free to reach out.

    This email was automatically generated by BDM.chat assistant.
    """
    print("\n=== Generated Email Response ===\n")
    print(reply)
    print("[DEBUG] generate_email_reply - output state:", state)
    return state


# === LLM Agent Tool Selection Node ===
from langchain.agents import ZeroShotAgent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# 設定自訂 prompt
prefix = (
    "你是專業的資料查詢與網頁分析助手。你只能根據下列工具來回答問題，請根據描述選擇最適合的工具。"
)
suffix = "問題: {input}\n{agent_scratchpad}"
prompt = ZeroShotAgent.create_prompt(
    [run_sql_agent, fetch_and_analyze_web_html_node],
    prefix=prefix,
    suffix=suffix,
    input_variables=["input", "agent_scratchpad"]
)
llm_chain = LLMChain(llm=llm, prompt=prompt)
agent = ZeroShotAgent(
    llm_chain=llm_chain,
    tools=[run_sql_agent, fetch_and_analyze_web_html_node],
    verbose=True
)
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=[run_sql_agent, fetch_and_analyze_web_html_node],
    verbose=True
)

def extract_summary(summary):
    # 遞迴取 summary string
    while isinstance(summary, dict):
        summary = summary.get("summary", "")
    return summary

def llm_agent_node(state: ChatState) -> ChatState:
    query = state.get("user_query", "")
    print("[DEBUG] llm_agent_node - input state:", state)
    try:
        result = agent_executor.invoke({"input": query})
        if isinstance(result, dict):
            summary = result.get("summary", result.get("output", str(result)))
            summary = extract_summary(summary)
        else:
            summary = str(result)
    except Exception as e:
        summary = f"Agent 執行時發生錯誤: {e}"
    new_state: ChatState = {
        "email_content": state.get("email_content", ""),
        "user_query": query,
        "summary": summary
    }
    print("[DEBUG] llm_agent_node - output state:", new_state)
    return new_state

    
graph = StateGraph(ChatState)
graph.add_node("parse_email", parse_email)
graph.add_node("llm_agent_node", llm_agent_node)
graph.add_node("generate_email_reply", generate_email_reply)

# 入口點
graph.set_entry_point("parse_email")
graph.add_edge("parse_email", "llm_agent_node")
graph.add_edge("llm_agent_node", "generate_email_reply")

workflow = graph.compile()

def run_agent_workflow(email_content: str):
    state: ChatState = {
        "email_content": email_content,
        "user_query": "",
        "summary": ""
    }
    print("[DEBUG] Initial workflow state:", state)
    try:
        result = workflow.invoke(state)
        print("[DEBUG] Final workflow result:", result)
        return result
    except Exception as e:
        print("[ERROR] Exception in workflow.invoke:")
        traceback.print_exc()
        # 你可以選擇回傳一個特殊的 ChatState 或直接 raise
        return {"email_content": email_content, "user_query": state.get("user_query", ""), "summary": f"Exception: {e}"}

