# Danh Sách Dataset Tiếng Việt Cho Lộ Trình Hugging Face Mastery (TIC Project)

Dựa trên yêu cầu từ `REQUIREMENTS.md` và hướng dẫn R&D của dự án TIC, dưới đây là các tập dữ liệu (dataset) tiếng Việt được đề xuất để thực hiện lộ trình 12 bước, đảm bảo tối ưu cho các công nghệ SOTA như Unsloth, LoRA/DoRA và Alignment (DPO/ORPO).

## 1. Giai đoạn Cơ bản & Deep Learning (Bước 2 & 3)

Mục tiêu: Làm quen với Trainer API, Tokenization và các bài toán phân loại cơ bản.

| Task | Dataset Đề Xuất | Mô Tả | Link HF |
| :--- | :--- | :--- | :--- |
| **Text Classification** | `uitnlp/vihsd` | Dataset phát hiện ngôn ngữ thù ghét (Hate Speech) với ~33k mẫu. Rất tốt để thực hành Classification. | [Link](https://huggingface.co/datasets/uitnlp/vihsd) |
| **Sentiment Analysis** | `uitnlp/visfc` | Phân tích cảm xúc sinh viên (Vietnamese Student Feedback Corpus). | [Link](https://huggingface.co/datasets/uitnlp/visfc) |
| **Emotion Recognition** | `tridm/UIT-VSMEC` | Nhận diện 7 loại cảm xúc cơ bản từ bình luận mạng xã hội. | [Link](https://huggingface.co/datasets/tridm/UIT-VSMEC) |
| **Fine-grained Emotion** | `uitnlp/vigoemotions` | Nhận diện cảm xúc chi tiết với 27 nhãn (Multi-label). | [Link](https://huggingface.co/datasets/uitnlp/vigoemotions) |
| **NER (Named Entity Recognition)** | `NNDK/vlsp-2016-ner-dataset` | Dataset chuẩn từ cuộc thi VLSP cho bài toán nhận dạng thực thể có tên. | [Link](https://huggingface.co/datasets/NNDK/vlsp-2016-ner-dataset) |
| **Image Classification** | `uitnlp/vietnamese-food-classification` | Phân loại các món ăn Việt Nam (Phở, Bánh mì, v.v.), phù hợp cho Bước 3 về Computer Vision. | [Link](https://huggingface.co/datasets/uitnlp/vietnamese-food-classification) |

## 2. Giai đoạn Instruction Tuning (Bước 5, 6 & 7)

Mục tiêu: Fine-tune LLM (Llama 3.2, Qwen 2.5) bằng Unsloth và LoRA/DoRA. Cần các bộ dữ liệu Instruction chất lượng cao.

| Dataset | Số lượng | Đặc điểm | Link HF |
| :--- | :--- | :--- | :--- |
| **saillab/alpaca_vietnamese_taco** | 52k+ | Bản dịch tiếng Việt của Stanford Alpaca, phổ biến và ổn định cho SFT cơ bản. | [Link](https://huggingface.co/datasets/saillab/alpaca_vietnamese_taco) |
| **5CD-AI/Vietnamese-alpaca-gpt4** | 52k | Dữ liệu Instruction được sinh bởi GPT-4 và dịch sang tiếng Việt, chất lượng phản hồi cao hơn Alpaca gốc. | [Link](https://huggingface.co/datasets/5CD-AI/Vietnamese-alpaca-gpt4-gg-translated) |
| **5CD-AI/Vietnamese-OpenGVLab-ShareGPT-4o** | Lớn | Dữ liệu hội thoại đa lượt (multi-turn), phù hợp để huấn luyện Chatbot ở Bước 9. | [Link](https://huggingface.co/datasets/5CD-AI/Vietnamese-OpenGVLab-ShareGPT-4o-gg-translated) |

## 3. Giai đoạn Alignment & Frontier LLMs (Bước 10)

Mục tiêu: Căn chỉnh mô hình theo sở thích con người bằng DPO (Direct Preference Optimization) hoặc ORPO.

| Dataset | Loại | Mô Tả | Link HF |
| :--- | :--- | :--- | :--- |
| **5CD-AI/Vietnamese-Intel-orca_dpo_pairs** | DPO Pairs | Bao gồm các cặp câu trả lời (Chosen vs Rejected) bằng tiếng Việt. Cần thiết cho kỹ thuật DPO/ORPO. | [Link](https://huggingface.co/datasets/5CD-AI/Vietnamese-Intel-orca_dpo_pairs-gg-translated) |
| **522H0134-NguyenNhatHuy/vietnamese-dpo-10k** | DPO Pairs | 10,000 cặp dữ liệu preference đã được lọc và chuẩn hóa cho tiếng Việt. | [Link](https://huggingface.co/datasets/522H0134-NguyenNhatHuy/vietnamese-dpo-10k) |

## 4. Đặc thù cho Chatbot Thương mại Điện tử (Ecommerce Chatbot)

Để xây dựng một chatbot cho công ty thương mại điện tử chuyên nghiệp, bạn cần tập trung vào các dataset chuyên biệt dưới đây:

| Dataset | Nguồn / Sàn | Mục đích | Mô Tả |
| :--- | :--- | :--- | :--- |
| **5CD-AI/Vietnamese-Ecommerce-Alpaca** | **Synthetic** (VN Context) | **SFT (Lệnh bán hàng)** | Dữ liệu mô phỏng chất lượng cao về tư vấn sản phẩm, so sánh giá, và đổi trả. |
| **5CD-AI/Vietnamese-Ecommerce-Multi-turn-Chat** | **Tiki** / Sendo | **Chatbot (Đa lượt)** | Dữ liệu thực tế từ Tiki giúp mô hình giữ ngữ cảnh hội thoại (ví dụ: hỏi giá sau khi hỏi size). |
| **ura-hcmut/Vietnamese-Customer-Support-QA** | **DooPage** (FB/Zalo) | **Hỗ trợ khách hàng** | 100% dữ liệu thực tế từ các shop online đa kênh, rất sát với ngôn ngữ khách hàng Việt. |
| **sailor2/Vietnamese_RAG** | Chung (Benchmark) | **RAG (Tra cứu)** | Dùng để huấn luyện mô hình khả năng trả lời dựa trên tài liệu (Catalogue sản phẩm). |

## 🚀 Quy trình triển khai Chatbot Ecommerce (Theo Roadmap)

1.  **Bước 5-7 (Huấn luyện):** Fine-tune mô hình **Qwen2.5-7B** hoặc **Llama-3.2-3B** bằng **Unsloth** với dataset `Vietnamese-Ecommerce-Alpaca`. Sử dụng LoRA/DoRA để mô hình "thông minh" hơn trong việc tư vấn.
2.  **Bước 9 (Xây dựng Demo):** Sử dụng Gradio kết hợp với dataset `Multi-turn-Chat` để tạo giao diện Chatbot thử nghiệm.
3.  **Bước 10 (Căn chỉnh):** Dùng DPO với dataset `vietnamese-dpo-10k` để đảm bảo Chatbot luôn phản hồi lịch sự, không dùng từ ngữ tiêu cực (Safety Alignment).
4.  **Bước 12 (Production):** Triển khai hệ thống **RAG**. Khi khách hỏi về sản phẩm cụ thể, Chatbot sẽ tra cứu Database/PDF của công ty qua một hệ thống Vector Database (như Pinecone hoặc Vertex AI Search) rồi mới trả lời.

> [!IMPORTANT]
> Với Chatbot TMĐT, **RAG** là yếu tố sống còn vì dữ liệu sản phẩm thay đổi liên tục. Không nên chỉ dựa vào kiến thức trong mô hình (Parametric Knowledge).
