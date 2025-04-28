from langchain.tools import tool
from langchain.agents.agent import AgentFinish

# Import required agents: agent_sql, search_and_summarize
from .agent import agent_sql
from .agent_search import search_and_summarize_advanced

@tool("run_sql_agent", return_direct=True)
def run_sql_agent(query: str) -> dict:
    """
    Query SQL database and return summary.
    Suitable for: database queries, statistical data, analysis reports, etc.
    """
    print("[DEBUG] run_sql_agent - input query:", query)
    if not isinstance(query, str) or not query.strip():
        summary = "Please provide a clear query content."
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
            summary = f"Error occurred during SQL query: {e}"
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
    Used for web analysis and external search, returns a brief summary.
    """
    print("[DEBUG] fetch_and_analyze_web_html_node - input query:", query)
    print("[Tool Branch] Executing fetch_and_analyze_web_html_node (Web analysis/search)")
    if not isinstance(query, str) or not query.strip():
        summary = "Please provide webpage content or keywords to analyze or search."
    else:
        try:
            summary = search_and_summarize_advanced(query)
        except Exception as e:
            summary = f"Error occurred during web analysis: {e}"
    new_state = {
        "email_content": "",
        "user_query": query,
        "summary": summary
    }
    print("[DEBUG] fetch_and_analyze_web_html_node - output state:", new_state)
    return new_state
