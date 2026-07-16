# Chức năng: Tìm kiếm thông tin trên Internet sử dụng Tavily Search API.

from typing import List, Dict, Any
import urllib.request
import json
import os

TRUSTED_DOMAINS = [
    "vbpl.vn",
    "thuvienphapluat.vn",
    "chinhphu.vn",
    "mof.gov.vn",    
    "gdt.gov.vn"       
]

def web_search_mcp(
    query: str, 
    max_results: int = 5, 
    limit_to_trusted: bool = True, 
    search_depth: str = "basic"
) -> List[Dict[str, Any]]:
    """Tìm kiếm thông tin trên Internet qua Tavily API và trả về snippets kèm liên kết nguồn."""
    # Đọc API Key từ biến môi trường
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key or api_key.strip() == "":
        print("[WARNING] Missing TAVILY_API_KEY in .env file. Skipping web search.")
        return []
        
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": search_depth,
        "max_results": max_results
    }
    
    # Lọc tên miền uy tín tại Việt Nam trực tiếp phía API của Tavily
    if limit_to_trusted and TRUSTED_DOMAINS:
        payload["include_domains"] = TRUSTED_DOMAINS
        
    headers = {
        "Content-Type": "application/json"
    }
    
    # Cấu hình proxy từ biến môi trường (nếu có)
    proxy_url = os.getenv("WEB_SEARCH_PROXY")
    if proxy_url and proxy_url.strip() != "":
        proxy_handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
        opener = urllib.request.build_opener(proxy_handler)
        urllib.request.install_opener(opener)
        
    results = []
    seen_links = set() # Tập hợp để lọc trùng lặp URL
    
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode('utf-8'), 
            headers=headers, 
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            search_results = res_data.get("results", [])
            for r in search_results:
                link = r.get("url")
                # Chỉ thêm nếu URL chưa từng xuất hiện để tránh trùng lặp thông tin
                if link and link not in seen_links:
                    seen_links.add(link)
                    results.append({
                        "title": r.get("title"),
                        "link": link,
                        "snippet": r.get("content")
                    })
    except Exception as e:
        print(f"[WARNING] Error executing Tavily search: {e}")
        # Cơ chế Fallback 1: Nếu lọc domain bị lỗi kết nối, thử tìm kiếm tự do
        if limit_to_trusted:
            print("[INFO] Retrying free search without domain limits on Tavily...")
            return web_search_mcp(query, max_results=max_results, limit_to_trusted=False, search_depth=search_depth)
        return []
        
    # Cơ chế Fallback 2: Nếu lọc domain chạy thành công nhưng không trả về kết quả nào
    if limit_to_trusted and not results:
        print("[INFO] No results found from trusted domains. Switching to free search on Tavily...")
        return web_search_mcp(query, max_results=max_results, limit_to_trusted=False, search_depth=search_depth)
        
    return results
