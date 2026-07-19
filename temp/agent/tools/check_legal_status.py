# Chức năng: Kiểm tra trạng thái hiệu lực pháp lý thực tế của văn bản pháp luật (Norm) từ Neo4j.

from typing import Dict, Any, List
from config import get_neo4j_driver

def check_legal_status(code: str) -> Dict[str, Any]:
    """Kiểm tra trạng thái hiệu lực của văn bản pháp luật và tìm các văn bản thay thế/bãi bỏ (nếu có)."""
    status_info = {
        "code": code,
        "exists": False,
        "type": None,
        "validity_status": "Không rõ (Chưa có thông tin trong CSDL)",
        "terminated_by": [],
        "amended_by": [],
        "error": None
    }
    
    try:
        driver = get_neo4j_driver()
        
        # 1. Truy vấn trạng thái hiệu lực hiện tại trên node Norm
        query_status = """
        MATCH (n:Norm) WHERE n.norm_number = $code
        RETURN n.norm_number AS code, 
               n.norm_type AS type, 
               n.validity_status AS validity_status
        LIMIT 1
        """
        
        # 2. Tìm các văn bản bãi bỏ hoặc bãi bỏ một phần văn bản này
        query_termination = """
        MATCH (n:Norm) WHERE n.norm_number = $code
        MATCH (terminator:Norm)-[r:TERMINATES|PARTIALLY_TERMINATES]->(n)
        RETURN terminator.norm_number AS code, terminator.norm_type AS type, type(r) AS rel_type
        """
        
        # 3. Tìm các văn bản sửa đổi, bổ sung văn bản này
        query_amendment = """
        MATCH (n:Norm) WHERE n.norm_number = $code
        MATCH (amender:Norm)-[r:AMENDS|SUPPLEMENTS]->(n)
        RETURN amender.norm_number AS code, amender.norm_type AS type, type(r) AS rel_type
        """
        
        with driver.session() as session:
            # Lấy trạng thái cơ bản
            res_status = session.run(query_status, code=code)
            record = res_status.single()
            if record:
                status_info["exists"] = True
                status_info["type"] = record["type"]
                # Nếu validity_status là None, để mặc định "Không rõ"
                if record["validity_status"]:
                    status_info["validity_status"] = record["validity_status"]
                else:
                    status_info["validity_status"] = "Đang áp dụng (Mặc định)"
                    
                # Lấy thông tin bãi bỏ
                res_term = session.run(query_termination, code=code)
                for r in res_term:
                    status_info["terminated_by"].append({
                        "code": r["code"],
                        "type": r["type"],
                        "action": "BÃI BỎ HOÀN TOÀN" if r["rel_type"] == "TERMINATES" else "BÃI BỎ MỘT PHẦN"
                    })
                    
                # Lấy thông tin sửa đổi
                res_amend = session.run(query_amendment, code=code)
                for r in res_amend:
                    status_info["amended_by"].append({
                        "code": r["code"],
                        "type": r["type"],
                        "action": "SỬA ĐỔI" if r["rel_type"] == "AMENDS" else "BỔ SUNG"
                    })
    except Exception as e:
        print(f"[ERROR] check_legal_status failed: {e}")
        status_info["error"] = str(e)
        
    return status_info
