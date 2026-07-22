# Chức năng: OrchestratorAgent phân loại ý định người dùng và định tuyến các domain luật.
# Lý do tạo: Thực hiện vai trò điều phối trung tâm của hệ thống Multi-Agent (Tầng 3).
# Link trích dẫn: https://github.com/HalogenFlo/TIC_-Hugging_Face_Models_Mastery_RD

import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from state import AgentState
from config import (
    get_ai_model, 
    DEFAULT_PROVIDER, 
    MODEL_ORCHESTRATOR_GPT, 
    MODEL_ORCHESTRATOR_GEMINI
)

class OrchestratorOutput(BaseModel):
    effort_level: str = Field(description="Đánh giá phân loại ý định ban đầu: 'bypass' (nếu là chitchat/xã giao/ngoài phạm vi) hoặc 'legal' (nếu hỏi về luật thuế hoặc luật đất đai).")
    detected_domains: List[str] = Field(default_factory=list, description="Danh sách các lĩnh vực luật liên quan phát hiện được, ví dụ: ['tax'], ['land'], hoặc ['tax', 'land']. Trống nếu là bypass.")

class OrchestratorAgent:
    """Tác nhân điều phối (Tầng 3) phân tích intent và định tuyến domain."""
    
    def __init__(self, provider: str = DEFAULT_PROVIDER):
        self.goal_context = (
            "Bạn là trợ lý ảo điều phối trung tâm (Orchestrator) cho hệ thống tư vấn pháp luật Việt Nam. "
            "Nhiệm vụ của bạn là phân tích câu hỏi người dùng và phân loại ý định định tuyến chính xác:\n"
            "1. Nếu là chào hỏi, chitchat xã giao: Đặt effort_level = 'bypass' và detected_domains = [].\n"
            "2. Nếu là câu hỏi pháp lý: Đặt effort_level = 'legal' và liệt kê TẤT CẢ CÁC LĨNH VỰC LUẬT BỊ ẢNH HƯỞNG trong detected_domains "
            "(như 'tax' cho Thuế, 'land' cho Đất Đai, và các lĩnh vực mở rộng khác như 'enterprise', 'civil', 'labor'...).\n"
            "LƯU Ý MỞ RỘNG ĐA MIỀN: Một câu hỏi phức tạp có thể có sự giao thoa liên quan tới 2, 3 hoặc nhiều hơn N lĩnh vực pháp lý cùng lúc. "
            "Hãy tự động phát hiện và kích hoạt ĐẦY ĐỦ TẤT CẢ các lĩnh vực liên quan trong detected_domains để hệ thống phối hợp tư vấn toàn diện."
        )
        self.task_boundary = (
            "Chỉ làm nhiệm vụ phân loại ý định và định tuyến lĩnh vực luật. "
            "Tuyệt đối không tự mình trả lời câu hỏi nghiệp vụ pháp lý hoặc giải quyết mâu thuẫn."
        )
        self.output_schema = OrchestratorOutput
        self.provider = provider

    def run(self, state: AgentState) -> Dict[str, Any]:
        """Thực thi suy luận phân loại và định tuyến ý định."""
        query_text = state.get("refined_query") or state.get("raw_query", "")
        
        # Chọn model nhỏ, nhanh cho vai trò Orchestrator
        model_name = MODEL_ORCHESTRATOR_GPT if self.provider == "openai" else MODEL_ORCHESTRATOR_GEMINI
        model = get_ai_model(model_name, provider=self.provider)
        
        system_instruction = (
            f"{self.goal_context}\n"
            f"Ràng buộc: {self.task_boundary}"
        )
        
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Câu hỏi của người dùng: '{query_text}'"}
        ]
        
        try:
            raw_output = model.generate(messages, response_schema=self.output_schema)
            parsed = self.output_schema.model_validate_json(raw_output)
            return parsed.model_dump()
        except Exception as e:
            print(f"[ERROR] LLM generation failed in OrchestratorAgent: {e}")
            # Fallback an toàn: mặc định chạy legal để không bỏ sót câu hỏi của người dùng
            return {
                "effort_level": "legal",
                "detected_domains": ["tax"]  # fallback sang tax làm mặc định
            }
