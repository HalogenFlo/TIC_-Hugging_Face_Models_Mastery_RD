# Chức năng: LandLawAgent tư vấn chuyên sâu về các vấn đề liên quan đến luật Đất đai Việt Nam.

import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from agents.base import BaseAgent
from state import AgentState
from skills.search_retrieval import execute_search_retrieval
from skills.analysis import execute_deep_analysis
from config import (
    get_ai_model, 
    DEFAULT_PROVIDER, 
    MODEL_SUB_AGENT_GPT, 
    MODEL_SUB_AGENT_GEMINI
)

class CitationItem(BaseModel):
    norm_code: str = Field(description="Số hiệu văn bản pháp lý (ví dụ: 45/2013/QH13)")
    citation_name: str = Field(description="Tên điều khoản trích dẫn (ví dụ: Điều 10)")
    comp_id: Optional[str] = Field(None, description="ID thành phần tương ứng nếu có")

class LandLawOutput(BaseModel):
    draft_answer: str = Field(description="Câu trả lời nháp chi tiết bằng tiếng Việt, trích dẫn chính xác luật theo dạng [Số hiệu - Điều khoản].")
    citations: List[CitationItem] = Field(description="Danh sách các trích dẫn đã sử dụng.")
    requires_clarification: bool = Field(description="Đặt thành True nếu thiếu thông tin đầu vào từ người dùng để đưa ra kết luận pháp lý chính xác.")
    clarification_prompt: Optional[str] = Field(None, description="Câu hỏi làm rõ gửi đến người dùng nếu requires_clarification = True.")

