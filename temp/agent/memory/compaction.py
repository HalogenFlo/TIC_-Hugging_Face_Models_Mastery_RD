# Chức năng: Nén ngữ cảnh hội thoại khi vượt ngưỡng giới hạn token (Context Compaction).

from typing import List, Dict, Any
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from config import get_ai_model, COMPACTION_TOKEN_THRESHOLD, DEFAULT_PROVIDER, MODEL_SUB_AGENT_GEMINI

def estimate_tokens(messages: List[BaseMessage]) -> int:
    """Ước lượng số lượng token của danh sách tin nhắn một cách nhanh chóng."""
    total_chars = 0
    for msg in messages:
        total_chars += len(msg.content)
    # Quy ước trung bình: 1 token ≈ 4 ký tự tiếng Việt/Anh
    return total_chars // 4

def compress_context(messages: List[BaseMessage], provider: str = DEFAULT_PROVIDER) -> List[BaseMessage]:
    """Nén ngữ cảnh hội thoại bằng cách tóm tắt các hội thoại cũ và giữ lại các hội thoại mới nhất."""
    token_count = estimate_tokens(messages)
    
    if token_count <= COMPACTION_TOKEN_THRESHOLD or len(messages) <= 6:
        return messages
        
    print(f"[INFO] Token count ({token_count}) vượt ngưỡng {COMPACTION_TOKEN_THRESHOLD}. Bắt đầu nén...")
    
    # Giữ lại tin nhắn hệ thống đầu tiên (nếu có)
    system_msg = None
    start_idx = 0
    if messages and messages[0].type == "system":
        system_msg = messages[0]
        start_idx = 1
        
    # Tách các tin nhắn cần tóm tắt và tin nhắn cần giữ lại (giữ lại 4 tin nhắn cuối cùng)
    messages_to_compact = messages[start_idx:-4]
    messages_to_keep = messages[-4:]
    
    # 1. Soạn thảo prompt tóm tắt
    conversation_text = []
    for msg in messages_to_compact:
        role = "Người dùng" if msg.type == "human" else "Trợ lý"
        conversation_text.append(f"{role}: {msg.content}")
    conversation_str = "\n".join(conversation_text)
    
    summary_instruction = (
        "Bạn là trợ lý ảo lưu trữ bộ nhớ ngắn hạn. Hãy tóm tắt lại diễn biến cuộc hội thoại sau đây "
        "thành các ý chính, tập trung vào những Facts (sự kiện, thông số người dùng cung cấp) và "
        "Preferences (yêu cầu cụ thể, loại thuế hay thửa đất) để giữ ngữ cảnh cho các lượt chat tiếp theo. "
        "Tóm tắt ngắn gọn dưới 300 từ."
    )
    
    summary_messages = [
        {"role": "system", "content": summary_instruction},
        {"role": "user", "content": f"Cuộc hội thoại cần tóm tắt:\n{conversation_str}"}
    ]
    
    try:
        model = get_ai_model(MODEL_SUB_AGENT_GEMINI, provider=provider)
        summary_text = model.generate(summary_messages)
    except Exception as e:
        print(f"[WARNING] Tạo tóm tắt nén ngữ cảnh thất bại: {e}")
        summary_text = "Lịch sử hội thoại trước đó đã được dọn dẹp để tối ưu hóa bộ nhớ."
        
    # 2. Xây dựng danh sách tin nhắn mới đã nén
    compacted_messages = []
    if system_msg:
        compacted_messages.append(system_msg)
        
    # Chèn tóm tắt ngữ cảnh cũ dưới dạng System Message
    context_summary_msg = SystemMessage(
        content=f"--- TÓM TẮT LỊCH SỬ HỘI THOẠI TRƯỚC ĐÓ ---\n{summary_text}\n------------------------------------------"
    )
    compacted_messages.append(context_summary_msg)
    
    # Thêm lại các tin nhắn cần giữ lại
    compacted_messages.extend(messages_to_keep)
    
    return compacted_messages
