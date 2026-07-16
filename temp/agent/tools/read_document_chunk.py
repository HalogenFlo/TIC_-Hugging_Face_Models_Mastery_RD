# Chức năng: Đọc và phân mảnh nội dung tệp tài liệu pháp lý (PDF, Word, Text) để tránh làm phình ngữ cảnh của LLM.

import os
from typing import Dict, Any

def read_text_file(file_path: str) -> str:
    """Đọc tệp tin văn bản thuần (.txt)."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def read_docx_file(file_path: str) -> str:
    """Đọc tệp tin Word (.docx)."""
    try:
        import docx
    except ImportError:
        raise ImportError(
            "Thư viện 'python-docx' chưa được cài đặt để đọc file Word. "
            "Vui lòng chạy lệnh: pip install python-docx"
        )
    
    doc = docx.Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)

def read_pdf_file(file_path: str) -> str:
    """Đọc tệp tin PDF (.pdf)."""
    try:
        import pypdf
    except ImportError:
        raise ImportError(
            "Thư viện 'pypdf' chưa được cài đặt để đọc file PDF. "
            "Vui lòng chạy lệnh: pip install pypdf"
        )
        
    reader = pypdf.PdfReader(file_path)
    full_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text.append(text)
    return "\n".join(full_text)

def read_document_chunk(file_path: str, chunk_index: int = 0, chunk_size: int = 2000) -> Dict[str, Any]:
    """Đọc và trích xuất một phân đoạn nội dung của tệp tài liệu dựa trên index."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy tệp tài liệu tại đường dẫn: {file_path}")
        
    ext = os.path.splitext(file_path)[1].lower()
    
    # 1. Trích xuất toàn bộ văn bản dựa trên định dạng
    if ext == ".txt":
        full_text = read_text_file(file_path)
    elif ext == ".docx":
        full_text = read_docx_file(file_path)
    elif ext == ".pdf":
        full_text = read_pdf_file(file_path)
    else:
        raise ValueError(f"Định dạng tệp '{ext}' không được hỗ trợ. Chỉ hỗ trợ .txt, .docx, và .pdf.")
        
    # 2. Phân đoạn văn bản (cắt theo độ dài ký tự)
    total_length = len(full_text)
    total_chunks = max(1, (total_length + chunk_size - 1) // chunk_size)
    
    # Đảm bảo index hợp lệ
    if chunk_index < 0:
        chunk_index = 0
    elif chunk_index >= total_chunks:
        chunk_index = total_chunks - 1
        
    start_pos = chunk_index * chunk_size
    end_pos = min(start_pos + chunk_size, total_length)
    
    chunk_text = full_text[start_pos:end_pos]
    
    return {
        "file_name": os.path.basename(file_path),
        "chunk_text": chunk_text,
        "chunk_index": chunk_index,
        "total_chunks": total_chunks,
        "total_characters": total_length
    }
