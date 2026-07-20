# Chức năng: Định nghĩa đồ thị StateGraph LangGraph kết nối các tác nhân và cấu hình cạnh rẽ nhánh.

from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from state import AgentState
from config import CLARIFICATION_THRESHOLD, MAX_CLARIFICATION_TURNS

from agents.query_reform import QueryReformAgent
from orchestrator import OrchestratorAgent
from agents.chitchat import ChitchatAgent
from agents.law_tax import TaxLawAgent
from agents.law_land import LandLawAgent
from agents.conflict import ConflictResolutionAgent
from agents.synthesis import SynthesisAgent

# --- ĐỊNH NGHĨA WRAPPER NODES ---

def query_reform_node(state: AgentState) -> Dict[str, Any]:
    """Node chuẩn hóa và mở rộng câu hỏi."""
    agent = QueryReformAgent()
    output = agent.run(state)
    return {
        "refined_query": output.get("refined_query", state.get("raw_query")),
        "evaluation": {
            "confidence": output.get("confidence", 1.0),
            "missing_info": output.get("missing_info", [])
        }
    }

def orchestrator_initial_node(state: AgentState) -> Dict[str, Any]:
    """Node phân loại ý định ban đầu."""
    agent = OrchestratorAgent()
    output = agent.run(state)
    return {
        "effort_level": output.get("effort_level", "legal"),
        "detected_domains": output.get("detected_domains", [])
    }

def orchestrator_check_node(state: AgentState) -> Dict[str, Any]:
    """Node kiểm tra độ tự tin (Clarification Gate) và Effort Scaling."""
    evaluation = state.get("evaluation", {})
    confidence = evaluation.get("confidence", 1.0)
    missing_info = evaluation.get("missing_info", [])
    detected_domains = state.get("detected_domains", [])
    clarification_count = state.get("clarification_count", 0)
    
    # 1. Clarification Gate
    if confidence < CLARIFICATION_THRESHOLD and len(missing_info) > 0:
        if clarification_count < MAX_CLARIFICATION_TURNS:
            prompt = missing_info[0].get("suggestion", "Vui lòng làm rõ câu hỏi của bạn.")
            return {
                "effort_level": "clarification",
                "human_feedback": prompt,
                "clarification_count": clarification_count + 1
            }
        else:
            print(f"[WARNING] Vượt quá giới hạn làm rõ ({MAX_CLARIFICATION_TURNS}). Bắt buộc thực thi.")
            effort_level = "complex"
    else:
        # 2. Rule-based Effort Scaling
        refined_query = state.get("refined_query") or state.get("raw_query", "")
        query_lower = refined_query.lower()
        has_doc_references = any(word in query_lower for word in ["luật", "nghị định", "thông tư", "tt", "nđ", "qh", "năm", "201", "202"])
        
        if len(detected_domains) >= 2 or has_doc_references:
            effort_level = "complex"
        else:
            effort_level = "simple"
            
    return {
        "effort_level": effort_level
    }

def chitchat_node(state: AgentState) -> Dict[str, Any]:
    """Node xử lý chitchat/xã giao."""
    agent = ChitchatAgent()
    output = agent.run(state)
    return {
        "draft_answer": output.get("response", "")
    }

def tax_node(state: AgentState) -> Dict[str, Any]:
    """Node tư vấn luật Thuế."""
    agent = TaxLawAgent()
    output = agent.run(state)
    return {
        "domain_outputs": {
            "tax": output
        }
    }

def land_node(state: AgentState) -> Dict[str, Any]:
    """Node tư vấn luật Đất đai."""
    agent = LandLawAgent()
    output = agent.run(state)
    return {
        "domain_outputs": {
            "land": output
        }
    }

def conflict_node(state: AgentState) -> Dict[str, Any]:
    """Node phát hiện và giải quyết mâu thuẫn luật."""
    agent = ConflictResolutionAgent()
    output = agent.run(state)
    return {
        "conflicts": output.get("conflicts", [])
    }

def synthesis_node(state: AgentState) -> Dict[str, Any]:
    """Node gộp kết quả và xuất báo cáo cuối cùng."""
    agent = SynthesisAgent()
    output = agent.run(state)
    return {
        "draft_answer": output.get("final_answer", ""),
        "citations": output.get("all_citations", [])
    }

def loop_controller_node(state: AgentState) -> Dict[str, Any]:
    """Node kiểm tra vòng lặp thẩm định chất lượng."""
    from loop_controller import loop_controller_check
    return loop_controller_check(state)

def clear_raw_outputs_node(state: AgentState) -> Dict[str, Any]:
    """Node dọn dẹp các kết quả thô của databases khỏi state để chống phình context."""
    from loop_controller import execute_human_checkpoint
    draft_answer = state.get("draft_answer", "")
    # Thực hiện Human Checkpoint giả lập trước khi trả về kết quả
    execute_human_checkpoint(draft_answer)
    
    cleaned_domains = {}
    for domain, output in state.get("domain_outputs", {}).items():
        cleaned_domains[domain] = {
            "draft_answer": "[Cleared to save context]",
            "citations": []
        }
    return {
        "domain_outputs": cleaned_domains
    }

