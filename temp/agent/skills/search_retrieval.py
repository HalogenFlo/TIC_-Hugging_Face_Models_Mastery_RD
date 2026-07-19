# Chức năng: Kỹ năng Tra cứu & Định vị Văn bản (Legal Search & Retrieval Skill).

from typing import List, Dict, Any, Optional
from tools.search_vector_db import search_vector_db
from tools.web_search_mcp import web_search_mcp
from tools.check_legal_status import check_legal_status
from config import DEFAULT_PROVIDER

def execute_search_retrieval(
    query_text: str,
    provider: str = DEFAULT_PROVIDER,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Đóng gói quy trình kết hợp tìm kiếm ngữ nghĩa Neo4j, kiểm tra hiệu lực pháp lý và fallback web search."""
    retrieved_results = []
    seen_unit_ids = set()
    
    try:
        # 1. Tìm kiếm trên CSDL Vector Neo4j
        vector_results = search_vector_db(query_text, limit=limit, provider=provider)
        
        for item in vector_results:
            uid = item.get("unit_id")
            if uid and uid not in seen_unit_ids:
                seen_unit_ids.add(uid)
                retrieved_results.append({
                    "unit_id": uid,
                    "comp_id": item.get("comp_id"),
                    "accumulated_text": item.get("accumulated_text"),
                    "citation": item.get("citation"),
                    "norm_number": item.get("norm_number"),
                    "norm_type": item.get("norm_type"),
                    "score": item.get("score"),
                    "source": "database"
                })
                
        # 2. Fallback: Nếu không tìm thấy kết quả hoặc kết quả quá ít, gọi tìm kiếm web bổ trợ
        if len(retrieved_results) < limit:
            web_limit = limit - len(retrieved_results)
            web_results = web_search_mcp(query_text, max_results=web_limit, limit_to_trusted=True)
            
            for item in web_results:
                link = item.get("link")
                if link and link not in seen_unit_ids:
                    seen_unit_ids.add(link)
                    retrieved_results.append({
                        "unit_id": link,
                        "comp_id": None,
                        "accumulated_text": item.get("snippet"),
                        "citation": item.get("title"),
                        "norm_number": "Web Source",
                        "norm_type": "Internet",
                        "score": 0.5, # Điểm mặc định cho web search
                        "source": "web"
                    })
                    
        # 3. Với mỗi văn bản tìm được, kiểm tra trạng thái hiệu lực pháp lý thực tế
        # Cache kết quả theo norm_number để tránh truy vấn DB trùng lặp cho cùng một văn bản
        status_cache: Dict[str, Dict[str, Any]] = {}
        final_results = []
        
        for doc in retrieved_results:
            norm_number = doc.get("norm_number")
            validity_status = "Không rõ"
            amended_by = []
            terminated_by = []
            
            # Chỉ kiểm tra CSDL cho những văn bản thực tế trong hệ thống
            if norm_number and norm_number != "Web Source" and doc.get("source") == "database":
                # Kiểm tra cache trước khi gọi DB
                if norm_number not in status_cache:
                    status_cache[norm_number] = check_legal_status(norm_number)
                
                status_info = status_cache[norm_number]
                if status_info.get("exists"):
                    validity_status = status_info.get("validity_status", "Còn hiệu lực")
                    amended_by = status_info.get("amended_by", [])
                    terminated_by = status_info.get("terminated_by", [])
                    
            final_results.append({
                **doc,
                "validity_status": validity_status,
                "amended_by": amended_by,
                "terminated_by": terminated_by
            })
            
        return final_results
        
    except Exception as e:
        print(f"[ERROR] execute_search_retrieval failed: {e}")
        return []

