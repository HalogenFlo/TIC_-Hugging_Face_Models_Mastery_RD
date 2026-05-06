import os
import torch
import numpy as np
import evaluate
from datasets import load_dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    TrainingArguments, 
    Trainer
)
from huggingface_hub import login
from dotenv import load_dotenv

# 1. Khởi tạo và Đăng nhập
load_dotenv()
hf_token = os.getenv("HUGFACE_TOKEN")
if hf_token:
    login(token=hf_token)
else:
    print("WARNING: HUGFACE_TOKEN not found in .env file.")

# 2. Xác định bài toán và dữ liệu
# Bài toán: Nhận diện cảm xúc (Emotion Recognition) với 7 nhãn cơ bản
print("Loading dataset: tridm/UIT-VSMEC...")
dataset = load_dataset("tridm/UIT-VSMEC")

# Danh sách 7 nhãn cảm xúc của VSMEC
labels = ['Other', 'Disgust', 'Enjoyment', 'Anger', 'Surprise', 'Sadness', 'Fear']
label2id = {label: i for i, label in enumerate(labels)}
id2label = {i: label for i, label in enumerate(labels)}

def preprocess_function(examples):
    # Chuyển đổi nhãn từ dạng chữ (Emotion) sang dạng số (label)
    examples["label"] = [label2id[l] for l in examples["Emotion"]]
    return examples

print("Mapping labels to IDs...")
dataset = dataset.map(preprocess_function, batched=True)

# 3. Tokenization và tiền xử lý
# Sử dụng FPTAI/vibert-base-cased - mô hình Encoder mạnh mẽ cho tiếng Việt
model_name = "FPTAI/vibert-base-cased"
print(f"Loading tokenizer: {model_name}")
tokenizer = AutoTokenizer.from_pretrained(model_name)

def tokenize_function(examples):
    return tokenizer(examples["Sentence"], padding="max_length", truncation=True, max_length=128)

print("Tokenizing dataset...")
tokenized_datasets = dataset.map(tokenize_function, batched=True)

# 4. Chọn mô hình pre-trained
print("Loading model...")
model = AutoModelForSequenceClassification.from_pretrained(
    model_name, 
    num_labels=len(labels),
    id2label=id2label,
    label2id=label2id
)

# Đảm bảo sử dụng GPU nếu có
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# 5. Các số liệu đánh giá (Metrics)
accuracy_metric = evaluate.load("accuracy")
f1_metric = evaluate.load("f1")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    acc = accuracy_metric.compute(predictions=predictions, references=labels)["accuracy"]
    f1 = f1_metric.compute(predictions=predictions, references=labels, average="macro")["f1"]
    return {"accuracy": acc, "f1": f1}

# 6. Training Arguments & Trainer
repo_name = "vibert-vsmec-emotion-recognition"

training_args = TrainingArguments(
    output_dir=repo_name,
    eval_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=3, # Huấn luyện 3 epoch để đạt kết quả tốt
    weight_decay=0.01,
    push_to_hub=True,
    logging_steps=10,
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="f1",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,
)

# 7. Fine-tuning
print("Bắt đầu huấn luyện...")
trainer.train()

# 8. Đẩy lên Hugging Face Hub (Lưu và chia sẻ)
print("Đẩy model lên Hugging Face Hub...")
trainer.push_to_hub()
print("Hoàn thành Bước 2 với tập dữ liệu UIT-VSMEC!")
