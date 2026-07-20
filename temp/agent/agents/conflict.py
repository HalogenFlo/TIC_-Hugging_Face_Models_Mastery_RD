# Chức năng: ConflictResolutionAgent phát hiện và giải quyết mâu thuẫn/xung đột giữa các văn bản pháp luật.

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

class LegalConflict(BaseModel):
    conflict_type: str = Field(description="Loại mâu thuẫn: 'thời gian' | 'cấp bậc' | 'nội dung' | 'chuyên ngành'")
    description: str = Field(description="Mô tả chi tiết về mâu thuẫn pháp lý phát hiện được.")
    resolving_rule: str = Field(description="Quy tắc pháp lý áp dụng để giải quyết (ví dụ: Điều 156 Luật Ban hành VBQPPL hoặc nguyên tắc tính thuế).")
    resolved_norm_code: str = Field(description="Số hiệu văn bản pháp lý được quyết định áp dụng sau khi giải quyết mâu thuẫn.")

class ConflictOutput(BaseModel):
    has_conflict: bool = Field(description="Đánh giá xem có mâu thuẫn nào giữa các tài liệu pháp lý đã tìm thấy hay không.")
    conflicts: List[LegalConflict] = Field(default_factory=list, description="Danh sách các mâu thuẫn cụ thể.")

class ConflictResolutionAgent(BaseAgent):
    """Tác nhân chuyên biệt phát hiện và giải quyết mâu thuẫn pháp luật (Tầng 2)."""

    def __init__(self, provider: str = DEFAULT_PROVIDER):
        goal_context = (
            "Bạn là chuyên gia giải quyết mâu thuẫn pháp lý Việt Nam. Nhiệm vụ của bạn là đọc các câu trả lời nháp "
            "và ngữ cảnh pháp luật thu thập được từ các tác nhân chuyên môn khác để phát hiện xem có sự mâu thuẫn "
            "nào giữa các văn bản pháp luật hay không, chỉ ra lý do mâu thuẫn và đưa ra quyết định áp dụng văn bản nào "
            "dựa trên các nguyên tắc chuẩn mực của pháp luật Việt Nam (đặc biệt là Điều 156 Luật Ban hành văn bản quy phạm pháp luật).\n"
            "Các nguyên tắc giải quyết mâu thuẫn chủ đạo:\n"
            "1. Nguyên tắc cấp bậc hiệu lực: Văn bản do cơ quan cấp trên ban hành có hiệu lực cao hơn (ví dụ: Luật > Nghị định > Thông tư).\n"
            "2. Nguyên tắc thời gian: Các văn bản do cùng một cơ quan ban hành quy định về cùng một vấn đề thì áp dụng văn bản ban hành sau (Luật mới thay thế luật cũ).\n"
            "3. Nguyên tắc chuyên ngành: Ưu tiên áp dụng quy định của luật chuyên ngành so với luật chung (Luật riêng > Luật chung).\n"
            "4. Nguyên tắc xác định giá tính thuế: Nếu có sự chênh lệch giữa giá trị giao dịch thực tế trên hợp đồng và bảng giá nhà nước quy định, "
            "áp dụng mức giá cao hơn để tính thuế."
        )
        task_boundary = (
            "Chỉ thực hiện phát hiện mâu thuẫn và chỉ ra hướng giải quyết. "
            "Không tự soạn thảo báo cáo tư vấn cuối cùng hay trả lời ngoài phạm vi mâu thuẫn."
        )
        skills_tools = ["search_retrieval", "reporting"]
        
        super().__init__(
            goal_context=goal_context,
            task_boundary=task_boundary,
            skills_tools=skills_tools,
            output_schema=ConflictOutput
        )
        self.provider = provider

    def run(self, state: AgentState) -> Dict[str, Any]:
        """Thực thi suy luận xử lý mâu thuẫn."""
        domain_outputs = state.get("domain_outputs", {})
        
        # 1. Tập hợp tất cả thông tin ngữ cảnh từ các domain agents
        contexts = []
        for domain, output in domain_outputs.items():
            draft = output.get("draft_answer", "")
            citations = output.get("citations", [])
            contexts.append(
                f"=== DOMAIN: {domain.upper()} ===\n"
                f"Dự thảo câu trả lời: {draft}\n"
                f"Danh sách trích dẫn: {json.dumps(citations, ensure_ascii=False)}\n"
            )
            
        context_str = "\n\n".join(contexts) if contexts else "Không có dữ liệu đầu vào từ các tác nhân chuyên môn."
        
        # 2. Xây dựng prompt sinh phản hồi
        system_instruction = (
            f"{self.goal_context}\n"
            f"Ràng buộc nhiệm vụ: {self.task_boundary}"
        )
        
        user_content = (
            f"Ngữ cảnh câu hỏi của người dùng: '{state.get('refined_query') or state.get('raw_query', '')}'\n\n"
            f"Dữ liệu cần kiểm tra mâu thuẫn:\n{context_str}\n"
        )
        
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content}
        ]
        
        model_name = MODEL_SUB_AGENT_GPT if self.provider == "openai" else MODEL_SUB_AGENT_GEMINI
        model = get_ai_model(model_name, provider=self.provider)
        
        try:
            raw_output = model.generate(messages, response_schema=self.output_schema)
            parsed = self.output_schema.model_validate_json(raw_output)
            return parsed.model_dump()
        except Exception as e:
            print(f"[ERROR] LLM generation failed in ConflictResolutionAgent: {e}")
            return {
                "has_conflict": False,
                "conflicts": []
            }
