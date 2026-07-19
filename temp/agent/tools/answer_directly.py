# Chức năng: Helper bypass tạo phản hồi trực tiếp cho chitchat hoặc câu hỏi ngoài phạm vi nghiệp vụ bằng LLM.

# Lưu ý kiến trúc: hàm này gọi LLM nên phù hợp làm bypass node/helper ở tầng orchestrator hơn là raw data tool.

from typing import Optional
from config import (
    get_ai_model, 
    DEFAULT_PROVIDER, 
    MODEL_ORCHESTRATOR_GPT, 
    MODEL_ORCHESTRATOR_GEMINI
)

def answer_directly(query: str, provider: str = DEFAULT_PROVIDER) -> str:
    """Bypass pipeline và tạo phản hồi trực tiếp, thân thiện cho các câu hỏi ngoài nghiệp vụ pháp lý."""
    # 1. Xác định mô hình điều phối tương ứng với nhà cung cấp
    model_name = MODEL_ORCHESTRATOR_GPT if provider == "openai" else MODEL_ORCHESTRATOR_GEMINI
    
    # 2. Khởi tạo LLM adapter
    model = get_ai_model(model_name, provider=provider)
    
    # 3. Tạo prompt hướng dẫn chitchat/Out-of-Scope
    system_instruction = (
        "Bạn là một trợ lý ảo thông minh chuyên về tư vấn pháp luật Việt Nam (như luật Thuế, luật Đất đai). "
        "Người dùng hiện tại đang chào hỏi hoặc chitchat/nói chuyện ngoài lề không liên quan đến pháp luật. "
        "Hãy phản hồi một cách ngắn gọn, thân thiện, lịch sự và tinh tế hướng người dùng đặt các câu hỏi "
        "liên quan đến lĩnh vực tư vấn pháp lý Việt Nam."
    )
    
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": query}
    ]
    
    # 4. Sinh phản hồi
    try:
        response_text = model.generate(messages)
        return response_text.strip()
    except Exception as e:
        return f"Xin chào! Tôi có thể giúp gì cho bạn về các vấn đề pháp luật Việt Nam (Thuế, Đất đai...) hôm nay? (Lỗi kết nối: {str(e)})"
