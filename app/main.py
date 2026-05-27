import os
import torch
from fastapi import FastAPI, Request
from transformers import AutoModelForCausalLM, AutoTokenizer

app =FastAPI()
GCS_URI = os.environ.get("GCS_URI", "gs://ticmastery/hf-ticmastery")
MODEL_PATH = GCS_URI.replace("gs://", "/gcs/") if GCS_URI.startswith("gs://") else "/workspace/model"

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True
).to("cuda")

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/predict")
async def predict(request: Request):
    body = await request.json()
    instances = body.get("instance", [])
    results = []

    for text in instances:
        input = tokenizer(text, return_tensors="pt").to("cuda")
        with torch.no_grad():
            output = model.generate(**input, max_length=2048)
            response = tokenizer.decode(output[0], skip_special_tokens=True)
        results.append(response)
    return {"predictions": results}
