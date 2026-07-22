# Chức năng: QueryReformAgent chuẩn hóa câu hỏi của người dùng và trích xuất thực thể pháp lý.

import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from agents.base import BaseAgent
from state import AgentState
from config import (
    get_ai_model, 
    DEFAULT_PROVIDER, 
    MODEL_SUB_AGENT_GPT, 
    MODEL_SUB_AGENT_GEMINI
)

class MissingInfoItem(BaseModel):
    field: str = Field(description="Loại thông tin còn thiếu (ví dụ: 'ngành nghề', 'loại hình doanh nghiệp', 'kỳ tính thuế').")
    suggestion: str = Field(description="Câu hỏi gợi ý để người dùng bổ sung thông tin còn thiếu.")

class QueryReformOutput(BaseModel):
    refined_query: str = Field(description="Câu hỏi đã được chuẩn hóa chính tả và mở rộng từ khóa pháp lý.")
    detected_entities: List[str] = Field(description="Danh sách các thực thể pháp lý phát hiện được (ví dụ: số hiệu thông tư, loại thuế, luật...).")
    original_query: str = Field(description="Câu hỏi gốc của người dùng.")
    confidence: float = Field(description="Điểm đánh giá độ rõ ràng của câu hỏi (0.0 = hoàn toàn mơ hồ, 1.0 = rõ ràng đầy đủ). Dưới 0.75 nghĩa là cần hỏi lại người dùng.")
    missing_info: List[MissingInfoItem] = Field(default_factory=list, description="Danh sách thông tin còn thiếu kèm câu hỏi gợi ý. Rỗng nếu câu hỏi đã đủ rõ.")

