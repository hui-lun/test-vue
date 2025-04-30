import logging

from langchain.tools import tool
from langchain.agents.agent import AgentFinish

from app.agents.sql import agent_sql
from app.agents.search import search_and_summarize_advanced

logger = logging.getLogger(__name__)

@tool("run_sql_agent", return_direct=True)
def run_sql_agent(query: str) -> dict:
    """
    Query SQL database and return summary.
    Suitable for: database queries, statistical data, analysis reports, etc.
    """
    logger.info("[Tool Branch] Executing run_sql_agent (SQL query)")
    if not isinstance(query, str) or not query.strip():
        summary = "Please provide a clear query content."
    else:
        try:
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
    # logger.debug("[DEBUG] run_sql_agent - output state: %s", new_state)
    return new_state


@tool("fetch_and_analyze_web_html", return_direct=True)
def fetch_and_analyze_web_html(query: str) -> dict:
    """
    Used for web analysis and external search, returns a brief summary.
    """
    # logger.debug("[DEBUG] fetch_and_analyze_web_html - input query: %s", query)
    # logger.info("[Tool Branch] Executing fetch_and_analyze_web_html (Web analysis/search)")
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
    # logger.debug("[DEBUG] fetch_and_analyze_web_html - output state: %s", new_state)
    return new_state
