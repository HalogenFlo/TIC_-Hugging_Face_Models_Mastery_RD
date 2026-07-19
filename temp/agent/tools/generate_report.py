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
    """Định dạng báo cáo dưới dạng tài liệu Markdown."""
    
    def format(self, data: Dict[str, Any]) -> str:
        query = data.get("query", "")
        summary = data.get("summary", "Không có tóm tắt.")
        details = data.get("details", [])
        conflicts = data.get("conflicts", [])
        citations = data.get("citations", [])
        
        md = []
        md.append(f"# BÁO CÁO TƯ VẤN PHÁP LUẬT VIỆT NAM\n")
        md.append(f"**Yêu cầu tư vấn:** {query}\n")
        md.append(f"## 1. Tóm tắt kết quả tư vấn\n")
        md.append(f"{summary}\n")
        
        md.append(f"## 2. Phân tích chi tiết theo Lĩnh vực\n")
        if not details:
            md.append("Không có phân tích chi tiết.\n")
        for item in details:
            domain = item.get("domain", "Chưa phân loại").upper()
            analysis = item.get("analysis", "Không có nội dung.")
            md.append(f"### Lĩnh vực: {domain}\n")
            md.append(f"{analysis}\n")
            
        md.append(f"## 3. Đánh giá xung đột & Hiệu lực pháp lý\n")
        if not conflicts:
            md.append("Không phát hiện xung đột hiệu lực văn bản trong phạm vi tra cứu.\n")
        else:
            for conflict in conflicts:
                md.append(f"- **Văn bản**: {conflict.get('doc_code', 'Không rõ')}\n")
                md.append(f"  - **Loại xung đột**: {conflict.get('type', 'Không rõ')}\n")
                md.append(f"  - **Chi tiết & Hướng xử lý**: {conflict.get('description', 'Không có chi tiết')}\n")
        md.append("")
        
        md.append(f"## 4. Danh mục Trích dẫn cơ sở pháp lý\n")
        if not citations:
            md.append("Không có trích dẫn nguồn.\n")
        else:
            for i, cite in enumerate(citations, 1):
                citation_name = cite.get("citation", cite.get("unit_id", "Trích dẫn"))
                text = cite.get("text", "Không có nội dung text.")
                md.append(f"{i}. **{citation_name}**:\n   > {text}\n")
                
        return "\n".join(md)

class HTMLFormatter(BaseReportFormatter):
    """Định dạng báo cáo dưới dạng trang tài liệu HTML5."""
    
    def format(self, data: Dict[str, Any]) -> str:
        query = data.get("query", "")
        summary = data.get("summary", "Không có tóm tắt.")
        details = data.get("details", [])
        conflicts = data.get("conflicts", [])
        citations = data.get("citations", [])
        
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html lang=\"vi\">")
        html.append("<head>")
        html.append("    <meta charset=\"UTF-8\">")
        html.append("    <title>Báo cáo Tư vấn Pháp luật</title>")
        html.append("    <style>")
        html.append("        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 40px auto; padding: 0 20px; }")
        html.append("        h1 { color: #1F4E79; border-bottom: 2px solid #1F4E79; padding-bottom: 10px; }")
        html.append("        h2 { color: #2E75B6; margin-top: 30px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }")
        html.append("        h3 { color: #5B9BD5; }")
        html.append("        .query-box { background-color: #f9f9f9; border-left: 5px solid #1F4E79; padding: 15px; margin-bottom: 20px; font-style: italic; }")
        html.append("        blockquote { background: #f1f1f1; border-left: 3px solid #ccc; margin: 1.5em 10px; padding: 0.5em 10px; }")
        html.append("        .conflict-item { margin-bottom: 10px; padding: 10px; background-color: #FFF2CC; border-left: 4px solid #D6B656; }")
        html.append("    </style>")
        html.append("</head>")
        html.append("<body>")
        
        html.append("    <h1>Báo cáo Tư vấn Pháp luật Việt Nam</h1>")
        html.append(f"    <div class=\"query-box\"><strong>Yêu cầu tư vấn:</strong> {query}</div>")
        
        html.append("    <h2>1. Tóm tắt kết quả tư vấn</h2>")
        html.append(f"    <p>{summary}</p>")
        
        html.append("    <h2>2. Phân tích chi tiết theo Lĩnh vực</h2>")
        if not details:
            html.append("    <p>Không có phân tích chi tiết.</p>")
        for item in details:
            domain = item.get("domain", "Chưa phân loại").upper()
            analysis = item.get("analysis", "Không có nội dung.")
            html.append(f"    <h3>Lĩnh vực: {domain}</h3>")
            html.append(f"    <p>{analysis.replace(chr(10), '<br>')}</p>")
            
        html.append("    <h2>3. Đánh giá xung đột & Hiệu lực pháp lý</h2>")
        if not conflicts:
            html.append("    <p>Không phát hiện xung đột hiệu lực văn bản trong phạm vi tra cứu.</p>")
        else:
            for conflict in conflicts:
                html.append("    <div class=\"conflict-item\">")
                html.append(f"        <strong>Văn bản:</strong> {conflict.get('doc_code', 'Không rõ')}<br>")
                html.append(f"        <strong>Loại xung đột:</strong> {conflict.get('type', 'Không rõ')}<br>")
                html.append(f"        <strong>Chi tiết & Hướng xử lý:</strong> {conflict.get('description', 'Không có chi tiết')}")
                html.append("    </div>")
                
        html.append("    <h2>4. Danh mục Trích dẫn cơ sở pháp lý</h2>")
        if not citations:
            html.append("    <p>Không có trích dẫn nguồn.</p>")
        else:
            html.append("    <ol>")
            for cite in citations:
                citation_name = cite.get("citation", cite.get("unit_id", "Trích dẫn"))
                text = cite.get("text", "Không có nội dung text.")
                html.append(f"        <li><strong>{citation_name}</strong>:<blockquote>{text}</blockquote></li>")
            html.append("    </ol>")
            
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
