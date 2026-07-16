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
    """Quét và đối chiếu các trích dẫn trong draft_answer với dữ liệu gốc trong CSDL Neo4j."""
    extracted = extract_citations(draft_answer)
    if not extracted:
        return []
        
    driver = get_neo4j_driver()
    results = []
    
    # Câu lệnh Cypher truy vấn nội dung gốc của điều luật
    query = """
    MATCH (n:Norm) WHERE n.norm_number = $norm_code
    MATCH (n)-[:CONTAINS]->(c:Component)
    WHERE c.citation = $citation_name
    OPTIONAL MATCH (c)-[:HAS_TEXTUNIT]->(t:TextUnit)
    RETURN c.comp_id AS comp_id, 
           t.accumulated_text AS text, 
           t.accumulated_text AS accumulated_text, 
           t.embedding AS embedding
    LIMIT 1
    """
    
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
                    "valid": False,
                    "score": 0.0,
                    "correct_text": None,
                    "reason": f"Không tìm thấy văn bản {norm_code} hoặc điều khoản {citation_name} trong CSDL Neo4j."
                })
                continue
                
            db_text = record["text"] or record["accumulated_text"] or ""
            db_embedding = record["embedding"]
            
            # Tính độ tương đồng để kiểm chứng
            # LLM sử dụng trích dẫn, ta so khớp ngữ nghĩa của câu trả lời nháp (hoặc ngữ cảnh xung quanh)
            # Trong tool thô này, ta sẽ so khớp chính nội dung trích dẫn trong draft_answer với văn bản gốc
            # Ta lấy 150 ký tự xung quanh trích dẫn trong draft_answer để so khớp
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
                is_valid = score >= VALIDATION_SCORE_THRESHOLD
                
                results.append({
                    "raw_citation": raw_match,
                    "valid": bool(is_valid),
                    "score": float(score),
                    "correct_text": db_text,
                    "reason": "Trích dẫn chính xác" if is_valid else "Nội dung trích dẫn bị sai lệch ngữ nghĩa so với văn bản gốc."
                })
            except Exception as e:
                # Fallback nếu lỗi sinh embedding
                results.append({
                    "raw_citation": raw_match,
                    "valid": False,
                    "score": 0.0,
                    "correct_text": db_text,
                    "reason": f"Lỗi trong quá trình kiểm chứng ngữ nghĩa: {str(e)}"
                })
                
    return results
