<!-- 
Chức năng: Báo cáo kỹ thuật chi tiết về việc cấu hình lại LLM Provider sang OpenAI và cơ chế tự phục hồi lỗi DB (SQLite Fallback).
Lý do tạo: Tuân thủ quy định báo cáo bắt buộc (Immediate Reporting) sau khi chỉnh sửa config.py và .env của hệ thống.
Link trích dẫn: [config.py](file:///c:/Users/Admin/Desktop/TIC_Project/temp/agent/config.py)
-->

# Báo Cáo Kỹ Thuật: Cấu Hình OpenAI và Tự Động Phục Hồi Database (SQLite Fallback)

Báo cáo này tài liệu hóa chi tiết các thay đổi trong việc thay đổi mô hình LLM mặc định sang `gpt-4o-mini` (thông qua OpenAI / GitHub Models API) để khắc phục lỗi hết quota Gemini (Error 429), đồng thời bổ sung cơ chế tự động chuyển đổi database sang SQLite cục bộ để khắc phục lỗi kết nối PostgreSQL.

---

## 1. Các Thay Đổi Về Cấu Hình Hệ Thống

### 1.1. Cấu hình file `.env`
*   **File sửa đổi:** [.env](file:///c:/Users/Admin/Desktop/TIC_Project/temp/agent/.env)
*   **Nội dung thay đổi:** Đổi `LLM_PROVIDER` từ `gemini` sang `openai`.
*   **Mục đích:** Đặt OpenAI làm nhà cung cấp mô hình ngôn ngữ mặc định toàn hệ thống.

### 1.2. Sửa đổi trong `config.py`
*   **File sửa đổi:** [config.py](file:///c:/Users/Admin/Desktop/TIC_Project/temp/agent/config.py)
*   **Chi tiết sửa đổi:**
    1.  **Hàm `get_ai_model`:**
        *   *Chức năng:* Trả về model adapter tương ứng với provider.
        *   *Thay đổi:* Thêm logic tự động mapping model name thông minh. Nếu `provider == "openai"` nhưng các agent con yêu cầu model Gemini (do bị hardcode tên model Gemini), hệ thống sẽ tự động chuyển sang sử dụng `"gpt-4o-mini"`.
    2.  **Hàm `get_embedding`:**
        *   *Chức năng:* Sinh vector embedding để tìm kiếm tương đồng trên Neo4j.
        *   *Thay đổi:* Ép cố định `provider = "gemini"` độc lập với cấu hình LLM_PROVIDER.
        *   *Lý do:* Giữ nguyên không gian vector của Neo4j DB (được xây dựng bằng Gemini embedding `gemini-embedding-001`). Điều này giúp tránh lệch khoảng cách cosine (cosine distance), đảm bảo kết quả tìm kiếm ngữ nghĩa chính xác 100%.
    3.  **Hàm `get_db_connection`:**
        *   *Chức năng:* Kết nối tới cơ sở dữ liệu lưu trữ bộ nhớ dài hạn (Personal Memory).
        *   *Thay đổi:* 
            *   Sửa lỗi TypeError khi dùng SQLite URI với SQLAlchemy engine (bỏ `pool_size` và `max_overflow`).
            *   Bổ sung cơ chế tự động Fallback sang SQLite cục bộ (`sqlite:///tic_personal_memory.db`) nếu tất cả kết nối PostgreSQL và MySQL đều thất bại (Connection refused).

### 1.3. Sửa đổi trong `app/server.py`
*   **File sửa đổi:** [server.py](file:///c:/Users/Admin/Desktop/TIC_Project/temp/agent/app/server.py)
*   **Chi tiết sửa đổi:** Chuyển đổi các thông báo in ra terminal (stdout `print`) từ tiếng Việt có dấu và Emoji sang tiếng Anh không dấu để tránh lỗi `UnicodeEncodeError` khi chạy trên môi trường Windows console (sử dụng encoding `cp1252`).

---

## 2. Kết Quả Kiểm Chứng (Verification)

Hệ thống đã được kiểm chứng thông qua các kịch bản chạy thử nghiệm độc lập:
1.  **Tự động chuyển đổi DB:** Khi PostgreSQL bị mất kết nối, hệ thống tự động in log và chuyển sang khởi tạo database SQLite `tic_personal_memory.db` cục bộ thành công.
2.  **Model Mapping:** Khởi tạo model adapter OpenAI `gpt-4o-mini` thành công từ yêu cầu gọi model Gemini, thực hiện sinh văn bản kiểm tra chính xác.
3.  **Embedding đồng nhất:** Đồ thị và tìm kiếm Neo4j vẫn sử dụng Gemini embedding cho kết quả chính xác cao (Score: ~0.86).
