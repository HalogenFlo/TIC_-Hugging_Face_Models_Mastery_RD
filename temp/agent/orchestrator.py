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
            "Bạn là trợ lý ảo điều phối trung tâm (Coordinator) cho hệ thống tư vấn pháp luật Việt Nam. "
            "Nhiệm vụ của bạn là đọc câu hỏi của người dùng và xác định xem đó là câu hỏi chào hỏi xã giao, "
            "nói chuyện ngoài lề (chitchat) hay là một câu hỏi nghiệp vụ pháp lý chuyên sâu về Luật Thuế hoặc Luật Đất đai Việt Nam.\n"
            "1. Nếu câu hỏi là chào hỏi, chitchat xã giao hoặc ngoài phạm vi tư vấn pháp lý: "
            "hãy đặt effort_level = 'bypass' và detected_domains = [].\n"
            "2. Nếu câu hỏi là về pháp lý (luật thuế, đất đai, bồi thường đất, chuyển nhượng nhà đất, lệ phí trước bạ...): "
            "hãy đặt effort_level = 'legal' và xác định các lĩnh vực luật liên quan trong detected_domains. "
            "Các lĩnh vực hợp lệ là: 'tax' (thuế) và 'land' (đất đai)."
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
