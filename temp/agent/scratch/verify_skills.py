# Chức năng: Kịch bản kiểm thử tích hợp (Verify) các kỹ năng đã được xây dựng.

import os
import sys

# Thêm thư mục gốc của agent vào sys.path để python nhận diện import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from skills.search_retrieval import execute_search_retrieval
from skills.analysis import execute_deep_analysis
from skills.reporting import execute_reporting_and_validation
from config import close_all_connections

def test_search_retrieval():
    print("\n--- 1. Testing execute_search_retrieval ---")
    query = "thuế thu nhập doanh nghiệp"
    print(f"Query: '{query}'")
    try:
        results = execute_search_retrieval(query_text=query, limit=3)
        print(f"Tìm thấy {len(results)} kết quả.")
        for i, res in enumerate(results):
            print(f"\n[Kết quả {i+1}]:")
            print(f"  - Unit ID: {res.get('unit_id')}")
            print(f"  - Comp ID: {res.get('comp_id')}")
            print(f"  - Citation: {res.get('citation')}")
            print(f"  - Norm Number: {res.get('norm_number')}")
            print(f"  - Validity Status: {res.get('validity_status')}")
            print(f"  - Source: {res.get('source')}")
            print(f"  - Amended By Count: {len(res.get('amended_by', []))}")
            print(f"  - Terminated By Count: {len(res.get('terminated_by', []))}")
        return results
    except Exception as e:
        print(f"Lỗi khi chạy test_search_retrieval: {e}")
        return []

def test_deep_analysis(comp_id):
    print("\n--- 2. Testing execute_deep_analysis ---")
    print(f"Analyzing Component ID: '{comp_id}'")
    try:
        res = execute_deep_analysis(comp_id=comp_id)
        print("Thông tin văn bản gốc:")
        print(f"  - Code: {res.get('norm_context', {}).get('code')}")
        print(f"  - Type: {res.get('norm_context', {}).get('type')}")
        print("Chi tiết điều khoản:")
        print(f"  - Title: {res.get('component_details', {}).get('title')}")
        print(f"  - Citation: {res.get('component_details', {}).get('citation')}")
        print(f"Số lượng lịch sử sửa đổi (Modifications): {len(res.get('modifications', []))}")
        for i, mod in enumerate(res.get('modifications', [])[:3]):
            print(f"  Modification {i+1}: doc={mod.get('amending_doc')}, type={mod.get('action_type')}")
    except Exception as e:
        print(f"Lỗi khi chạy test_deep_analysis: {e}")

def test_reporting():
    print("\n--- 3. Testing execute_reporting_and_validation ---")
    # Giả lập câu trả lời nháp có chứa trích dẫn đúng định dạng [NormNumber - Citation]
    draft_answer = "Theo quy định tại [103/2014/TT-BTC - Điều 10], doanh nghiệp được khấu trừ thuế. Tuy nhiên cần lưu ý [65/2013/NĐ-CP - Điều 12] về các trường hợp loại trừ."
    raw_data = {
        "query": "thuế thu nhập doanh nghiệp",
        "details": [
            {"title": "Khấu trừ thuế", "content": "Chi tiết về việc khấu trừ thuế thu nhập doanh nghiệp."},
            {"title": "Loại trừ", "content": "Chi tiết các trường hợp loại trừ không được khấu trừ."}
        ],
        "conflicts": [
            {"type": "conflict", "description": "Mâu thuẫn nhỏ về hiệu lực giữa Nghị định 65 và Thông tư 103."}
        ]
    }
    
    try:
        # Gửi email giả lập (simulation)
        os.environ["SMTP_SIMULATION"] = "true"
        
        res = execute_reporting_and_validation(
            draft_answer=draft_answer,
            raw_data=raw_data,
            format_type="markdown",
            recipient_email="test_user@example.com"
        )
        
        print(f"Số lượng trích dẫn đã được xác thực: {len(res.get('verified_citations', []))}")
        for c in res.get('verified_citations', []):
            print(f"  - Trích dẫn: {c.get('raw_citation')} -> Exists: {c.get('exists')}, Valid: {c.get('valid')}")
        
        print("\nNội dung báo cáo tạo ra (Markdown - 200 ký tự đầu):")
        print(res.get("report_content", "")[:200] + "...")
        print(f"\nTrạng thái gửi Email: {res.get('email_status', {}).get('status')}")
    except Exception as e:
        print(f"Lỗi khi chạy test_reporting: {e}")

if __name__ == "__main__":
    try:
        # Chạy test retrieval
        results = test_search_retrieval()
        
        # Lấy một comp_id hợp lệ để chạy test phân tích
        comp_id = None
        if results:
            for r in results:
                if r.get("comp_id"):
                    comp_id = r.get("comp_id")
                    break
        
        # Nếu không có comp_id nào từ CSDL, dùng comp_id giả lập để test error-handling
        if not comp_id:
            comp_id = "127429__c59"
            print(f"\n[INFO] Không tìm thấy comp_id nào trong kết quả. Dùng comp_id mặc định: {comp_id}")
            
        test_deep_analysis(comp_id)
        
        # Chạy test reporting
        test_reporting()
    finally:
        # Đóng tất cả kết nối DB sau khi chạy xong
        close_all_connections()
        print("\n--- Đóng toàn bộ kết nối DB thành công ---")
