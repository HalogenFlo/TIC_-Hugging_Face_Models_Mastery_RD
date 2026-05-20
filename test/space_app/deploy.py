# CHỨC NĂNG: Triển khai ứng dụng Gradio và tệp requirements.txt lên Hugging Face Spaces (HalogenFlo/TIC_Guide)
# LÝ DO TẠO: Khắc phục lỗi context Git lồng nhau và tự động hóa quy trình đẩy code thông qua huggingface_hub API.
# LINK TRÍCH DẪN: https://huggingface.co/docs/huggingface_hub/guides/upload

import os
from huggingface_hub import HfApi

def deploy():
    # Cấu hình các thông số
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise ValueError("Biến môi trường HF_TOKEN chưa được thiết lập. Vui lòng đặt: export HF_TOKEN='your_token'")
    repo_id = "HalogenFlo/TIC_Guide"
    
    print(f"Bắt đầu đẩy các tệp tin lên Space: {repo_id}...")
    
    api = HfApi(token=token)
    
    # Danh sách các file cần upload và path đích trên Space
    files_to_upload = {
        "test/space_app/app.py": "app.py",
        "test/space_app/requirements.txt": "requirements.txt"
    }
    
    for local_path, repo_path in files_to_upload.items():
        if os.path.exists(local_path):
            print(f"Đang tải lên {local_path} -> {repo_path}...")
            try:
                api.upload_file(
                    path_or_fileobj=local_path,
                    path_in_repo=repo_path,
                    repo_id=repo_id,
                    repo_type="space",
                    commit_message=f"Cập nhật {repo_path} bằng pip freeze"
                )
                print(f"Tải lên {repo_path} thành công!")
            except Exception as e:
                print(f"Lỗi khi tải lên {repo_path}: {e}")
        else:
            print(f"Cảnh báo: Không tìm thấy tệp {local_path}")
            
    print("Hoàn tất quá trình deploy lên Hugging Face Space!")

if __name__ == "__main__":
    deploy()
