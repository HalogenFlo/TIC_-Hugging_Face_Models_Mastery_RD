# -*- coding: utf-8 -*-
# Chức năng: Kịch bản kiểm thử tích hợp xác minh hoạt động của 3 Sub-Agents ở Tầng 2.

import sys
import os
sys.path.append(r"c:\Users\Admin\Desktop\TIC_Project\temp\agent")
sys.stdout.reconfigure(encoding='utf-8')

from config import close_all_connections, DEFAULT_PROVIDER
from agents.chitchat import ChitchatAgent
from agents.query_reform import QueryReformAgent
from agents.law_tax import TaxLawAgent

def test_chitchat_agent():
    print("\n=== 1. KIỂM THỬ CHITCHAT AGENT ===")
    agent = ChitchatAgent(provider=DEFAULT_PROVIDER)
    
    # Giả lập state chứa câu hỏi chitchat ngoài lề
    state = {
        "raw_query": "Xin chào trợ lý, thời tiết hôm nay ở Hà Nội thế nào?",
        "messages": []
    }
    
    print(f"Câu hỏi thô: '{state['raw_query']}'")
    result = agent.run(state)
    print("Kết quả đầu ra của ChitchatAgent:")
    print(f"  - Phản hồi: {result.get('response')}")

def test_query_reform_agent():
    print("\n=== 2. KIỂM THỬ QUERY REFORM AGENT ===")
    agent = QueryReformAgent(provider=DEFAULT_PROVIDER)
    
    # Giả lập state câu hỏi viết tắt, sai lỗi chính tả
    state = {
        "raw_query": "thue tndn theo tt 103 dong bao nhieu",
        "messages": []
    }
    
    print(f"Câu hỏi gốc: '{state['raw_query']}'")
    result = agent.run(state)
    print("Kết quả đầu ra của QueryReformAgent:")
    print(f"  - Câu hỏi đã chuẩn hóa: {result.get('refined_query')}")
    print(f"  - Thực thể phát hiện:   {result.get('detected_entities')}")
    print(f"  - Câu hỏi gốc trả về:   {result.get('original_query')}")
    print(f"  - Confidence:            {result.get('confidence')}")
    print(f"  - Missing info:          {result.get('missing_info')}")
    
    return result.get('refined_query')

def test_tax_law_agent(refined_query: str):
    print("\n=== 3. KIỂM THỬ TAX LAW AGENT ===")
    agent = TaxLawAgent(provider=DEFAULT_PROVIDER)
    
    # Giả lập state với câu hỏi đã được chuẩn hóa ở bước trước
    state = {
        "raw_query": "thue tndn theo tt 103 dong bao nhieu",
        "refined_query": refined_query,
        "messages": []
    }
    
    print(f"Câu hỏi đã chuẩn hóa sử dụng: '{refined_query}'")
    result = agent.run(state)
    print("Kết quả đầu ra của TaxLawAgent:")
    print(f"  - Câu trả lời nháp (draft_answer):")
    print(f"    {result.get('draft_answer')}")
    print(f"  - Trích dẫn (citations): {result.get('citations')}")
    print(f"  - Cần hỏi lại người dùng? (requires_clarification): {result.get('requires_clarification')}")
    print(f"  - Câu hỏi làm rõ (clarification_prompt): {result.get('clarification_prompt')}")

if __name__ == "__main__":
    try:
        # Chạy thử nghiệm tuần tự
        test_chitchat_agent()
        refined = test_query_reform_agent()
        test_tax_law_agent(refined)
    except Exception as e:
        print(f"\n❌ LỖI TRONG QUÁ TRÌNH KIỂM THỬ: {e}")
    finally:
        # Đóng tất cả kết nối Neo4j
        close_all_connections()
        print("\n--- Đóng toàn bộ kết nối DB thành công ---")
