from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from .main import llm

def search_and_summarize(query: str, max_results: int = 10) -> str:
    """
    Use DuckDuckGoSearchAPIWrapper to fetch structured search results (with URLs), then summarize with LLM.
    """
    duck_api = DuckDuckGoSearchAPIWrapper()
    try:
        results = duck_api.results(query, max_results)
        # print("[DEBUG] DuckDuckGo results (list):", type(results), results)
    except Exception as e:
        return f"DuckDuckGo 搜尋失敗: {e}"
    if not results or not isinstance(results, list):
        return "找不到相關網頁。"
    # 組 context，清楚標號、標題、網址、摘要
    context = ""
    url_list = []
    for idx, res in enumerate(results, 1):
        title = res.get("title", "")
        snippet = res.get("snippet", "")
        context += f"{idx}. {title}\n{snippet}\n\n"
    prompt = (
        f"Based ONLY on the following DuckDuckGo search results, answer the user's question as accurately as possible.\n"
        f"Question: {query}\n"
        f"Search Results:\n{context}\n"
        f"- Only use information from the search results.\n"
        f"- If the answer cannot be found, reply: 'Not enough information in the search results.'"
    )
    try:
        answer = llm.invoke(prompt)
        answer_text = answer.content if hasattr(answer, "content") else str(answer)
        # return f"查詢到的網址：\n{url_section}\n\nAnswer：\n{answer_text}"
        return answer_text
    except Exception as e:
        return f"LLM 分析失敗: {e}"
