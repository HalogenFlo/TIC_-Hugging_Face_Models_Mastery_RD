# Chức năng: Lưu trữ và đồng bộ bộ nhớ ngắn hạn (Redis) và bộ nhớ dài hạn (PostgreSQL).

import json
from typing import Dict, Any, List, Optional
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from config import get_redis_client, get_db_connection, get_ai_model, DEFAULT_PROVIDER, MODEL_SUB_AGENT_GEMINI

# --- HELPER TUẦN TỰ HÓA TIN NHẮN LANGCHAIN ---

def serialize_messages(messages: List[BaseMessage]) -> str:
    """Chuyển đổi danh sách tin nhắn thành chuỗi JSON."""
    serialized = []
    for msg in messages:
        serialized.append({
            "type": msg.type,
            "content": msg.content,
            "additional_kwargs": msg.additional_kwargs
        })
    return json.dumps(serialized, ensure_ascii=False)

def deserialize_messages(json_str: str) -> List[BaseMessage]:
    """Khôi phục danh sách tin nhắn từ chuỗi JSON."""
    try:
        data = json.loads(json_str)
        messages = []
        for item in data:
            msg_type = item.get("type", "human")
            content = item.get("content", "")
            kwargs = item.get("additional_kwargs", {})
            if msg_type == "system":
                messages.append(SystemMessage(content=content, additional_kwargs=kwargs))
            elif msg_type == "human":
                messages.append(HumanMessage(content=content, additional_kwargs=kwargs))
            elif msg_type == "ai":
                messages.append(AIMessage(content=content, additional_kwargs=kwargs))
            else:
                messages.append(HumanMessage(content=content, additional_kwargs=kwargs))
        return messages
    except Exception as e:
        print(f"[WARNING] Giải tuần tự hóa tin nhắn thất bại: {e}")
        return []

# --- SQL HELPER ROBUST ---

def execute_sql(query: str, params: tuple = ()) -> Optional[List[tuple]]:
    """Thực thi truy vấn SQL tương thích cả SQLAlchemy, psycopg2 và pymysql."""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        if hasattr(conn, "execute") and not hasattr(conn, "cursor"):
            # Thích ứng với SQLAlchemy Connection
            from sqlalchemy import text
            result = conn.execute(text(query), params)
            # Thử commit nếu database có hỗ trợ autocommit=False
            try:
                if hasattr(conn, "commit"):
                    conn.commit()
            except Exception:
                pass
            if query.strip().upper().startswith("SELECT"):
                return [row for row in result]
            return None
        else:
            # Thích ứng với psycopg2 / pymysql connection
            cursor = conn.cursor()
            cursor.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                res = cursor.fetchall()
                cursor.close()
                return res
            conn.commit()
            cursor.close()
            return None
    except Exception as e:
        print(f"[WARNING] SQL execution failed: {e}")
        return None