class LandLawAgent(BaseAgent):
    """Tác nhân tư vấn chuyên sâu Luật Đất đai Việt Nam (Tầng 2)."""
    
    def __init__(self, provider: str = DEFAULT_PROVIDER):
        goal_context = (
            "Bạn là một chuyên gia tư vấn pháp luật Đất đai Việt Nam giàu kinh nghiệm. Nhiệm vụ của bạn là nhận "
            "câu hỏi của người dùng và các thông tin luật được cung cấp từ CSDL để đưa ra câu trả lời nháp có "
            "căn cứ pháp lý rõ ràng, chính xác.\n"
            "QUY TẮC XỬ LÝ ĐỐI TƯỢNG VÀ THỜI GIAN:\n"
            "1. Về Đối tượng: Nếu người dùng ĐÃ NÊU CỤ THỂ ĐỐI TƯỢNG (ví dụ: 'Tôi là doanh nghiệp tư nhân...', 'Tôi là hộ gia đình...'), "
            "hãy tập trung trả lời CHÍNH XÁC CHO ĐÚNG ĐỐI TƯỢNG ĐÓ. Chỉ khi người dùng KHÔNG nói rõ đối tượng mà luật có sự phân biệt, "
            "hãy phân tích đầy đủ tất cả các trường hợp phân lớp để họ tham khảo.\n"
            "2. Về Mốc Thời gian: Nếu người dùng KHÔNG NÓI GÌ VỀ MỐC THỜI GIAN, MẶC ĐỊNH 100% ÁP DỤNG VĂN BẢN LUẬT MỚI NHẤT HIỆN HÀNH. "
            "Chỉ khi người dùng NÊU RÕ MỐC/KHOẢNG THỜI GIAN QUÁ KHỨ CỤ THỂ (ví dụ: năm 2017, năm 2021...), "
            "mới áp dụng văn bản luật có hiệu lực tại đúng giai đoạn lịch sử đó.\n"
            "3. QUY TẮC TRÍCH GIẢI CHI TIẾT NỘI DUNG ĐIỀU LUẬT: Tuyệt đối KHÔNG chỉ trích dẫn tên điều khoản suông "
            "(như 'theo quy định tại Điều X Luật Đất đai...'). Bạn bắt buộc phải NÊU VÀ TRÍCH GIẢI RÕ NỘI DUNG CỤ THỂ CỦA ĐIỀU LUẬT ĐÓ "
            "(điều luật đó quy định những gì, điều kiện ra sao, thủ tục/quyền lợi thế nào...) dựa trên dữ liệu CSDL được cung cấp "
            "để người dùng đọc là hiểu ngay mà không cần phải tự đi tìm tra cứu lại."
        )
        task_boundary = (
            "Chỉ tư vấn và trả lời các nội dung liên quan đến Luật Đất đai Việt Nam. Phải trích dẫn chính xác "
            "các số hiệu văn bản và điều khoản theo cấu trúc chuẩn dạng [Số hiệu văn bản - Điều X - Khoản Y - Điểm Z] "
            "(ví dụ: [Luật Đất đai 2024 - Điều 10 - Khoản 2 - Điểm a]). "
            "Tuyệt đối không tự bịa đặt (hallucinate) các số hiệu văn bản hoặc nội dung điều luật không có trong tài liệu hỗ trợ."
        )
        skills_tools = ["search_retrieval", "analysis"]
        
        super().__init__(
            goal_context=goal_context,
            task_boundary=task_boundary,
            skills_tools=skills_tools,
            output_schema=LandLawOutput
        )
        self.provider = provider

    def _process_search_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Xử lý một kết quả tra cứu: trích xuất citation và phân tích lịch sử sửa đổi."""
        comp_id = item.get("comp_id")
        norm_number = item.get("norm_number", "Không rõ")
        citation_name = item.get("citation", "Không rõ")
        
        citation = {
            "norm_code": norm_number,
            "citation_name": citation_name,
            "comp_id": comp_id
        }
        
        if not comp_id:
            # Kết quả từ Web Search (Internet fallback)
            text_unit = item.get("accumulated_text") or ""
            return {
                "citation": citation,
                "context": f"=== TÀI LIỆU NGOÀI (INTERNET FALLBACK) ===\nNội dung:\n{text_unit}\n"
            }
        
        # Phân tích sâu điều khoản trên đồ thị
        try:
            analysis = execute_deep_analysis(comp_id)
            modifications = analysis.get("modifications", [])
            mod_texts = [
                f"- Bị sửa đổi/thay thế bởi văn bản {mod.get('amending_doc')} (Loại hành động: {mod.get('action_type')}). "
                f"Nội dung sửa đổi bổ sung: {mod.get('action_text', 'Không có chi tiết')}"
                for mod in modifications
            ]
            mod_desc = "\n".join(mod_texts) if mod_texts else "Không có sửa đổi bổ sung nào được ghi nhận trên đồ thị."
        except Exception as ae:
            print(f"[WARNING] execute_deep_analysis failed for comp_id {comp_id}: {ae}")
            mod_desc = "Không thể phân tích lịch sử sửa đổi do lỗi hệ thống."
        
        text_unit = item.get("accumulated_text") or ""
        context = (
            f"=== VĂN BẢN: {norm_number} - ĐIỀU KHOẢN: {citation_name} ===\n"
            f"ID thành phần: {comp_id}\n"
            f"Trạng thái hiệu lực thực tế: {item.get('validity_status', 'Không rõ')}\n"
            f"Nội dung văn bản gốc:\n{text_unit}\n"
            f"Lịch sử hiệu lực / sửa đổi:\n{mod_desc}\n"
        )
        return {"citation": citation, "context": context}

    def run(self, state: AgentState) -> Dict[str, Any]:
        """Thực thi nghiệp vụ tra cứu, phân tích và soạn thảo câu trả lời luật Đất đai."""
        query_text = state.get("refined_query") or state.get("raw_query", "")
        human_feedback = state.get("human_feedback", "")
        loop_step = state.get("loop_step", 0)
        
        # 1. Gọi Kỹ năng Tra cứu & Định vị Văn bản (Legal Search & Retrieval)
        try:
            search_results = execute_search_retrieval(query_text, provider=self.provider, limit=3)
        except Exception as se:
            print(f"[WARNING] execute_search_retrieval failed in LandLawAgent: {se}")
            search_results = []
            
        # 2. Xử lý từng kết quả tra cứu bằng Kỹ năng Phân tích sâu (Deep Analysis)
        processed = list(map(self._process_search_item, search_results))
        citations_found = [p["citation"] for p in processed]
        detailed_context = [p["context"] for p in processed]
        
        # 3. Tổng hợp ngữ cảnh truyền cho LLM suy luận
        context_str = "\n\n".join(detailed_context) if detailed_context else "Không tìm thấy tài liệu pháp lý liên quan trong CSDL."
        
        system_instruction = (
            f"{self.goal_context}\n"
            f"Ràng buộc nhiệm vụ: {self.task_boundary}\n\n"
            "Hãy đọc kỹ câu hỏi của người dùng và dữ liệu pháp luật hỗ trợ được cung cấp để đưa ra câu trả lời chính xác, "
            "logic và đúng căn cứ pháp luật. Lưu ý đối chiếu trạng thái hiệu lực thực tế (Hết hiệu lực hay Hết hiệu lực một phần...) "
            "và thông tin sửa đổi bổ sung để cảnh báo cho người dùng nếu điều luật đó không còn hiệu lực đầy đủ.\n"
            "ĐẶC BIỆT LƯU Ý VỀ XUNG ĐỘT THỜI GIAN: Nếu phát hiện điều luật có sự thay đổi nội dung/thuế suất/hình phạt qua các thời kỳ "
            "mà câu hỏi người dùng không nêu rõ mốc thời gian xảy ra sự việc, hãy áp dụng CHIẾN LƯỢC TRẢ LỜI PHÂN NHÁNH THEO ĐIỀU KIỆN THỜI GIAN: "
            "trình bày rõ ràng câu trả lời tương ứng với từng thời kỳ/mốc hiệu lực (ví dụ: trước khi sửa đổi áp dụng mức nào, từ ngày văn bản sửa đổi "
            "có hiệu lực áp dụng mức nào) ngay trong draft_answer để người dùng có đầy đủ căn cứ đối chiếu.\n"
            "Nếu dữ liệu hỗ trợ không đủ để đưa ra kết luận chắc chắn hoặc câu hỏi quá mơ hồ, hãy thiết lập requires_clarification = True "
            "và viết một câu hỏi làm rõ tinh tế trong clarification_prompt để hướng dẫn người dùng bổ sung thông tin."
        )
        
        user_profile = state.get("user_profile", {})
        profile_text = f"Hồ sơ người dùng đã lưu từ các phiên trước: {user_profile}\n" if user_profile else ""

        user_content = (
            f"{profile_text}"
            f"Câu hỏi của người dùng: {query_text}\n\n"
            f"Dữ liệu pháp luật hỗ trợ tra cứu:\n{context_str}\n"
        )
        
        # Đính kèm feedback sửa lỗi từ Verifier nếu đây là lượt chạy sửa đổi
        if loop_step > 0 and human_feedback:
            user_content += (
                f"\n\n=== PHẢN HỒI YÊU CẦU CHỈNH SỬA TỪ KIỂM SOÁT VIÊN (LƯỢT #{loop_step}) ===\n"
                f"Báo cáo nháp trước đó của bạn chưa đạt yêu cầu do: {human_feedback}\n"
                f"Hãy điều chỉnh và sửa đổi nội dung câu trả lời nháp của bạn để khắc phục hoàn toàn lỗi trên."
            )
        
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content}
        ]
        
        model_name = MODEL_SUB_AGENT_GPT if self.provider == "openai" else MODEL_SUB_AGENT_GEMINI
        model = get_ai_model(model_name, provider=self.provider)
        
        try:
            # 4. Sinh và parse phản hồi có cấu trúc
            raw_output = model.generate(messages, response_schema=self.output_schema)
            parsed = self.output_schema.model_validate_json(raw_output)
            return parsed.model_dump()
        except Exception as e:
            # Fallback an toàn nếu LLM hoặc parse lỗi
            print(f"[ERROR] LLM generation failed in LandLawAgent: {e}")
            import traceback
            traceback.print_exc()
            return {
                "draft_answer": "Không thể soạn thảo câu trả lời do lỗi hệ thống trong quá trình gọi mô hình ngôn ngữ.",
                "citations": citations_found,
                "requires_clarification": False,
                "clarification_prompt": None
            }
