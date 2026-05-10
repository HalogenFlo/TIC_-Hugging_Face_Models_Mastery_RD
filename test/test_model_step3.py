# python test/use_model_step3.py --image duong_dan_anh.png
import argparse
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

def load_model(model_path="vit-emnist-byclass"):
    print(f"Loading from: {model_path}")
    processor = AutoImageProcessor.from_pretrained(model_path)
    model = AutoModelForImageClassification.from_pretrained(model_path)
    model.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    return processor, model, device

def predict(image_path, processor, model, device):
    image = Image.open(image_path).convert("RGB").resize((224, 224))
    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    probs = torch.nn.functional.softmax(logits, dim=-1)
    pred_class_id = torch.argmax(probs, dim=-1).item()
    confidence = probs[0, pred_class_id].item()
    id2label = model.config.id2label
    pred_label = id2label.get(pred_class_id, f"Class {pred_class_id}")
    return pred_class_id, pred_label, confidence

def main():
    parser = argparse.ArgumentParser(description="Dự đoán ảnh EMNIST với ViT đã huấn luyện")
    parser.add_argument("--model_path", default="vit-emnist-byclass",
                        help="Repo Hub hoặc đường dẫn local (mặc định: vit-emnist-byclass)")
    parser.add_argument("--image", "-i", type=str, help="Đường dẫn ảnh muốn dự đoán")
    args = parser.parse_args()

    processor, model, device = load_model(args.model_path)

    if args.image:
        images = [args.image]
    else:
        print("Chế độ tương tác. Nhập đường dẫn ảnh, Enter để dừng.")
        images = []
        while True:
            img = input("Ảnh: ").strip()
            if not img:
                break
            images.append(img)

    for img_path in images:
        cls_id, label, conf = predict(img_path, processor, model, device)
        print(f"Ảnh: {img_path}")
        print(f"  → Lớp dự đoán: {label} (ID {cls_id})")
        print(f"  → Độ tin cậy: {conf:.4f}")
        print("-" * 40)

if __name__ == "__main__":
    main()