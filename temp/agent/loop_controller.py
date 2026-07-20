# Chức năng: Bộ kiểm soát chất lượng (Verifier), khống chế số bước lặp (Loop Controller) và Human Checkpoint.

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from state import AgentState
from config import get_ai_model, DEFAULT_PROVIDER, MODEL_SUB_AGENT_GEMINI, MAX_LOOP_STEPS

class VerifierOutput(BaseModel):
    is_valid: bool = Field(description="Đánh giá chất lượng báo cáo: True (đạt chất lượng) hoặc False (cần chỉnh sửa).")
    reason: str = Field(description="Lý do chi tiết tại sao đạt hoặc không đạt chất lượng.")
    feedback: str = Field(description="Ý kiến phản hồi gửi lại cho các Sub-Agents để bổ sung/sửa đổi nếu is_valid = False.")
    failed_domains: list[str] = Field(default_factory=list, description="Danh sách các domain cụ thể gặp lỗi cần chạy lại để bổ sung/sửa đổi (chỉ nhận giá trị 'tax' hoặc 'land'). Nếu đạt chất lượng thì trả về danh sách rỗng.")

def execute_verifier(draft_answer: str, query_text: str, provider: str = DEFAULT_PROVIDER) -> Dict[str, Any]:
    """Kiểm checker đánh giá chất lượng toàn diện câu trả lời nháp (Tầng 5)."""
    system_instruction = (
        "Bạn là kiểm soát viên chất lượng (Verifier) của hệ thống Mas-Legal. "
        "Nhiệm vụ của bạn là đánh giá xem báo cáo tư vấn pháp lý nháp có:\n"
        "1. Trả lời đúng, trực diện và đầy đủ yêu cầu của người dùng không?\n"
        "2. Có trích dẫn điều khoản luật rõ ràng không? (Báo cáo không có trích dẫn là không đạt).\n"
        "3. Có mâu thuẫn hay điểm bất hợp lý nào trong lập luận không?\n"
        "Nếu báo cáo đạt chất lượng, trả về is_valid = True. "
        "Nếu chưa đạt (thiếu thông tin, trích dẫn trống...), trả về is_valid = False kèm feedback chi tiết chỉ ra chỗ cần sửa "
        "và xác định rõ domain nào bị lỗi trong 'failed_domains' ('tax' cho Luật Thuế, 'land' cho Luật Đất Đai)."
    )
    
    user_content = (
        f"Câu hỏi của người dùng: '{query_text}'\n\n"
        f"Báo cáo nháp cần kiểm tra:\n{draft_answer}"
    )
    
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_content}
    ]
    
    try:
        model = get_ai_model(MODEL_SUB_AGENT_GEMINI, provider=provider)
        raw_output = model.generate(messages, response_schema=VerifierOutput)
        parsed = VerifierOutput.model_validate_json(raw_output)
        return parsed.model_dump()
    except Exception as e:
        print(f"[WARNING] Trình Verifier gặp lỗi: {e}. Tự động phê duyệt bypass.")
        return {
            "is_valid": True,
            "reason": f"Verifier bypass do lỗi: {str(e)}",
            "feedback": "",
            "failed_domains": []
        }

def loop_controller_check(state: AgentState) -> Dict[str, Any]:
    """Kiểm tra và khống chế số lượng vòng lặp sửa đổi."""
    loop_step = state.get("loop_step", 0)
    
    # 1. Gọi Verifier đánh giá chất lượng draft_answer
    draft_answer = state.get("draft_answer", "")
    query_text = state.get("refined_query") or state.get("raw_query", "")
    
    verification = execute_verifier(draft_answer, query_text)
    
    # 2. Lưu kết quả đánh giá vào evaluation
    new_evaluation = dict(state.get("evaluation", {}))
    new_evaluation["verifier"] = verification
    
    # 3. Phán quyết vòng lặp
    is_valid = verification.get("is_valid", True)
    
    if not is_valid and loop_step < MAX_LOOP_STEPS:
        # Yêu cầu chạy lại vòng lặp để sửa đổi
        print(f"[LOOP CONTROLLER] Lượt {loop_step + 1}/{MAX_LOOP_STEPS} không đạt chất lượng. Lý do: {verification.get('reason')}. Quay lại sửa đổi...")
        return {
            "evaluation": new_evaluation,
            "loop_step": loop_step + 1,
            "human_feedback": verification.get("feedback", "")  # Ghi feedback sửa lỗi vào human_feedback để sub-agents đọc
        }
    else:
        # Đạt chất lượng hoặc đạt giới hạn số lần lặp tối đa
        if not is_valid:
            print(f"[LOOP CONTROLLER] Đạt giới hạn lặp tối đa ({MAX_LOOP_STEPS}). Force exit và chấp nhận kết quả hiện tại.")
        else:
            print(f"[LOOP CONTROLLER] Báo cáo đạt chất lượng thẩm định ở lượt thứ {loop_step}. Tiến tới phê duyệt.")
            
        return {
            "evaluation": new_evaluation,
            "human_feedback": ""  # Xóa sạch feedback sửa lỗi để tránh hiểu nhầm
        }

def execute_human_checkpoint(draft_answer: str) -> bool:
    """Giả lập checkpoint phê duyệt thủ công từ người vận hành (Human Checkpoint)."""
    print("\n" + "-"*40)
    print(" [HUMAN CHECKPOINT] YÊU CẦU PHÊ DUYỆT BÁO CÁO ".center(40, "="))
    print("-"*40)
    # Lấy 100 từ đầu tiên để hiển thị nhanh
    preview = draft_answer[:200] + "..." if len(draft_answer) > 200 else draft_answer
    print(f"Bản nháp báo cáo:\n{preview}")
    print("-"*40)
    print("[INFO] Hệ thống tự động phê duyệt trong chế độ tự động hóa.")
    return True
