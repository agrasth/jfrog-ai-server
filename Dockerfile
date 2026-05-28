FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .

ENV INDEX_PATH=/data/faiss.index
ENV CHUNKS_PATH=/data/chunks.json
ENV MODEL_PATH=/models/llama3-8b-q4.gguf

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
