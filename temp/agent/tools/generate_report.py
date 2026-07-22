# Chức năng: Định nghĩa Strategy Pattern để xuất bản báo cáo tư vấn pháp lý dưới nhiều định dạng (Markdown, HTML).

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseReportFormatter(ABC):
    """Lớp cơ sở trừu tượng (Interface) định nghĩa cơ chế format báo cáo."""
    
    @abstractmethod
    def format(self, data: Dict[str, Any]) -> str:
        """Định dạng dữ liệu báo cáo thành chuỗi kết quả."""
        pass

class MarkdownFormatter(BaseReportFormatter):
    """Định dạng câu trả lời ngắn gọn, đi thẳng vào trọng tâm cần thiết + Nguồn trích dẫn."""
    
    def format(self, data: Dict[str, Any]) -> str:
        summary = data.get("summary", "Không có nội dung câu trả lời.")
        citations = data.get("citations", [])
        
        md = []
        md.append(f"{summary}\n")
        
        if citations:
            md.append("\n📌 **Nguồn trích dẫn cơ sở pháp lý:**")
            for i, cite in enumerate(citations, 1):
                citation_name = cite.get("raw_citation", "Trích dẫn")
                text = cite.get("correct_text")
                if text and str(text).strip() and str(text).strip() != "None":
                    md.append(f"{i}. **{citation_name}**:\n   > {text}")
                else:
                    md.append(f"{i}. **{citation_name}**")
                
        return "\n".join(md)

import re

def convert_markdown_to_html(md_text: str) -> str:
    """Chuyển đổi chuỗi Markdown (Bảng biểu, Tiêu đề, In đậm, Danh sách) sang HTML5 chuẩn."""
    try:
        import markdown
        return markdown.markdown(md_text, extensions=['tables', 'fenced_code'])
    except Exception:
        lines = md_text.split('\n')
        html_lines = []
        in_table = False
        table_rows = []
        
        for line in lines:
            stripped = line.strip()
            # Xử lý Bảng Markdown | col1 | col2 |
            if stripped.startswith('|') and stripped.endswith('|'):
                if '---' in stripped or ':--' in stripped:
                    continue
                cells = [c.strip() for c in stripped.split('|')[1:-1]]
                if not in_table:
                    in_table = True
                    table_rows.append('<thead><tr>' + ''.join(f'<th>{c}</th>' for c in cells) + '</tr></thead><tbody>')
                else:
                    table_rows.append('<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>')
                continue
            elif in_table:
                in_table = False
                table_rows.append('</tbody>')
                html_lines.append('<table class="legal-table">' + ''.join(table_rows) + '</table>')
                table_rows = []
                
            # Xử lý Tiêu đề #, ##, ###
            if stripped.startswith('# '):
                html_lines.append(f'<h2 style="color:#1e3a8a; border-bottom:1px solid #e2e8f0; padding-bottom:6px; margin-top:25px;">{stripped[2:]}</h2>')
            elif stripped.startswith('## '):
                html_lines.append(f'<h3 style="color:#1e3a8a; margin-top:20px;">{stripped[3:]}</h3>')
            elif stripped.startswith('### '):
                html_lines.append(f'<h4 style="color:#334155; margin-top:15px;">{stripped[4:]}</h4>')
            elif stripped.startswith('- ') or stripped.startswith('* '):
                html_lines.append(f'<li style="margin-left: 20px;">{stripped[2:]}</li>')
            elif stripped:
                html_lines.append(f'<p>{stripped}</p>')
                
        if in_table:
            table_rows.append('</tbody>')
            html_lines.append('<table class="legal-table">' + ''.join(table_rows) + '</table>')
            
        res = '\n'.join(html_lines)
        res = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', res)
        return res

