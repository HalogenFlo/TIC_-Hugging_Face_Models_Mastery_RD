# Hướng dẫn Vận hành Hệ thống Legal-MAS (Web UI)

Hệ thống Trợ lý Tư vấn Pháp luật Đa tác nhân (Legal-MAS) chuyên biệt cho Luật Đất Đai & Luật Thuế Việt Nam chạy trên nền tảng LangGraph.

---

## 1. Cài đặt Thư viện Yêu cầu

Cài đặt các thư viện Python cần thiết bằng cách chạy lệnh sau từ thư mục gốc của dự án:

```bash
pip install -r requirements.txt
```

---

## 2. Cấu hình Môi trường (.env)

Đảm bảo bạn đã cấu hình các biến môi trường cần thiết trong file `.env` tại thư mục gốc, bao gồm các cấu hình:
*   **API Keys**: `GEMINI_API_KEY` hoặc `OPENAI_API_KEY`.
*   **CSDL Neo4j (GraphRAG)**: Địa chỉ URI và thông tin xác thực tài khoản.
*   **CSDL Redis (Session Memory)**: Địa chỉ host và port của Redis.
*   **CSDL PostgreSQL (Long-term Profile)**: Thông tin kết nối để lưu hồ sơ người dùng dài hạn.

---

## 3. Khởi chạy Giao diện Web UI (Không dùng CLI)

Khởi chạy máy chủ HTTP phục vụ API và Static Files cục bộ:

```bash
python app/server.py
```

Sau khi máy chủ khởi động thành công, hãy mở trình duyệt Web và truy cập địa chỉ:

```
http://localhost:8000
```

---

## 4. Các tính năng nổi bật trên Web UI

*   **Premium Dark UI**: Giao diện Glassmorphic hiện đại, tối ưu hóa trải nghiệm đọc báo cáo tư vấn.
*   **Visualizer LangGraph**: Hiển thị hoạt họa quy trình chạy trực quan qua các node tác nhân trong thời gian thực.
*   **Clarification Dialog**: Tự động chuyển đổi giao diện khi hệ thống cần hỏi lại để làm rõ câu hỏi.
*   **Đồng bộ Hồ sơ dài hạn**: Tự động trích xuất thông tin Facts & Preferences để cập nhật trực tiếp lên thanh Sidebar từ PostgreSQL.
