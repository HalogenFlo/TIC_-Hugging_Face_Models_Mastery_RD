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

def split_citation_robust(bracketed_text: str):
    """Tách thông minh số hiệu văn bản và điều khoản trích dẫn bên trong dấu ngoặc vuông."""
    bracketed_text = bracketed_text.strip()
    
    # Tìm vị trí bắt đầu của Số hiệu văn bản (luôn chứa định dạng số/năm: ví dụ 103/2014 hoặc 14/2008)
    norm_start_match = re.search(r"\b\d+/\d{4}", bracketed_text)
    
    if norm_start_match:
        norm_start_idx = norm_start_match.start()
        if norm_start_idx > 0:
            # Định dạng: [Điều khoản - Văn bản] (Số hiệu nằm phía sau)
            citation_part = bracketed_text[:norm_start_idx].strip()
            norm_part = bracketed_text[norm_start_idx:].strip()
            
            # Loại bỏ ký tự phân tách thừa ở cuối citation_part
            citation_raw = re.sub(r"\s*[-:,]\s*$", "", citation_part)
            norm_raw = norm_part
            return norm_raw, citation_raw
        else:
            # Định dạng: [Văn bản - Điều khoản] (Số hiệu nằm ở đầu)
            # Tìm vị trí của từ khóa điều khoản đầu tiên
            keyword_pattern = r"(?i)\b(điều|khoản|điểm|chương|mục|phần)\b"
            keyword_match = re.search(keyword_pattern, bracketed_text)
            if keyword_match:
                citation_raw = bracketed_text[keyword_match.start():].strip()
                norm_part = bracketed_text[:keyword_match.start()].strip()
                # Loại bỏ ký tự phân tách thừa ở cuối norm_part
                norm_raw = re.sub(r"\s*[-:,]\s*$", "", norm_part)
                return norm_raw, citation_raw
                
    # Fallback mặc định nếu không có định dạng số/năm chuẩn
    parts = bracketed_text.rsplit("-", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return bracketed_text, ""

def extract_citations(text: str) -> List[Dict[str, str]]:
    """Trích xuất danh sách các trích dẫn tự động từ nội dung phản hồi nháp.
    Hỗ trợ nhiều định dạng phân tách (gạch ngang, phẩy, hai chấm) và bất kể thứ tự trước sau.
    """
    matches = re.findall(r"\[([^\]]+)\]", text)
    
    citations = []
    for match in matches:
        norm_raw, citation_raw = split_citation_robust(match)
        if norm_raw and citation_raw:
            norm_code = clean_norm_code(norm_raw)
            citations.append({
                "raw_match": f"[{match}]",
                "norm_code": norm_code,
                "citation_name": citation_raw
            })
    return citations

def parse_citation_parts(citation_str: str) -> List[str]:
    """Phân tách chuỗi trích dẫn thô thành danh sách các cấp phân cấp (Điều, Khoản, Điểm...).
    Ví dụ: 'Điều 10 Khoản 2 Điểm a' -> ['Điều 10', 'Khoản 2', 'Điểm a']
    """
    # Regex matching cho các cấp trích dẫn pháp luật Việt Nam phổ biến
    patterns = [
        r"Điều\s+\d+[a-zđ]?",
        r"Khoản\s+\d+",
        r"Điểm\s+[a-zđđA-Z]",
        r"Chương\s+[IVXLCDM\d]+",
        r"Mục\s+\d+",
        r"Phần\s+[IVXLCDM\d]+"
    ]
    citation_str = citation_str.replace(",", " ").replace(".", " ")
    found_matches = []
    for pattern in patterns:
        for m in re.finditer(pattern, citation_str, re.IGNORECASE):
            text = m.group(0).strip()
            # Chuẩn hóa chữ cái đầu thành viết hoa (VD: 'điều 10' -> 'Điều 10')
            words = text.split()
            if words:
                words[0] = words[0].capitalize()
                normalized = " ".join(words)
                found_matches.append((m.start(), normalized))
                
    # Sắp xếp theo thứ tự xuất hiện trong chuỗi trích dẫn thô để giữ đúng phân cấp gốc
    found_matches.sort(key=lambda x: x[0])
    parts = [x[1] for x in found_matches]
    
    # Nếu không parse được gì bằng pattern, trả về chuỗi thô
    if not parts:
        parts = [citation_str.strip()]
    return parts

def get_level_weight(part: str) -> int:
    """Xác định trọng số phân cấp của thành phần trích dẫn để tìm kiếm cấp sâu nhất trước."""
    part_lower = part.lower()
    if part_lower.startswith("điểm"):
        return 6
    if part_lower.startswith("khoản"):
        return 5
    if part_lower.startswith("điều"):
        return 4
    if part_lower.startswith("mục"):
        return 3
    if part_lower.startswith("chương"):
        return 2
    if part_lower.startswith("phần"):
        return 1
    return 0

def validate_citations(draft_answer: str, provider: str = DEFAULT_PROVIDER) -> List[Dict[str, Any]]:
    """Quét và đối chiếu các trích dẫn trong draft_answer với dữ liệu gốc trong CSDL Neo4j.
    
    `valid` phản ánh việc tìm thấy đúng văn bản và điều khoản trong CSDL. Điểm cosine chỉ là tín hiệu tham khảo
    để phát hiện nội dung diễn giải có thể lệch nghĩa, không phải bằng chứng pháp lý duy nhất.
    """
    extracted = extract_citations(draft_answer)
    if not extracted:
        return []
        
    results = []
    
    # Câu lệnh Cypher truy vấn nội dung gốc và toàn bộ các node phân cấp trên đường dẫn chứa Component đích
    query = """
    MATCH path = (n:Norm {norm_number: $norm_code})-[:CONTAINS*1..6]->(c:Component)
    WHERE c.citation = $target_citation
    OPTIONAL MATCH (c)-[:HAS_TEXTUNIT]->(t:TextUnit)
    RETURN c.comp_id AS comp_id, 
           t.accumulated_text AS text, 
           t.accumulated_text AS accumulated_text, 
           t.embedding AS embedding,
           [node in nodes(path) WHERE 'Component' in labels(node) | node.citation] AS path_citations
    """
    
    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            for cite in extracted:
                raw_match = cite["raw_match"]
                norm_code = cite["norm_code"]
                citation_name = cite["citation_name"]
                
                # Phân tách trích dẫn thành các cấp nhỏ hơn (VD: Điều 10, Khoản 2)
                parts = parse_citation_parts(citation_name)
                sorted_parts = sorted(parts, key=get_level_weight, reverse=True)
                
                matched_record = None
                fallback_level_used = None
                
                # Cơ chế Graceful Fallback: Thử tìm cấp sâu nhất trước, nếu không có, hạ dần cấp
                for target_citation in sorted_parts:
                    target_weight = get_level_weight(target_citation)
                    # Chỉ yêu cầu những cấp trích dẫn bằng hoặc lớn hơn cấp hiện tại phải khớp trên path
                    required_parts_in_path = [p for p in parts if get_level_weight(p) <= target_weight]
                    
                    res = session.run(query, norm_code=norm_code, target_citation=target_citation)
                    records = list(res)
                    
                    for record in records:
                        path_citations = record["path_citations"]
                        # Kiểm tra xem tất cả các trích dẫn yêu cầu có nằm trong path_citations hay không
                        if all(p in path_citations for p in required_parts_in_path):
                            matched_record = record
                            fallback_level_used = target_citation
                            break
                            
                    if matched_record:
                        break
                
                if not matched_record:
                    # Không tìm thấy bất kỳ cấp điều khoản nào phù hợp trong CSDL
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
                    
                db_text = matched_record["text"] or matched_record["accumulated_text"] or ""
                db_embedding = matched_record["embedding"]
                
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
                    
                    reason_msg = "Tìm thấy trích dẫn trong CSDL"
                    if fallback_level_used != citation_name:
                        reason_msg += f" (graceful fallback khớp tại cấp '{fallback_level_used}')"
                    
                    if is_semantically_close:
                        reason_msg += "; ngữ cảnh diễn giải gần với văn bản gốc."
                    else:
                        reason_msg += "; điểm tương đồng thấp, cần kiểm tra lại phần diễn giải."
                    
                    results.append({
                        "raw_citation": raw_match,
                        "exists": True,
                        "valid": True,
                        "score": float(score),
                        "correct_text": db_text,
                        "reason": reason_msg,
                        "error": None
                    })
                except Exception as e:
                    # Fallback nếu lỗi sinh embedding
                    reason_msg = "Tìm thấy trích dẫn trong CSDL"
                    if fallback_level_used != citation_name:
                        reason_msg += f" (graceful fallback khớp tại cấp '{fallback_level_used}')"
                    reason_msg += " nhưng không tính được điểm tương đồng ngữ nghĩa."
                    
                    results.append({
                        "raw_citation": raw_match,
                        "exists": True,
                        "valid": True,
                        "score": 0.0,
                        "correct_text": db_text,
                        "reason": reason_msg,
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
