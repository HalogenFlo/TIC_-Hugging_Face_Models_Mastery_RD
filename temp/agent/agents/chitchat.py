# Chức năng: ChitchatAgent xử lý các phản hồi xã giao hoặc câu hỏi ngoài phạm vi nghiệp vụ pháp luật.

import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from agents.base import BaseAgent
from state import AgentState
from config import (
    get_ai_model, 
    DEFAULT_PROVIDER, 
    MODEL_SUB_AGENT_GPT, 
    MODEL_SUB_AGENT_GEMINI
)

class ChitchatOutput(BaseModel):
    response: str = Field(description="Phản hồi thân thiện chào hỏi hoặc chitchat xã giao.")

class ChitchatAgent(BaseAgent):
    """Tác nhân xử lý chitchat/Out-of-Scope (Tầng 2)."""
    
    def __init__(self, provider: str = DEFAULT_PROVIDER):
        goal_context = (
            "Bạn là một trợ lý ảo thông minh chuyên về tư vấn pháp luật Việt Nam bao gồm nhiều lĩnh vực. "
            "Người dùng hiện tại đang chào hỏi hoặc chitchat/nói chuyện ngoài lề không liên quan đến pháp luật. "
            "Hãy phản hồi một cách ngắn gọn, thân thiện, lịch sự và tinh tế hướng người dùng đặt các câu hỏi "
            "liên quan đến lĩnh vực tư vấn pháp lý Việt Nam."
        )
        task_boundary = "Chỉ trả lời chitchat, chào hỏi, trả lời câu hỏi hợp lý. Tuyệt đối không tư vấn pháp luật chuyên sâu."
        skills_tools: List[str] = []
        
        super().__init__(
            goal_context=goal_context,
            task_boundary=task_boundary,
            skills_tools=skills_tools,
            output_schema=ChitchatOutput
        )
        self.provider = provider

    def run(self, state: AgentState) -> Dict[str, Any]:
        """Thực thi suy luận chào hỏi/chitchat."""
        query = state.get("raw_query", "")
        
        # 1. Khởi tạo LLM adapter tương ứng với nhà cung cấp
        model_name = MODEL_SUB_AGENT_GPT if self.provider == "openai" else MODEL_SUB_AGENT_GEMINI
        model = get_ai_model(model_name, provider=self.provider)
        
        # 2. Xây dựng prompt
        messages = [
            {"role": "system", "content": self.goal_context},
            {"role": "user", "content": query}
        ]
        
        try:
            # 3. Gọi LLM sinh structured output
            raw_output = model.generate(messages, response_schema=self.output_schema)
            # 4. Parse kết quả theo schema
            parsed = self.output_schema.model_validate_json(raw_output)
            return parsed.model_dump()
        except Exception as e:
            # Fallback an toàn nếu LLM lỗi hoặc parse thất bại
            fallback_text = (
                "Xin chào! Tôi là trợ lý ảo tư vấn pháp luật Việt Nam. "
                "Hiện tôi hỗ trợ giải đáp các thắc mắc về các lĩnh vực pháp luật như: Luật Thuế, Luật Đất đai, Luật Lao động, Luật Doanh nghiệp.... "
                "Bạn cần tôi hỗ trợ thông tin gì về các lĩnh vực này không?"
            )
            return {"response": fallback_text}