class QueryReformAgent(BaseAgent):
    """Tác nhân chuẩn hóa câu hỏi và trích xuất thực thể (Tầng 2)."""
    
    def __init__(self, provider: str = DEFAULT_PROVIDER):
        goal_context = (
            "Bạn là một chuyên gia phân tích ngôn ngữ pháp lý Việt Nam. Nhiệm vụ của bạn là nhận câu hỏi thô từ người dùng, "
            "làm sạch chính tả, chuẩn hóa các thuật ngữ viết tắt và mở rộng các từ khóa pháp luật liên quan "
            "(ví dụ: 'thuế tndn' -> 'thuế thu nhập doanh nghiệp', 'nđ cp' -> 'nghị định chính phủ'). "
            "Đồng thời trích xuất danh sách thực thể pháp lý có trong câu hỏi. "
            "Cuối cùng, đánh giá mức độ rõ ràng của câu hỏi bằng confidence (0.0-1.0):\n"
            "- Đặt confidence = 1.0 cho các câu chào hỏi, các câu hỏi đã có sản phẩm/đối tượng/vị trí cụ thể (như 'thuế GTGT đèn LED', 'bảng giá đất Phường 2 Quận 7 TP.HCM').\n"
            "- Đặt confidence < 0.70 và bổ sung missing_info khi câu hỏi rơi vào các nhóm mơ hồ/thiếu điều kiện sau:\n"
            "  1. CỤT NGỦN / MƠ HỒ: Câu hỏi quá ngắn không đủ nghĩa (ví dụ: 'Tiền bao nhiêu?', 'Thuế thế nào?').\n"
            "  2. DANH MỤC HÀNG HÓA/SẢN PHẨM QUÁ RỘNG: (ví dụ: 'thuế cá', 'thuế gỗ', 'thuế xe', 'thuế nông sản'...) "
            "hỏi làm rõ trạng thái sản phẩm (tươi sống hay chế biến đóng hộp), dòng xe cũ/mới hay mục đích kinh doanh/xuất khẩu để chốt mức thuế chính xác.\n"
            "  3. THIẾU VỊ TRÍ ĐỊA BÀN ĐẤT ĐAI: (ví dụ: 'giá đất thế nào?', 'bảng giá đất TP.HCM...', 'lệ phí sổ đỏ...'): "
            "hỏi làm rõ địa bàn hành chính (Quận/Huyện, Phường/Xã hoặc Tuyến đường) để báo giá đất và quy định chính xác.\n"
            "  4. THIẾU TÌNH TRẠNG GIẤY TỜ / PHÁP LÝ ĐẤT: (ví dụ: 'thủ tục cấp sổ đỏ', 'bồi thường thu hồi đất', 'tách thửa đất'...): "
            "hỏi làm rõ tình trạng giấy tờ hiện tại (đã có Sổ đỏ/Sổ hồng hay chưa, đất có tranh chấp không...).\n"
            "  5. THIẾU MỐC THỜI GIAN TRANH CHẤP / GIAO DỊCH QUÁ KHỨ: (ví dụ: 'thừa kế đất đai từ xưa', 'miễn giảm thuế năm cũ'...): "
            "hỏi làm rõ năm/thời điểm phát sinh giao dịch (năm 2013, 2017 hay 2024) để tra cứu đúng luật có hiệu lực tại thời điểm đó.\n"
            "  6. THIẾU LOẠI HÌNH THUẾ CỤ THỂ: (ví dụ: 'nộp thuế doanh nghiệp', 'kê khai thuế'...): "
            "hỏi làm rõ loại thuế muốn tư vấn (Thuế GTGT, Thuế TNDN, Thuế TNCN, Lệ phí môn bài...) và kỳ tính thuế.\n"
            "  7. THIẾU HÀNG THỪA KẾ / DI CHÚC: (ví dụ: 'chia thừa kế đất đai', 'tài sản vợ chồng'...): "
            "hỏi làm rõ có di chúc hay không, quan hệ nhân thân (con ruột, con nuôi...) để xác định chia theo pháp luật hay di chúc.\n"
            "  8. THIẾU ĐIỀU KIỆN MIỄN GIẢM / ƯU ĐÃI THUẾ: (ví dụ: 'miễn thuế khi bán nhà', 'ưu đãi thuế DN'...): "
            "hỏi làm rõ điều kiện đặc thù (bán căn nhà duy nhất, địa bàn ưu đãi đầu tư, doanh nghiệp nhỏ và vừa...)."
        )
        task_boundary = "Chỉ chuẩn hóa câu hỏi, trích xuất thực thể và đánh giá độ rõ ràng. Tuyệt đối không tự trả lời câu hỏi."
        skills_tools: List[str] = []
        
        super().__init__(
            goal_context=goal_context,
            task_boundary=task_boundary,
            skills_tools=skills_tools,
            output_schema=QueryReformOutput
        )
        self.provider = provider

    def run(self, state: AgentState) -> Dict[str, Any]:
        """Thực thi suy luận chuẩn hóa câu hỏi."""
        raw_query = state.get("raw_query", "")
        history_messages = state.get("messages", [])
        
        # 1. Khởi tạo LLM adapter tương ứng với nhà cung cấp
        model_name = MODEL_SUB_AGENT_GPT if self.provider == "openai" else MODEL_SUB_AGENT_GEMINI
        model = get_ai_model(model_name, provider=self.provider)
        
        # 2. Xây dựng prompt kèm Hồ sơ Bộ nhớ Dài hạn & Lịch sử Hội thoại gần nhất
        user_profile = state.get("user_profile", {})
        profile_text = f"Hồ sơ khách hàng đã lưu từ trước: {user_profile}\n" if user_profile else ""
        
        history_text = ""
        if history_messages:
            recent_msgs = history_messages[-12:]  # Lấy 12 tin nhắn gần nhất (6 lượt trao đổi)
            formatted_history = []
            for msg in recent_msgs:
                role = "Người dùng" if getattr(msg, "type", "") == "human" or (isinstance(msg, dict) and msg.get("role") == "user") else "Trợ lý"
                content = getattr(msg, "content", "") or (msg.get("content") if isinstance(msg, dict) else str(msg))
                formatted_history.append(f"{role}: {content}")
            history_text = "Lịch sử hội thoại gần đây:\n" + "\n".join(formatted_history) + "\n"
        
        prompt_text = (
            f"{profile_text}"
            f"{history_text}"
            f"Câu hỏi thô mới của người dùng: '{raw_query}'\n"
            f"Lưu ý: Sử dụng hồ sơ khách hàng đã lưu và lịch sử hội thoại trên để làm rõ đối tượng/ngữ cảnh "
            f"nếu câu hỏi mới có tính chất nối tiếp hoặc hỏi ngắn."
        )
        
        messages = [
            {"role": "system", "content": self.goal_context},
            {"role": "user", "content": prompt_text}
        ]
        
        try:
            # 3. Gọi LLM sinh structured output
            raw_output = model.generate(messages, response_schema=self.output_schema)
            # 4. Parse kết quả theo schema
            parsed = self.output_schema.model_validate_json(raw_output)
            return parsed.model_dump()
        except Exception as e:
            # Fallback an toàn nếu LLM lỗi hoặc parse thất bại
            return {
                "refined_query": raw_query,
                "detected_entities": [],
                "original_query": raw_query,
                "confidence": 0.5,
                "missing_info": []
            }
