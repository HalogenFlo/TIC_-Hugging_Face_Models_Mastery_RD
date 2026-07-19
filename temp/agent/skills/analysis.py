# Chức năng: Kỹ năng Phân tích & Trích xuất Điều khoản (Deep Analysis & Extraction Skill).

from typing import Dict, Any, Optional
from tools.search_legal_graph import get_component_context, get_component_actions
from tools.read_document_chunk import read_document_chunk

def execute_deep_analysis(
    comp_id: str,
    file_path: Optional[str] = None,
    chunk_index: int = 0,
    chunk_size: int = 2000
) -> Dict[str, Any]:
    """Tổng hợp ngữ cảnh của một điều luật cùng lịch sử sửa đổi đệ quy và thông tin tài liệu bổ trợ (nếu có)."""
    analysis_result = {
        "comp_id": comp_id,
        "norm_context": {},
        "component_details": {},
        "modifications": [],
        "additional_document": None,
        "error": None
    }
    
    try:
        # 1. Lấy ngữ cảnh văn bản gốc của Component
        context_info = get_component_context(comp_id)
        if context_info:
            analysis_result["norm_context"] = context_info.get("norm", {})
            analysis_result["component_details"] = context_info.get("component", {})
            if context_info.get("error"):
                analysis_result["error"] = context_info.get("error")
                
        # 2. Duyệt đệ quy tìm chuỗi sửa đổi pháp lý hoặc dẫn chiếu chéo
        actions = get_component_actions(comp_id)
        analysis_result["modifications"] = actions
        
        # 3. Đọc tài liệu bổ trợ từ phía người dùng tải lên (nếu được cung cấp)
        if file_path:
            try:
                doc_chunk = read_document_chunk(file_path, chunk_index=chunk_index, chunk_size=chunk_size)
                analysis_result["additional_document"] = doc_chunk
            except Exception as doc_err:
                print(f"[WARNING] Cannot read document chunk in skill analysis: {doc_err}")
                analysis_result["additional_document"] = {
                    "error": str(doc_err),
                    "file_name": file_path
                }
                
        return analysis_result
        
    except Exception as e:
        print(f"[ERROR] execute_deep_analysis failed: {e}")
        analysis_result["error"] = str(e)
        return analysis_result
