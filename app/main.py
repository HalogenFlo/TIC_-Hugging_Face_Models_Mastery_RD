import os
import torch
from fastapi import FastAPI, Request
from transformers import AutoModelForCausalLM, AutoTokenizer
from dotenv import load_dotenv
from peft import PeftModel
load_dotenv()
app =FastAPI()
MODEL_PATH = os.environ.get("AIP_STORAGE_URI") or os.environ.get("AIP_MODEL_DIR", "/workspace/model")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

BASE_MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME)

base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_NAME,
    torch_dtype=torch_dtype,
    low_cpu_mem_usage=True
).to(device)

model = PeftModel.from_pretrained(base_model, MODEL_PATH).to(device)

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/predict")
async def predict(request: Request):
    body = await request.json()
    instances = body.get("instances", body.get("instance", []))
    results = []

    for text in instances:
        input = tokenizer(text, return_tensors="pt").to(device)
        with torch.no_grad():
            output = model.generate(**input, max_length=2048)
            response = tokenizer.decode(output[0], skip_special_tokens=True)
        results.append(response)
    return {"predictions": results}
