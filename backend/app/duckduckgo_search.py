import requests
from typing import List, Dict

def duckduckgo_search(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """
    Use DuckDuckGo Instant Answer API to get search results (web links).
    Returns a list of dicts: [{"title": ..., "url": ...}, ...]
    """
    # DuckDuckGo's official API is limited; for web results, use html scraping or 3rd-party endpoints
    # Here we use a public unofficial API endpoint for demonstration. For production, use a proper package.
    resp = requests.get(
        "https://duckduckgo.com/html/",
        params={"q": query, "kl": "zh-tw"},
        headers={"User-Agent": "Mozilla/5.0"}
    )
    # print(resp.text[:1000])  # 印出前1000字元的 HTML
    # 存成 html 檔案方便用瀏覽器檢查
    # with open("duckduckgo_debug.html", "w", encoding="utf-8") as f:
    #     f.write(resp.text)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(resp.text, "html.parser")
    # 印出所有 <a> 的 class 和 href
    # for a in soup.find_all("a"):
    #     print("a:", a.get("class"), a.get("href"))
    results = []
    import urllib.parse
    for a in soup.select("a.result__a"):
        href = a.get("href")
        title = a.get_text()
        # DuckDuckGo 會用 /l/?uddg= 實際網址
        if href and "/l/?uddg=" in href:
            url = href.split("/l/?uddg=")[-1]
            url = urllib.parse.unquote(url.split('&')[0])
        elif href and href.startswith("http"):
            url = href
        else:
            continue
        # 過濾掉非 http(s) 連結
        if url.startswith("http"):
            results.append({"title": title, "url": url})
        if len(results) >= max_results:
            break
    # print(f"抓到 {len(results)} 筆結果")  # 印出實際抓到的筆數
    return results
