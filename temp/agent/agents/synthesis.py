# Chức năng: SynthesisAgent tổng hợp các câu trả lời nháp và kết quả mâu thuẫn thành báo cáo chính thức.
# Lý do tạo: Tác nhân tổng hợp & xác thực đầu ra (Tầng 2) trước khi gửi cho người dùng.
# Link trích dẫn: https://github.com/HalogenFlo/TIC_-Hugging_Face_Models_Mastery_RD

import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from agents.base import BaseAgent
from state import AgentState
from skills.reporting import execute_reporting_and_validation
from config import (
    get_ai_model, 
    DEFAULT_PROVIDER, 
    MODEL_SUB_AGENT_GPT, 
    MODEL_SUB_AGENT_GEMINI
)

class CitationItem(BaseModel):
    norm_code: str = Field(description="Số hiệu văn bản pháp lý (ví dụ: 103/2014/TT-BTC)")
    citation_name: str = Field(description="Tên điều khoản trích dẫn (ví dụ: Điều 10)")
    comp_id: Optional[str] = Field(None, description="ID thành phần tương ứng nếu có")

class SynthesisOutput(BaseModel):
    final_answer: str = Field(description="Báo cáo tư vấn pháp lý chính thức đã tổng hợp và giải quyết mâu thuẫn, định dạng Markdown.")
    all_citations: List[CitationItem] = Field(default_factory=list, description="Danh sách toàn bộ các trích dẫn pháp lý thu thập được từ các tác nhân con.")
    requires_clarification: bool = Field(description="Đặt thành True nếu bất kỳ sub-agent nào yêu cầu làm rõ thêm và chưa được giải quyết.")
    clarification_prompt: Optional[str] = Field(None, description="Câu hỏi làm rõ gộp lại gửi tới người dùng.")

class SynthesisAgent(BaseAgent):
    """Tác nhân tổng hợp báo cáo tư vấn pháp luật chính thức (Tầng 2)."""

    def __init__(self, provider: str = DEFAULT_PROVIDER):
        goal_context = (
            "Bạn là chuyên gia biên soạn báo cáo pháp lý Việt Nam. Nhiệm vụ của bạn là nhận câu hỏi ban đầu, "
            "câu trả lời nháp từ các domain sub-agents (Thuế, Đất đai) và kết quả xử lý mâu thuẫn pháp lý từ Conflict Agent "
            "để tổng hợp thành một bản báo cáo tư vấn pháp lý chính thức, mạch lạc, dễ hiểu, chuyên nghiệp và có căn cứ luật rõ ràng.\n"
            "Nếu có mâu thuẫn pháp luật phát hiện được, hãy giải thích rõ ràng cho người dùng biết mâu thuẫn đó nằm ở đâu "
            "và nguyên tắc/cách hệ thống quyết định áp dụng điều khoản nào để họ yên tâm đối chiếu."
        )
        task_boundary = (
            "Chỉ tổng hợp và biên soạn báo cáo. Tuyệt đối không tự sáng tạo ra điều luật "
            "hoặc tự bịa ra thông tin không có trong các tài liệu hỗ trợ."
        )
        skills_tools = ["reporting"]
        
        super().__init__(
            goal_context=goal_context,
            task_boundary=task_boundary,
            skills_tools=skills_tools,
            output_schema=SynthesisOutput
        )
        self.provider = provider

    def run(self, state: AgentState) -> Dict[str, Any]:
        """Thực thi suy luận tổng hợp và gọi Skill Tầng 1 để kiểm chứng/định dạng."""
        query_text = state.get("refined_query") or state.get("raw_query", "")
        domain_outputs = state.get("domain_outputs", {})
        conflicts = state.get("conflicts", [])
        
        # 1. Tập hợp các câu trả lời nháp và citations từ domain agents
        drafts = []
        drafts_for_report = []
        all_citations_raw = []
        requires_clarification = False
        clarification_prompts = []
        
        for domain, output in domain_outputs.items():
            draft_text = output.get("draft_answer", "")
            drafts.append(f"Nháp của Sub-Agent {domain.upper()}:\n{draft_text}")
            drafts_for_report.append({
                "domain": domain,
                "analysis": draft_text
            })
            if output.get("requires_clarification"):
                requires_clarification = True
                if output.get("clarification_prompt"):
                    clarification_prompts.append(output.get("clarification_prompt"))
            for cite in output.get("citations", []):
                all_citations_raw.append(cite)
                
        # 2. Tập hợp thông tin mâu thuẫn
        conflict_desc = []
        conflicts_for_report = []
        for conf in conflicts:
            conflict_desc.append(
                f"- Phát hiện mâu thuẫn dạng '{conf.get('conflict_type')}' tại văn bản áp dụng {conf.get('resolved_norm_code')}. "
                f"Mô tả: {conf.get('description')}. Quy tắc giải quyết: {conf.get('resolving_rule')}."
            )
            conflicts_for_report.append({
                "doc_code": conf.get("resolved_norm_code", "Không rõ"),
                "type": conf.get("conflict_type", "Không rõ"),
                "description": f"{conf.get('description', '')}. Hướng xử lý: {conf.get('resolving_rule', '')}"
            })
            
        drafts_str = "\n\n".join(drafts)
        conflicts_str = "\n".join(conflict_desc) if conflict_desc else "Không phát hiện mâu thuẫn nào."
        
        system_instruction = (
            f"{self.goal_context}\n"
            f"Ràng buộc: {self.task_boundary}"
        )
        
        user_content = (
            f"Câu hỏi gốc: '{query_text}'\n\n"
            f"Các câu trả lời nháp của chuyên viên:\n{drafts_str}\n\n"
            f"Thông tin mâu thuẫn luật phát hiện được:\n{conflicts_str}\n"
        )
        
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content}
        ]
        
        model_name = MODEL_SUB_AGENT_GPT if self.provider == "openai" else MODEL_SUB_AGENT_GEMINI
        model = get_ai_model(model_name, provider=self.provider)
        
        # 3. LLM soạn thảo báo cáo tổng hợp nháp sơ bộ
        try:
            raw_output = model.generate(messages, response_schema=self.output_schema)
            parsed = self.output_schema.model_validate_json(raw_output)
            output_dict = parsed.model_dump()
        except Exception as e:
            print(f"[ERROR] LLM generation failed in SynthesisAgent: {e}")
            output_dict = {
                "final_answer": "Không thể tổng hợp báo cáo do lỗi hệ thống trong quá trình gọi mô hình ngôn ngữ.",
                "all_citations": all_citations_raw,
                "requires_clarification": requires_clarification,
                "clarification_prompt": clarification_prompts[0] if clarification_prompts else None
            }
            
        # 4. Gọi Skill Tầng 1 (Reporting Skill) để đối chiếu nguồn Neo4j và định dạng Markdown
        raw_data = {
            "query": query_text,
            "details": drafts_for_report,
            "conflicts": conflicts_for_report
        }
        
        try:
            report_result = execute_reporting_and_validation(
                draft_answer=output_dict["final_answer"],
                raw_data=raw_data,
                provider=self.provider,
                format_type="markdown"
            )
            # Thay thế bằng nội dung báo cáo đã qua validate và format đẹp đẽ
            if report_result.get("report_content"):
                output_dict["final_answer"] = report_result["report_content"]
        except Exception as re:
            print(f"[WARNING] execute_reporting_and_validation failed in SynthesisAgent: {re}")
            
        return output_dict
