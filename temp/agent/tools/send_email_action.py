# Chức năng: Gửi email báo cáo kết quả tư vấn pháp lý cho người dùng qua giao thức SMTP.

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, Optional

# --- Cấu hình mặc định SMTP ---
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_email_action(
    recipient_email: str, 
    subject: str, 
    body_text: str, 
    attachment_path: Optional[str] = None
) -> Dict[str, Any]:
    """Gửi email chứa báo cáo tư vấn. Tự động chuyển sang chế độ giả lập nếu thiếu cấu hình SMTP."""
    
    # 1. Kiểm tra cấu hình môi trường
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("[WARNING] Thiếu cấu hình SMTP_USERNAME hoặc SMTP_PASSWORD trong file .env.")
        print(f"[SIMULATION] Giả lập gửi email thành công tới: {recipient_email}")
        print(f"[SIMULATION] Tiêu đề: {subject}")
        print(f"[SIMULATION] Đính kèm: {attachment_path}")
        return {
            "status": "simulated",
            "message": "Giả lập gửi email thành công (chế độ demo do thiếu cấu hình SMTP).",
            "recipient": recipient_email,
            "subject": subject,
            "attachment": attachment_path
        }
        
    # 2. Xây dựng cấu trúc Email
    msg = MIMEMultipart()
    msg['From'] = SMTP_USERNAME
    msg['To'] = recipient_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
    
    # 3. Đính kèm tệp tin nếu có
    if attachment_path and os.path.exists(attachment_path):
        try:
            filename = os.path.basename(attachment_path)
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}",
            )
            msg.attach(part)
        except Exception as e:
            print(f"[WARNING] Lỗi khi đính kèm file: {e}")
            
    # 4. Thực hiện gửi qua SMTP Server
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls() # Bảo mật TLS
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_USERNAME, recipient_email, msg.as_string())
        server.quit()
        
        return {
            "status": "sent",
            "message": f"Email đã được gửi thành công tới: {recipient_email}",
            "recipient": recipient_email,
            "subject": subject
        }
    except Exception as e:
        print(f"[ERROR] Gửi email thất bại: {e}")
        return {
            "status": "failed",
            "message": f"Gửi email thất bại: {str(e)}",
            "recipient": recipient_email,
            "subject": subject
        }
