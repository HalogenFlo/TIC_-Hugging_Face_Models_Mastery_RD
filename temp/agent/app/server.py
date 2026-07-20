# Chức năng: Máy chủ Backend HTTP phục vụ API và Static Files cho ứng dụng Web UI.
# Lý do tạo: Thay thế CLI bằng giao diện Web UI tương tác trực tiếp (Tầng 5).
# Link trích dẫn: https://github.com/HalogenFlo/TIC_-Hugging_Face_Models_Mastery_RD

import os
import sys
import json
import http.server
from typing import Dict, Any, List

# Thêm thư mục gốc vào PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph import build_graph
from memory.memory_store import sync_long_term_memory, load_user_profile

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

def merge_state(current_state: dict, update: dict) -> dict:
    """Gộp state thủ công tương thích với các reducer định nghĩa trong state.py."""
    new_state = dict(current_state)
    for key, val in update.items():
        if key in ["detected_domains", "conflicts", "citations"]:
            new_state[key] = (new_state.get(key) or []) + (val or [])
        elif key in ["domain_outputs", "evaluation"]:
            new_state[key] = {**(new_state.get(key) or {}), **(val or {})}
        else:
            new_state[key] = val
    return new_state

class WebUIRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handler xử lý phục vụ trang chủ index.html và API endpoint chat."""

    def __init__(self, *args, **kwargs):
        # Thiết lập thư mục phục vụ static files là thư mục app/
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        """Xử lý định tuyến cho yêu cầu GET static files."""
        if self.path in ["/", "/index.html"]:
            self.path = "/index.html"
            return super().do_GET()
        return super().do_GET()

    def do_POST(self):
        """Xử lý API Endpoint POST cho giao dịch chat."""
        if self.path == "/api/chat":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                request_json = json.loads(post_data.decode('utf-8'))
                raw_query = request_json.get("raw_query", "").strip()
                user_id = request_json.get("user_id", "web_user_01")
                previous_state = request_json.get("state", {})
                
                # 1. Khởi tạo/Khôi phục state hội thoại
                state = {
                    "user_id": user_id,
                    "user_profile": previous_state.get("user_profile") or load_user_profile(user_id),
                    "messages": [],
                    "raw_query": raw_query,
                    "refined_query": previous_state.get("refined_query", ""),
                    "effort_level": previous_state.get("effort_level", "simple"),
                    "clarification_count": previous_state.get("clarification_count", 0),
                    "detected_domains": previous_state.get("detected_domains", []),
                    "domain_outputs": previous_state.get("domain_outputs", {}),
                    "conflicts": previous_state.get("conflicts", []),
                    "draft_answer": previous_state.get("draft_answer", ""),
                    "citations": previous_state.get("citations", []),
                    "evaluation": previous_state.get("evaluation", {}),
                    "loop_step": previous_state.get("loop_step", 0),
                    "human_feedback": previous_state.get("human_feedback", "")
                }
                
                # Cập nhật thông tin làm rõ nếu lượt trước là clarification
                if previous_state.get("effort_level") == "clarification":
                    state["raw_query"] = f"{previous_state.get('raw_query')} (Thông tin bổ sung: {raw_query})"
                    state["effort_level"] = "simple"  # Reset
                
                # 2. Xây dựng và chạy đồ thị LangGraph
                app = build_graph()
                final_state = state
                nodes_executed = []
                
                # Stream đồ thị và ghi nhận các Node thực thi
                for output in app.stream(state):
                    for node_name, node_output in output.items():
                        nodes_executed.append(node_name)
                        final_state = merge_state(final_state, node_output)
                
                # 3. Đồng bộ bộ nhớ dài hạn nếu tư vấn thành công và có câu trả lời
                if final_state.get("effort_level") != "clarification" and final_state.get("draft_answer"):
                    from langchain_core.messages import HumanMessage, AIMessage
                    chat_history = [
                        HumanMessage(content=final_state.get("raw_query", "")),
                        AIMessage(content=final_state.get("draft_answer", ""))
                    ]
                    new_profile = sync_long_term_memory(user_id, chat_history)
                    final_state["user_profile"] = new_profile
                
                # Tạo payload kết quả phản hồi
                response_data = {
                    "success": True,
                    "nodes_executed": nodes_executed,
                    "draft_answer": final_state.get("draft_answer"),
                    "effort_level": final_state.get("effort_level"),
                    "human_feedback": final_state.get("human_feedback"),
                    "detected_domains": final_state.get("detected_domains"),
                    # Trả lại state dạng rút gọn để frontend lưu trữ duy trì phiên tiếp theo
                    "state": {
                        "user_profile": final_state.get("user_profile"),
                        "raw_query": final_state.get("raw_query"),
                        "refined_query": final_state.get("refined_query"),
                        "effort_level": final_state.get("effort_level"),
                        "clarification_count": final_state.get("clarification_count"),
                        "detected_domains": final_state.get("detected_domains"),
                        "domain_outputs": final_state.get("domain_outputs"),
                        "conflicts": final_state.get("conflicts"),
                        "draft_answer": final_state.get("draft_answer"),
                        "citations": final_state.get("citations"),
                        "evaluation": final_state.get("evaluation"),
                        "loop_step": final_state.get("loop_step"),
                        "human_feedback": final_state.get("human_feedback")
                    }
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    server_address = ('', PORT)
    httpd = http.server.HTTPServer(server_address, WebUIRequestHandler)
    print(f"\n[INFO] Web UI Server is running at: http://localhost:{PORT}")
    print("[INFO] Press Ctrl+C to stop the server.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Stopping server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
