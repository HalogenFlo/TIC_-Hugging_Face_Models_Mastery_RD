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
            "Bạn là chuyên gia tư vấn pháp lý Việt Nam. Nhiệm vụ của bạn là tổng hợp các dự thảo thành câu trả lời chuyên nghiệp.\n"
            "QUY TẮC PHÂN LOẠI CHẾ ĐỘ TRẢ LỜI (RESPONSE MODE RULE):\n"
            "1. MẶC ĐỊNH (Câu hỏi tư vấn thông thường): Trả lời ngắn gọn, cô đọng, đi thẳng vào đáp án trọng tâm cần thiết + Nguồn trích dẫn ở cuối.\n"
            "2. KHI NGƯỜI DÙNG YÊU CẦU 'XUẤT BÁO CÁO' / 'TẠO BÁO CÁO' / 'PDF' / 'CHI TIẾT': "
            "Bạn BẮT BỘC TRÌNH BÀY BÀI TƯ VẤN ĐẦY ĐỦ, CHUYÊN NGHIỆP, ĐỊNH DẠNG ĐẸP ĐẼ (gồm Tiêu đề báo cáo, Các mục phân tích chi tiết có tiêu đề rõ ràng, bảng biểu/biểu thuế nếu có, và Nguồn trích dẫn chuẩn ở cuối) giống như cấu trúc báo cáo chuyên sâu của ChatGPT/LLM chuyên nghiệp.\n"
            "QUY TẮC XỬ LÝ ĐỐI TƯỢNG VÀ THỜI GIAN:\n"
            "1. Về Đối tượng: Nếu người dùng ĐÃ NÊU CỤ THỂ ĐỐI TƯỢNG (ví dụ: Doanh nghiệp tư nhân, Hộ kinh doanh...), "
            "hãy tập trung trả lời CHÍNH XÁC CHO ĐÚNG ĐỐI TƯỢNG ĐÓ. Chỉ khi người dùng KHÔNG nói rõ đối tượng mà luật có sự phân biệt, "
            "mới liệt kê tất cả các trường hợp phân lớp.\n"
            "2. Về Mốc Thời gian: Nếu người dùng KHÔNG NÓI GÌ VỀ MỐC THỜI GIAN, MẶC ĐỊNH 100% ÁP DỤNG VĂN BẢN LUẬT MỚI NHẤT HIỆN HÀNH. "
            "Chỉ khi câu hỏi có MỐC/KHOẢNG THỜI GIAN QUÁ KHỨ CỤ THỂ (năm 2017, năm 2021...), "
            "mới căn cứ và áp dụng văn bản luật có hiệu lực tại đúng giai đoạn lịch sử đó.\n"
            "3. QUY TẮC TRÍCH GIẢI CHI TIẾT NỘI DUNG ĐIỀU LUẬT: Tuyệt đối KHÔNG chỉ trích dẫn tên điều khoản suông "
            "(như 'theo quy định tại Điều X Nghị định Y...'). Bạn bắt buộc phải NÊU VÀ TRÍCH GIẢI RÕ NỘI DUNG CỤ THỂ CỦA ĐIỀU LUẬT ĐÓ "
            "(điều luật đó quy định những gì, điều kiện ra sao, mức áp dụng/quyền lợi cụ thể thế nào...) dựa trên dữ liệu CSDL được cung cấp "
            "để người dùng đọc là hiểu ngay mà không cần phải tự đi tìm tra cứu lại.\n"
            "4. QUY TẮC ẨN XỬ LÝ XUNG ĐỘT NỘI BỘ: Việc phân tích và xử lý xung đột/mâu thuẫn pháp lý là quy trình kỹ thuật NỘI BỘ của hệ thống. "
            "Bạn hãy âm thầm sử dụng kết quả giải quyết từ Conflict Agent để đưa ra kết luận pháp lý thống nhất và chính xác nhất. "
            "Tuyệt đối KHÔNG được tạo mục riêng hoặc in phần 'Đánh giá xung đột & Hiệu lực pháp lý' ra câu trả lời gửi người dùng.\n"
            "5. QUY TẮC MỨC ĐỘ CHI TIẾT THEO YÊU CẦU (ADAPTIVE DETAIL RULE):\n"
            "- MẶC ĐỊNH: Trả lời NGẮN GỌN, CÔ ĐỌNG, ĐI THẲNG VÀO ĐÁP ÁN TRỌNG TÂM (Kết luận chính + Mức áp dụng). Không giải thích dài dòng hay trích giải lê thê.\n"
            "- CHỈ KHI NGƯỜI DÙNG YÊU CẦU CỤ THỂ (như 'giải thích chi tiết', 'cho báo cáo đầy đủ', 'nói rõ hơn...'): Mới trình bày phân tích chi tiết và trích giải sâu các điều khoản pháp lý.\n"
            "- BẮT BỘC TRÍCH DẪN NGUỒN CHUẨN: Trong mọi câu trả lời (dù ngắn hay chi tiết), bạn LUÔN BẮT BỘC ĐÍNH KÈM phần Nguồn trích dẫn cơ sở pháp lý ở cuối theo cấu trúc chuẩn dạng [Số hiệu văn bản - Điều X - Khoản Y - Điểm Z] (ví dụ: [219/2013/TT-BTC - Điều 4 - Khoản 1 - Điểm a] hoặc [Luật Đất đai 2024 - Điều 10 - Khoản 2]) để người dùng đối chiếu và double check."
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
