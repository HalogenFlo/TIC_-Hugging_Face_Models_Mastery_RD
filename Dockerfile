FROM python:3.10-slim

WORKDIR /workspace

COPY ./app /workspace/app

RUN pip install --no-cache-dir torch fastapi uvicorn transformers google-cloud-aiplatform huggingface_hub peft

RUN python3 -c "from transformers import AutoModelForCausalLM, AutoTokenizer; AutoTokenizer.from_pretrained('Qwen/Qwen2.5-0.5B-Instruct'); AutoModelForCausalLM.from_pretrained('Qwen/Qwen2.5-0.5B-Instruct')"


EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