# --- CÁC HÀM ĐỊNH TUYẾN ĐIỀU KIỆN ---

def route_initial(state: AgentState) -> str:
    """Định tuyến ban đầu dựa theo ý định phân loại."""
    effort = state.get("effort_level", "legal")
    if effort == "bypass":
        return "chitchat_node"
    return "query_reform_node"

def route_check(state: AgentState) -> List[str]:
    """Định tuyến sau khi check câu hỏi (hỏi lại hoặc gọi domains song song)."""
    effort = state.get("effort_level", "simple")
    if effort == "clarification":
        return ["__end__"] # dừng đồ thị
        
    domains = state.get("detected_domains", [])
    destinations = []
    if "tax" in domains:
        destinations.append("tax_node")
    if "land" in domains:
        destinations.append("land_node")
        
    # Fallback nếu orchestrator không nhận diện được domain nào cụ thể
    if not destinations:
        destinations.append("tax_node")
        
    return destinations

def route_loop(state: AgentState) -> List[str]:
    """Định tuyến sau thẩm định: quay lại sửa đổi hoặc kết thúc."""
    from config import MAX_LOOP_STEPS
    evaluation = state.get("evaluation", {})
    verifier = evaluation.get("verifier", {})
    is_valid = verifier.get("is_valid", True)
    loop_step = state.get("loop_step", 0)
    
    if not is_valid and loop_step < MAX_LOOP_STEPS:
        # Lấy các domain bị lỗi từ kết quả thẩm định
        failed_domains = verifier.get("failed_domains", [])
        
        # Nếu không trích xuất được failed_domains, fallback dùng các domain phát hiện ban đầu
        if not failed_domains:
            failed_domains = state.get("detected_domains", [])
            
        destinations = []
        if "tax" in failed_domains:
            destinations.append("tax_node")
        if "land" in failed_domains:
            destinations.append("land_node")
            
        if not destinations:
            # Fallback an toàn
            destinations.append("tax_node")
            
        print(f"[ROUTE LOOP] Quay lại sửa đổi cho các domain: {destinations}")
        return destinations
        
    # Đạt chất lượng hoặc đạt giới hạn số lần lặp -> Dọn dẹp và kết thúc
    return ["clear_raw_outputs_node"]

# --- KHỞI TẠO VÀ LIÊN KẾT ĐỒ THỊ ---

def build_graph() -> StateGraph:
    """Xây dựng StateGraph của hệ thống Multi-Agent."""
    workflow = StateGraph(AgentState)
    
    # 1. Khai báo các Node
    workflow.add_node("orchestrator_initial_node", orchestrator_initial_node)
    workflow.add_node("query_reform_node", query_reform_node)
    workflow.add_node("orchestrator_check_node", orchestrator_check_node)
    workflow.add_node("chitchat_node", chitchat_node)
    workflow.add_node("tax_node", tax_node)
    workflow.add_node("land_node", land_node)
    workflow.add_node("conflict_node", conflict_node)
    workflow.add_node("synthesis_node", synthesis_node)
    workflow.add_node("loop_controller_node", loop_controller_node)
    workflow.add_node("clear_raw_outputs_node", clear_raw_outputs_node)
    
    # 2. Thiết lập Entry Point
    workflow.set_entry_point("orchestrator_initial_node")
    
    # 3. Liên kết Cạnh Điều kiện ban đầu
    workflow.add_conditional_edges(
        "orchestrator_initial_node",
        route_initial,
        {
            "chitchat_node": "chitchat_node",
            "query_reform_node": "query_reform_node"
        }
    )
    
    # 4. Liên kết Cạnh từ Reform sang Check
    workflow.add_edge("query_reform_node", "orchestrator_check_node")
    
    # 5. Liên kết Cạnh Điều kiện từ Check sang Domains
    workflow.add_conditional_edges(
        "orchestrator_check_node",
        route_check,
        {
            "__end__": END,
            "tax_node": "tax_node",
            "land_node": "land_node"
        }
    )
    
    # 6. Liên kết Domains hội tụ về Conflict Node (Fan-in)
    workflow.add_edge("tax_node", "conflict_node")
    workflow.add_edge("land_node", "conflict_node")
    
    # 7. Liên kết từ Conflict sang Synthesis
    workflow.add_edge("conflict_node", "synthesis_node")
    
    # 8. Liên kết từ Synthesis sang Loop Controller Node để thẩm định chất lượng
    workflow.add_edge("synthesis_node", "loop_controller_node")
    
    # 9. Liên kết Cạnh Điều kiện sau Loop Controller
    workflow.add_conditional_edges(
        "loop_controller_node",
        route_loop,
        {
            "tax_node": "tax_node",
            "land_node": "land_node",
            "clear_raw_outputs_node": "clear_raw_outputs_node"
        }
    )
    
    # 10. Từ clear_raw_outputs_node và chitchat_node đi đến kết thúc
    workflow.add_edge("clear_raw_outputs_node", END)
    workflow.add_edge("chitchat_node", END)
    
    return workflow.compile()