def init_db_schema():
    """Khởi tạo cấu trúc bảng user_profiles tự phục hồi nếu chưa tồn tại."""
    create_table_query = """
    CREATE TABLE IF NOT EXISTS user_profiles (
        user_id VARCHAR(100) PRIMARY KEY,
        profile TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    execute_sql(create_table_query)

# --- SHORT-TERM MEMORY (REDIS) ---

def save_session_state(session_id: str, state: Dict[str, Any]) -> bool:
    """Lưu trữ AgentState hiện tại lên Redis theo session_id."""
    r = get_redis_client()
    if r is None:
        return False
    try:
        # Copy và chuyển đổi messages trước khi chuyển JSON
        state_copy = dict(state)
        if "messages" in state_copy:
            state_copy["messages"] = serialize_messages(state_copy["messages"])
            
        r.set(f"session:{session_id}", json.dumps(state_copy, ensure_ascii=False))
        return True
    except Exception as e:
        print(f"[WARNING] Không thể lưu session state lên Redis: {e}")
        return False

def load_session_state(session_id: str) -> Optional[Dict[str, Any]]:
    """Tải và khôi phục AgentState từ Redis theo session_id."""
    r = get_redis_client()
    if r is None:
        return None
    try:
        raw_data = r.get(f"session:{session_id}")
        if not raw_data:
            return None
        state = json.loads(raw_data)
        if "messages" in state:
            state["messages"] = deserialize_messages(state["messages"])
        return state
    except Exception as e:
        print(f"[WARNING] Không thể tải session state từ Redis: {e}")
        return None

# --- LONG-TERM MEMORY (POSTGRESQL PROFILE) ---

def load_user_profile(user_id: str) -> Dict[str, Any]:
    """Tải hồ sơ người dùng (Facts & Preferences) dài hạn từ PostgreSQL."""
    init_db_schema()
    query = "SELECT profile FROM user_profiles WHERE user_id = %s"
    rows = execute_sql(query, (user_id,))
    if rows:
        try:
            return json.loads(rows[0][0])
        except Exception:
            pass
    return {"facts": [], "preferences": []}

def save_user_profile(user_id: str, profile: Dict[str, Any]) -> bool:
    """Lưu hồ sơ người dùng dài hạn vào PostgreSQL."""
    init_db_schema()
    profile_str = json.dumps(profile, ensure_ascii=False)
    
    # Thực hiện UPSERT tương thích
    check_query = "SELECT 1 FROM user_profiles WHERE user_id = %s"
    exists = execute_sql(check_query, (user_id,))
    
    if exists:
        update_query = "UPDATE user_profiles SET profile = %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s"
        execute_sql(update_query, (profile_str, user_id))
    else:
        insert_query = "INSERT INTO user_profiles (user_id, profile) VALUES (%s, %s)"
        execute_sql(insert_query, (user_id, profile_str))
    return True

def sync_long_term_memory(user_id: str, new_messages: List[BaseMessage], provider: str = DEFAULT_PROVIDER) -> Dict[str, Any]:
    """Gọi LLM phân tích tin nhắn mới để trích xuất thêm Facts/Preferences và lưu vào Postgres."""
    current_profile = load_user_profile(user_id)
    
    if not new_messages:
        return current_profile
        
    conversation_text = []
    for msg in new_messages[-4:]:  # Chỉ phân tích 4 tin nhắn gần nhất để tối ưu
        role = "User" if msg.type == "human" else "Assistant"
        conversation_text.append(f"{role}: {msg.content}")
    conversation_str = "\n".join(conversation_text)
    
    system_instruction = (
        "Bạn là chuyên gia quản lý thông tin khách hàng. Hãy phân tích cuộc trò chuyện của khách hàng "
        "để trích xuất ra các Sự kiện (Facts - ví dụ: là chủ đất, doanh nghiệp FDI...) và Sở thích/Yêu cầu cụ thể "
        "(Preferences - ví dụ: muốn gửi báo cáo qua email, cần gấp...). "
        "Hãy so sánh và bổ sung các thông tin này vào hồ sơ JSON hiện có của họ một cách ngắn gọn.\n"
        "Định dạng trả về bắt buộc phải tuân thủ JSON Schema sau:\n"
        "{\n"
        "  \"facts\": [\"chuỗi sự kiện 1\", \"chuỗi sự kiện 2\"],\n"
        "  \"preferences\": [\"sở thích 1\", \"sở thích 2\"]\n"
        "}"
    )
    
    user_content = (
        f"Hồ sơ người dùng hiện tại:\n{json.dumps(current_profile, ensure_ascii=False)}\n\n"
        f"Tin nhắn mới gần đây:\n{conversation_str}"
    )
    
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_content}
    ]
    
    try:
        model = get_ai_model(MODEL_SUB_AGENT_GEMINI, provider=provider)
        raw_output = model.generate(messages)
        # Loại bỏ các block markdown json nếu LLM trả về
        clean_json = raw_output.replace("```json", "").replace("```", "").strip()
        parsed_new = json.loads(clean_json)
        
        # Merge kết quả
        merged_profile = {
            "facts": list(set(current_profile.get("facts", []) + parsed_new.get("facts", []))),
            "preferences": list(set(current_profile.get("preferences", []) + parsed_new.get("preferences", [])))
        }
        
        save_user_profile(user_id, merged_profile)
        return merged_profile
    except Exception as e:
        print(f"[WARNING] Trích xuất long-term memory thất bại: {e}")
        return current_profile
