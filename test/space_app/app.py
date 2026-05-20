import gradio as gr
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoImageProcessor, AutoModelForSequenceClassification, AutoModelForImageClassification, pipeline

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

print("Loading emotion tokenizer and model...")
emotion_model_name = "HalogenFlo/microsoft-deberta-v3-base-emotion-recognition"
emotion_tokenizer = AutoTokenizer.from_pretrained(emotion_model_name)
emotion_model = AutoModelForSequenceClassification.from_pretrained(emotion_model_name).to(device)
emotion_labels = ["sadness", "joy", "love", "anger", "fear", "surprise"]

def predict_emotion(text):
    inputs = emotion_tokenizer(text, padding=True, truncation=True, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = emotion_model(**inputs)
    pros = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]
    # pred = torch.argmax(pros, dim=-1)
    results = {emotion_labels[i]: float(pros[i]) for i in range(len(emotion_labels))} 
    return dict(sorted(results.items(), key=lambda item: item[1], reverse=True))

print("Loading vit processor and model...")
emnist_model_name = "HalogenFlo/vit-emnist-byclass"
process = AutoImageProcessor(emnist_model_name)
emnist_model = AutoModelForImageClassification.from_pretrained(emnist_model_name).to(device)



print("Loading llm processor and model...")
emnist_model_name = "HalogenFlo/qwen-2.5b-finetuned-qlora"