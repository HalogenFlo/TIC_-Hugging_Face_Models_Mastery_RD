# Chức năng: Kỹ năng Đóng gói Báo cáo & Kiểm chứng (Reporting & Action Execution Skill).

from typing import Dict, Any, Optional
from tools.validate_citations import validate_citations
from tools.generate_report import generate_report
from tools.send_email_action import send_email_action
from config import DEFAULT_PROVIDER

def execute_reporting_and_validation(
    draft_answer: str,
    raw_data: Dict[str, Any],
    provider: str = DEFAULT_PROVIDER,
    format_type: str = "markdown",
    recipient_email: Optional[str] = None,
    email_subject: Optional[str] = None
) -> Dict[str, Any]:
    """Kiểm chứng trích dẫn của câu trả lời nháp, xuất báo cáo và thực hiện gửi email hành động nếu được yêu cầu."""
    result = {
        "verified_citations": [],
        "report_content": None,
        "email_status": None,
        "error": None
    }
    
    try:
        # 1. Đối chiếu trích dẫn nguồn chống ảo tưởng (validate citations)
        citations_check = validate_citations(draft_answer, provider=provider)
        result["verified_citations"] = citations_check
        
        # 2. Chuẩn bị dữ liệu để xuất báo cáo
        # Dữ liệu truyền vào generate_report gồm: query, summary, details, conflicts, citations
        report_data = {
            "query": raw_data.get("query", "Yêu cầu tư vấn pháp luật"),
            "summary": draft_answer, # Tóm tắt chính là nội dung nháp đã có
            "details": raw_data.get("details", []),
            "conflicts": raw_data.get("conflicts", []),
            "citations": citations_check
        }
        
        # 3. Kích hoạt định dạng báo cáo (generate_report)
        report_content = generate_report(report_data, format_type=format_type)
        
        # 3.1. Tự động xuất file báo cáo vật lý cho người dùng tải về máy nếu có yêu cầu
        query_lower = raw_data.get("query", "").lower()
        if any(k in query_lower for k in ["báo cáo", "pdf", "tải", "xuất"]):
            import os
            import time
            exports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "exports")
            os.makedirs(exports_dir, exist_ok=True)
            filename = f"bao_cao_phap_ly_{int(time.time())}.html"
            filepath = os.path.join(exports_dir, filename)
            
            html_report = generate_report(report_data, format_type="html")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_report)
                
            download_link = f"\n\n---\n<a href='/exports/{filename}' target='_blank' style='display: inline-block; padding: 10px 20px; background-color: #2563eb; color: white !important; font-weight: 600; border-radius: 6px; text-decoration: none; margin-top: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.15); transition: all 0.2s;'>📥 Nhấn vào đây để Xuất & Tải File Báo Cáo PDF (Mở Tab Mới)</a>"
            report_content = report_content + download_link
            
        result["report_content"] = report_content
        
        # 4. Gửi SMTP email nếu được cung cấp recipient_email
        if recipient_email:
            subject = email_subject or f"Báo cáo Tư vấn Pháp luật: {raw_data.get('query', '')[:30]}..."
            email_res = send_email_action(
                recipient_email=recipient_email,
                subject=subject,
                body_text=f"Kính gửi Quý khách,\n\nDưới đây là báo cáo tư vấn pháp luật chi tiết của quý khách.\n\n{draft_answer}\n\nTrân trọng,\nLegalMAS System.",
                # Tạm thời chưa đính kèm file do chưa lưu báo cáo thành file vật lý
            )
            result["email_status"] = email_res
            
        return result
        
    except Exception as e:
        print(f"[ERROR] execute_reporting_and_validation failed: {e}")
        result["error"] = str(e)
        return result
