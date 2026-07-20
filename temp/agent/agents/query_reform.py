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
            "Cuối cùng, đánh giá mức độ rõ ràng của câu hỏi bằng confidence (0.0-1.0): "
            "nếu câu hỏi mơ hồ, thiếu ngữ cảnh hoặc thiếu thông tin quan trọng (như ngành nghề, kỳ tính thuế, loại hình DN...) thì confidence < 0.75 "
            "và liệt kê các thông tin còn thiếu kèm câu hỏi gợi ý trong missing_info."
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
        
        # 1. Khởi tạo LLM adapter tương ứng với nhà cung cấp
        model_name = MODEL_SUB_AGENT_GPT if self.provider == "openai" else MODEL_SUB_AGENT_GEMINI
        model = get_ai_model(model_name, provider=self.provider)
        
        # 2. Xây dựng prompt
        messages = [
            {"role": "system", "content": self.goal_context},
            {"role": "user", "content": f"Câu hỏi thô cần xử lý: '{raw_query}'"}
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
