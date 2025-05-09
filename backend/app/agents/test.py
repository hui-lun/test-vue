import requests
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from app.config import llm
from bs4 import BeautifulSoup

def duckduckgo_search(query: str, max_results: int = 5):
    duck_api = DuckDuckGoSearchAPIWrapper()
    try:
        results = duck_api.results(query, max_results)
        urls = []
        for idx, res in enumerate(results, 1):
            url = res.get("link", "")
            urls.append(url)
        print(f'urls: {urls}')
    except Exception as e:
        raise RuntimeError(f"DuckDuckGo search failed: {e}")
    if not results or not isinstance(results, list):
        raise RuntimeError("No relevant webpages found.")
    return urls

def fetch_url_content(url: str):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        return {'url': url, 'content': soup.get_text(separator=' ', strip=True)}
    except Exception as e:
        return {'url': url, 'content': f"[Error fetching {url}: {e}]"}

def search_and_fetch(query: str, max_results: int = 5):
    try:
        urls = duckduckgo_search(query, max_results)
    except Exception as e:
        return {'error': True, 'message': str(e)}
    contents = []
    for url in urls:
        content_result = fetch_url_content(url)
        if not content_result.get('error'):
            snippet = content_result['content'][:4000]
            contents.append(f"- {snippet}")
    if not contents:
        return {'error': True, 'message': 'All fetch_url_content failed.'}
    search_results_text = "\n".join(contents)
    prompt = (
        f"Based ONLY on the following DuckDuckGo search results, answer the user's question as accurately as possible.\n"
        f"Question: {query}\n"
        f"Search Results:\n{search_results_text}\n"
        f"- Only use information from the search results. Do NOT use any prior knowledge.\n"
        f"- If the answer cannot be found in the search results, do NOT make up an answer. Instead, reply: 'Not enough information in the search results.'\n"
        f"- Summarize the answer in 150 words or less, avoid repeating content.\n"
        f"- Do not include the results number in the answer.\n"
        f"- Do not include the URL in the answer.\n"
    )
    result = llm.invoke(prompt)
    print(f'result: {result}')
    return result.content if hasattr(result, "content") else str(result)

