# Báo Cáo Tiến Độ Dự Án TIC - Hugging Face Mastery

## Cập nhật ngày: 2026-05-06
## Trạng thái: **Bước 1 - HOÀN THÀNH**

---

### Các công việc đã thực hiện trong Bước 1:
1.  **Thiết lập môi trường:** Khởi tạo Python venv và cấu hình biến môi trường.
2.  **Cài đặt thư viện:** Hoàn thành cài đặt bộ công cụ SOTA cho LLM.
3.  **Hệ thống hóa kiến thức:** Hiểu rõ vai trò của các thư viện Tokenization(biến text -> token -> chuyển thành số) và Serialization(lưu model xuống đĩa và load lên)

---

### Danh sách thư viện đã cài đặt & Lý do kỹ thuật

| Thư viện | Vai trò / Lý do cài đặt | Tầm quan trọng đối với Tiếng Việt |
| :--- | :--- | :--- |
| **`transformers`** | Thư viện lõi của Hugging Face để tải và chạy các mô hình (BERT, Llama, Qwen...). | Chứa các kiến trúc pre-trained tối ưu cho tiếng Việt, có thể dùng để fine-turning trên dataset tiếng Việt. |
| **`datasets`** | Quản lý, tải và tiền xử lý dữ liệu huấn luyện quy mô lớn. | Hỗ trợ xử lý các tập dữ liệu tiếng Việt (như PhoBERT data) hiệu quả. |
| **`tokenizers`** | Bộ chia từ (tokenization) hiệu năng cao viết bằng Rust. | Xử lý dấu tiếng Việt và âm tiết với tốc độ cực nhanh. |
| **`accelerate`** | Tối ưu hóa việc huấn luyện trên GPU/TPU và hỗ trợ Distributed Training. | Cần thiết khi huấn luyện các mô hình LLM lớn. |
| **`peft`** | Hỗ trợ các kỹ thuật Fine-tuning hiệu quả (LoRA, DoRA, Prefix Tuning). | Giúp giảm chi phí phần cứng khi tinh chỉnh mô hình cho doanh nghiệp. |
| **`bitsandbytes`** | Hỗ trợ Quantization (8-bit, 4-bit) để giảm bộ nhớ VRAM. | Cho phép chạy/huấn luyện LLM trên các dòng GPU phổ thông (12GB-16GB). |
| **`sentencepiece`** | Engine chia từ dựa trên subword, bắt buộc cho các dòng Llama, Mistral, T5. | Giúp đọc các file `.model` chứa quy tắc ngôn ngữ của các mô hình SOTA. |
| **`protobuf`** | Chuẩn hóa việc đọc/ghi dữ liệu cấu hình và model tokenizer. | Là điều kiện cần để thư viện SentencePiece hoạt động ổn định. |
| **`unsloth`** | Công cụ tối ưu hóa huấn luyện LLM nhanh hơn 2-5 lần và tiết kiệm 70% VRAM. | **Key SOTA** của dự án để đạt hiệu suất cao nhất. |
| **`google-cloud-aiplatform`** | SDK để tương tác với Google Vertex AI. | Phục vụ cho việc triển khai mô hình lên môi trường Production (Bước 12). |

---

### Kế hoạch tiếp theo: **Bước 2**
*   **Thực hiện quy trình Machine Learning tiêu chuẩn:**
    *   Xác định bài toán và dữ liệu
    *   Tokenization và tiền xử lý dữ liệu
    *   Chọn mô hình pre-trained
    *   Fine-tuning
    *   Tăng tốc và tối ưu hóa
    *   Đánh giá mô hình
    *   Triển khai mô hình
    *   Lưu và chia sẻ model
*   **So sánh ML, DL và LLM:**
    *   **ML:** Đơn giản, dùng các thuật toán truyền thống, dữ liệu dạng bảng có cấu trúc hoặc không cấu trúc, chạy trên CPU, huấn luyện từ đầu.
    *   **DL:** Dùng các mô hình Deep Learning mạng thần kinh đa lớp, dữ liệu nhiều dạng (hình ảnh, video, âm thanh, văn bản) chạy trên GPU, có thể huấn luyện từ đầu hoặc dùng kiến trúc pre-trained để fine-tuning.
    *   **LLM:** Dùng các mô hình Large Language Models, dữ liệu văn bản khổng lồ chạy trên GPU, dùng kiến trúc pre-trained để fine-tuning.
*   **Các số liệu đánh giá:**
    *   **Phân loại văn bản:** accuracy, f1-score, precision, recall
    *   **Dịch máy:** BLEU, METEOR
    *   **Tóm tắt văn bản:** ROUGE-1, ROUGE-2, ROUGE-L
    *   **Sinh văn bản:** Perplexity, BLEU, BERTScore
    *   **Đối thoại (Chatbot):** Human Evaluation (Fluency, Relevance, Coherence)
*   Tải tập dữ liệu tiếng Việt: **Sử dụng `tridm/UIT-VSMEC` (Nhận diện cảm xúc 7 nhãn - Emotion Recognition).**
    *   Tạo mối quan hệ giữa labels và id
    *   Chuẩn hóa nhãn thành id
    *   Tải tokenizer và mô hình `FPTAI/vibert-base-cased`
*   Huấn luyện một bộ phân loại văn bản (Text Classifier) đơn giản: **Đã tạo mã nguồn `TIC_Mastery.ipynb` sử dụng mô hình `FPTAI/vibert-base-cased` kết hợp thư viện Trainer API để phân loại 7 loại cảm xúc.**
    *   Chọn các chit số đánh giá accuracy và f1-score
    *   Chọn số epoch là 5 và batch size là 16
    *   Huấn luyện mô hình
    *   Đánh giá mô hình
    *   Lưu và chia sẻ model

---
*Báo cáo này được tự động cập nhật để theo dõi lộ trình làm chủ Hugging Face.*
