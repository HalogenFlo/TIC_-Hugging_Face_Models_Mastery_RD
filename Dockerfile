FROM python:3.10-slim

WORKDIR /workspace

COPY ./app /workspace/app

RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
    torch torchvision torchaudio && \
    pip install -- no-cache-dir  fastapi uvicorn transformers google-cloud-aiplatform huggingface_hub

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
