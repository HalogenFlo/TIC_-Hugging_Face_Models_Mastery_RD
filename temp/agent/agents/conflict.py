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
            "và ngữ cảnh pháp luật từ các tác nhân chuyên môn để phát hiện xem có sự mâu thuẫn/xung đột nào giữa các văn bản pháp luật hay không, "
            "và đưa ra quyết định ưu tiên áp dụng văn bản nào dựa trên Điều 156 Luật Ban hành văn bản quy phạm pháp luật 2015:\n"
            "1. Cấp bậc hiệu lực: Văn bản do cơ quan cấp trên ban hành ưu tiên áp dụng (Luật > Nghị định > Thông tư).\n"
            "2. Mốc thời gian ban hành: Nếu cùng cấp ban hành về cùng vấn đề ➔ Áp dụng văn bản ban hành sau (Mới thay thế Cũ).\n"
            "3. Chuyên ngành vs Chung: Ưu tiên áp dụng quy định của Luật chuyên ngành so với Luật chung.\n"
            "4. Giá tính thuế: Nếu giá hợp đồng thấp hơn Bảng giá đất/giá Nhà nước quy định ➔ Áp dụng mức giá Nhà nước để tính nộp thuế.\n"
            "5. Xung đột mốc thời gian giao dịch: Nếu sự việc xảy ra ở thời điểm quá khứ (năm 2017...) ➔ Ưu tiên áp dụng văn bản đang có hiệu lực tại đúng thời điểm 2017 đó."
        )
        task_boundary = (
            "Chỉ âm thầm xử lý mâu thuẫn và cung cấp quyết định ưu tiên cho SynthesisAgent. "
            "Tuyệt đối không tự mình soạn thảo báo cáo tư vấn cuối cùng."
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
