# Chức năng: Định nghĩa cấu trúc dữ liệu dùng chung AgentState cho LangGraph.

from typing import TypedDict, List, Dict, Any, Annotated, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


def merge_dict(left: Optional[Dict[str, Any]], right: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Gộp hai dictionary từ các Agent chạy song song thay vì ghi đè."""
    return {**(left or {}), **(right or {})}

def merge_list(left: Optional[List[Any]], right: Optional[List[Any]]) -> List[Any]:
    """Gộp hai danh sách từ các Agent chạy song song thay vì ghi đè."""
    return (left or []) + (right or [])


# --- ĐỊNH NGHĨA GLOBAL AGENT STATE ---

class AgentState(TypedDict):
    # --- THÔNG TIN NGƯỜI DÙNG & CÁ NHÂN HÓA ---
    user_id: str
    user_profile: Dict[str, Any]
    
    messages: Annotated[List[BaseMessage], add_messages]

    raw_query: str
    refined_query: str
    
    # --- ĐIỀU PHỐI (Orchestrator) ---
    effort_level: str                                     # "bypass" | "simple" | "complex"
    clarification_count: int     
    detected_domains: Annotated[List[str], merge_list]
    
    # --- KẾT QUẢ TỪ CÁC SUB-AGENTS (Gộp song song) ---
    domain_outputs: Annotated[Dict[str, Any], merge_dict]
    conflicts: Annotated[List[Dict[str, Any]], merge_list]
    
    # --- TỔNG HỢP & ĐÁNH GIÁ ---
    draft_answer: str
    citations: Annotated[List[Dict[str, Any]], merge_list]
    evaluation: Annotated[Dict[str, Any], merge_dict]

    # --- KIỂM SOÁT VÒNG LẶP & ĐỐI THOẠI NGƯỜI DÙNG---
    loop_step: int
    human_feedback: str                