class HTMLFormatter(BaseReportFormatter):
    """Định dạng báo cáo HTML5 chuẩn A4 văn phòng, hỗ trợ xuất/in thành file PDF sắc nét."""
    
    def format(self, data: Dict[str, Any]) -> str:
        query = data.get("query", "")
        summary = data.get("summary", "Không có tóm tắt.")
        details = data.get("details", [])
        citations = data.get("citations", [])
        
        summary_html = convert_markdown_to_html(summary)
        
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html lang=\"vi\">")
        html.append("<head>")
        html.append("    <meta charset=\"UTF-8\">")
        html.append("    <title>Báo cáo Tư vấn Pháp luật - LegalMAS</title>")
        html.append("    <style>")
        html.append("        @page { size: A4; margin: 15mm; }")
        html.append("        body { font-family: 'Segoe UI', 'Roboto', Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 850px; margin: 0 auto; padding: 20px; background: #f8fafc; }")
        html.append("        .print-bar { background: #0f172a; color: white; padding: 12px 24px; display: flex; justify: space-between; align-items: center; border-radius: 8px; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }")
        html.append("        .btn-print { background: #2563eb; color: white; border: none; padding: 10px 20px; font-weight: 600; border-radius: 6px; cursor: pointer; transition: all 0.2s; font-size: 14px; display: flex; align-items: center; gap: 8px; }")
        html.append("        .btn-print:hover { background: #1d4ed8; transform: translateY(-1px); }")
        html.append("        .report-paper { background: white; padding: 50px; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; }")
        html.append("        .legal-header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #0f172a; padding-bottom: 20px; }")
        html.append("        .national-title { font-weight: 700; font-size: 13px; letter-spacing: 1px; text-transform: uppercase; color: #334155; margin-bottom: 4px; }")
        html.append("        .motto { font-size: 12px; font-weight: 600; color: #475569; margin-bottom: 15px; }")
        html.append("        .report-title { color: #1e3a8a; font-size: 22px; font-weight: 800; margin-top: 15px; letter-spacing: 0.5px; text-transform: uppercase; }")
        html.append("        .query-box { background: #f0f9ff; border-left: 4px solid #0284c7; padding: 14px 18px; margin: 25px 0; border-radius: 0 8px 8px 0; color: #0369a1; font-style: italic; font-size: 14.5px; }")
        html.append("        .content-body { font-size: 15px; color: #334155; line-height: 1.7; text-align: justify; }")
        html.append("        .legal-table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; }")
        html.append("        .legal-table th, .legal-table td { border: 1px solid #cbd5e1; padding: 10px 14px; text-align: left; }")
        html.append("        .legal-table th { background-color: #f1f5f9; color: #1e293b; font-weight: 700; }")
        html.append("        .legal-table tr:nth-child(even) { background-color: #f8fafc; }")
        html.append("        .citation-section { margin-top: 35px; padding-top: 20px; border-top: 1px solid #e2e8f0; }")
        html.append("        .citation-title { color: #1e3a8a; font-size: 16px; font-weight: 700; margin-bottom: 12px; display: flex; align-items: center; gap: 6px; }")
        html.append("        blockquote { background: #f8fafc; border-left: 3px solid #64748b; margin: 8px 0; padding: 8px 14px; color: #475569; font-size: 14px; }")
        html.append("        .footer-note { text-align: center; margin-top: 40px; font-size: 12px; color: #94a3b8; border-top: 1px dashed #cbd5e1; padding-top: 15px; }")
        html.append("        @media print { .print-bar { display: none !important; } body { background: white; padding: 0; } .report-paper { box-shadow: none; border: none; padding: 0; } }")
        html.append("    </style>")
        html.append("</head>")
        html.append("<body>")
        
        html.append("    <div class=\"print-bar\">")
        html.append("        <span>📄 <strong>Hệ Thống Trợ Lý Tư Vấn Pháp Luật Đa Tác Nhân (LegalMAS)</strong></span>")
        html.append("        <button onclick=\"window.print()\" class=\"btn-print\">🖨️ Tải Xuống / Lưu Thành File PDF</button>")
        html.append("    </div>")
        
        html.append("    <div class=\"report-paper\">")
        html.append("        <div class=\"legal-header\">")
        html.append("            <div class=\"national-title\">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</div>")
        html.append("            <div class=\"motto\">Độc lập - Tự do - Hạnh phúc</div>")
        html.append("            <div style=\"width: 120px; height: 1px; background: #94a3b8; margin: 0 auto 15px auto;\"></div>")
        html.append("            <h1 class=\"report-title\">BÁO CÁO TƯ VẤN PHÁP LUẬT CHUYÊN SÂU</h1>")
        html.append("        </div>")
        
        html.append(f"        <div class=\"query-box\"><strong>Nội dung câu hỏi tư vấn:</strong> {query}</div>")
        
        html.append("        <div class=\"content-body\">")
        html.append(f"            {summary_html}")
        html.append("        </div>")
        
        if citations:
            html.append("        <div class=\"citation-section\">")
            html.append("            <div class=\"citation-title\">📌 Danh Mục Cơ Sở Pháp Lý Trích Dẫn Chuẩn</div>")
            html.append("            <ol style=\"padding-left: 20px;\">")
            for cite in citations:
                citation_name = cite.get("raw_citation", "Trích dẫn")
                text = cite.get("correct_text")
                if text and str(text).strip() and str(text).strip() != "None":
                    html.append(f"                <li><strong>{citation_name}</strong>:<blockquote>{text}</blockquote></li>")
                else:
                    html.append(f"                <li><strong>{citation_name}</strong></li>")
            html.append("            </ol>")
            html.append("        </div>")
            
        html.append("        <div class=\"footer-note\">Báo cáo được xuất tự động bởi Hệ thống LegalMAS. Căn cứ pháp lý đã qua xác thực đối chiếu CSDL.</div>")
        html.append("    </div>")
        
        html.append("    <script>")
        html.append("        // Tự động bật ngay cửa sổ lưu/in PDF khi mở trang")
        html.append("        window.addEventListener('load', function() {")
        html.append("            setTimeout(function() { window.print(); }, 500);")
        html.append("        });")
        html.append("    </script>")
        html.append("</body>")
        html.append("</html>")
        
        return "\n".join(html)

class PDFFormatter(BaseReportFormatter):
    """Định dạng báo cáo dưới dạng tài liệu PDF (Sẽ phát triển ở phần sau)."""
    
    def format(self, data: Dict[str, Any]) -> str:
        raise NotImplementedError("PDFFormatter sẽ được triển khai ở Phần 2.")

class ExcelFormatter(BaseReportFormatter):
    """Định dạng báo cáo dưới dạng bảng Excel (Sẽ phát triển ở phần sau)."""
    
    def format(self, data: Dict[str, Any]) -> str:
        raise NotImplementedError("ExcelFormatter sẽ được triển khai ở Phần 2.")

def generate_report(data: Dict[str, Any], format_type: str = "markdown") -> str:
    """Hàm wrapper xuất bản báo cáo theo định dạng yêu cầu."""
    format_type = format_type.lower()
    
    formatters: Dict[str, BaseReportFormatter] = {
        "markdown": MarkdownFormatter(),
        "md": MarkdownFormatter(),
        "html": HTMLFormatter(),
    }
    
    formatter = formatters.get(format_type)
    if not formatter:
        raise ValueError("Không hỗ trợ định dạng báo cáo: {0}. Hiện chỉ hỗ trợ: markdown, md, html.".format(format_type))
        
    return formatter.format(data)
