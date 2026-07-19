# Chức năng: Kiểm tra và đối chiếu chéo các trích dẫn pháp luật trong câu trả lời nháp với CSDL Neo4j bằng Cosine Similarity.

import re
import math
from typing import List, Dict, Any
from config import get_neo4j_driver, get_embedding, VALIDATION_SCORE_THRESHOLD, DEFAULT_PROVIDER

def clean_norm_code(code_str: str) -> str:
    """Làm sạch mã hiệu văn bản luật (loại bỏ tiền tố như Thông tư, Nghị định...)."""
    code_str = code_str.strip()
    cleaned = re.sub(r'^(Thông tư|Nghị định|Luật|Quyết định|Thông tư liên tịch)\s+', '', code_str, flags=re.IGNORECASE)
    return cleaned.strip()

def calculate_cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Tính độ tương đồng Cosine giữa hai vector embedding."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude_v1 = math.sqrt(sum(a * a for a in v1))
    magnitude_v2 = math.sqrt(sum(a * a for a in v2))
    
    if magnitude_v1 == 0 or magnitude_v2 == 0:
        return 0.0
        
    return dot_product / (magnitude_v1 * magnitude_v2)

def extract_citations(text: str) -> List[Dict[str, str]]:
    """Trích xuất danh sách các trích dẫn dạng [Văn bản - Điều khoản] từ nội dung phản hồi nháp."""
    # Regex khớp bằng cách phân tách bởi dấu gạch ngang có khoảng trắng xung quanh (ví dụ: ' - ')
    pattern = r"\[([^\]]+?)\s+-\s+([^\]]+)\]"
    matches = re.findall(pattern, text)
    
    citations = []
    for norm_raw, citation_raw in matches:
        norm_code = clean_norm_code(norm_raw)
        citations.append({
            "raw_match": f"[{norm_raw.strip()} - {citation_raw.strip()}]",
            "norm_code": norm_code,
            "citation_name": citation_raw.strip()
        })
    return citations

def validate_citations(draft_answer: str, provider: str = DEFAULT_PROVIDER) -> List[Dict[str, Any]]:
    """Quét và đối chiếu các trích dẫn trong draft_answer với dữ liệu gốc trong CSDL Neo4j.
    
    `valid` phản ánh việc tìm thấy đúng văn bản và điều khoản trong CSDL. Điểm cosine chỉ là tín hiệu tham khảo
    để phát hiện nội dung diễn giải có thể lệch nghĩa, không phải bằng chứng pháp lý duy nhất.
    """
    extracted = extract_citations(draft_answer)
    if not extracted:
        return []
        
    results = []
    
    # Câu lệnh Cypher truy vấn nội dung gốc của điều luật (sử dụng CONTAINS*1..6 cho phân cấp sâu)
    query = """
    MATCH (n:Norm) WHERE n.norm_number = $norm_code
    MATCH (n)-[:CONTAINS*1..6]->(c:Component)
    WHERE c.citation = $citation_name
    OPTIONAL MATCH (c)-[:HAS_TEXTUNIT]->(t:TextUnit)
    RETURN c.comp_id AS comp_id, 
           t.accumulated_text AS text, 
           t.accumulated_text AS accumulated_text, 
           t.embedding AS embedding
    LIMIT 1
    """
    
    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            for cite in extracted:
                raw_match = cite["raw_match"]
                norm_code = cite["norm_code"]
                citation_name = cite["citation_name"]
                
                res = session.run(query, norm_code=norm_code, citation_name=citation_name)
                record = res.single()
                
                if not record:
                    # Không tìm thấy điều khoản này trong CSDL
                    results.append({
                        "raw_citation": raw_match,
                        "exists": False,
                        "valid": False,
                        "score": 0.0,
                        "correct_text": None,
                        "reason": f"Không tìm thấy văn bản {norm_code} hoặc điều khoản {citation_name} trong CSDL Neo4j.",
                        "error": None
                    })
                    continue
                    
                db_text = record["text"] or record["accumulated_text"] or ""
                db_embedding = record["embedding"]
                
                # Tính độ tương đồng để kiểm chứng
                context_start = max(0, draft_answer.find(raw_match) - 100)
                context_end = min(len(draft_answer), draft_answer.find(raw_match) + len(raw_match) + 150)
                draft_context = draft_answer[context_start:context_end]
                
                try:
                    # 1. Sinh embedding cho ngữ cảnh chứa trích dẫn trong bản nháp
                    draft_embedding = get_embedding(draft_context, provider=provider)
                    
                    # 2. Sinh embedding cho văn bản gốc nếu CSDL chưa lưu sẵn vector
                    if not db_embedding or len(db_embedding) == 0:
                        db_embedding = get_embedding(db_text, provider=provider)
                        
                    # 3. Tính toán độ tương đồng Cosine
                    score = calculate_cosine_similarity(draft_embedding, db_embedding)
                    is_semantically_close = score >= VALIDATION_SCORE_THRESHOLD
                    
                    results.append({
                        "raw_citation": raw_match,
                        "exists": True,
                        "valid": True,
                        "score": float(score),
                        "correct_text": db_text,
                        "reason": "Tìm thấy trích dẫn trong CSDL; ngữ cảnh diễn giải gần với văn bản gốc." if is_semantically_close else "Tìm thấy trích dẫn trong CSDL; điểm tương đồng thấp, cần kiểm tra lại phần diễn giải.",
                        "error": None
                    })
                except Exception as e:
                    # Fallback nếu lỗi sinh embedding
                    results.append({
                        "raw_citation": raw_match,
                        "exists": True,
                        "valid": True,
                        "score": 0.0,
                        "correct_text": db_text,
                        "reason": "Tìm thấy trích dẫn trong CSDL nhưng không tính được điểm tương đồng ngữ nghĩa.",
                        "error": str(e)
                    })
    except Exception as db_err:
        print(f"[ERROR] validate_citations database error: {db_err}")
        # Trả về các trích dẫn đều không hợp lệ do lỗi kết nối
        for cite in extracted:
            results.append({
                "raw_citation": cite["raw_match"],
                "exists": False,
                "valid": False,
                "score": 0.0,
                "correct_text": None,
                "reason": f"Lỗi kết nối cơ sở dữ liệu Neo4j: {str(db_err)}",
                "error": str(db_err)
            })
            
    return results
