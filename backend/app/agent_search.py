from .duckduckgo_search import duckduckgo_search
import requests
from .agent import llm

def search_and_summarize(query: str, max_results: int = 3) -> str:
    """
    1. 以 DuckDuckGo 搜尋 query
    2. 取得前幾個網址內容
    3. 用 LLM 摘要內容
    """
    results = duckduckgo_search(query, max_results=max_results)
    if not results:
        return "找不到相關網頁。"
    all_summaries = []
    for res in results:
        url = res['url']
        title = res['title']
        try:
            html = requests.get(url, timeout=10).text
        except Exception as e:
            all_summaries.append(f"【{title}】({url})\n無法取得內容: {e}")
            continue
        # 過濾明顯無效的 HTML
        if (not html or 
            '403 Forbidden' in html or 
            '404 Not Found' in html or 
            '<meta' in html and len(html.strip()) < 2000):
            all_summaries.append(f"【{title}】({url})\n此頁面內容無法取得或不包含有效資訊，已自動跳過。")
            continue
        prompt = f"請根據下列問題，閱讀 HTML 並根據內容回答問題：\n問題：{query}\n\nHTML：\n{html[:8000]}\n\n若無法從本頁找到答案，請簡短說明並建議使用者提供更明確的產品頁面。"
        try:
            analysis = llm.invoke(prompt)
            summary = analysis.content if hasattr(analysis, "content") else str(analysis)
        except Exception as e:
            summary = f"LLM 分析失敗: {e}"
        all_summaries.append(f"【{title}】({url})\n{summary}")
    return "\n\n".join(all_summaries)
