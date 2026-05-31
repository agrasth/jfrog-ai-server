FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

COPY *.py .
COPY start.sh .
RUN chmod +x start.sh

ENV INDEX_PATH=/data/faiss.index
ENV CHUNKS_PATH=/data/chunks.json
ENV MODEL_PATH=/models/llama3-8b-q4.gguf
ENV ARTIFACTORY_URL=https://ecosysjfrog.jfrog.io/artifactory

EXPOSE 8080

# start.sh downloads artifacts from Artifactory if ARTIFACTORY_TOKEN is set,
# then starts uvicorn
CMD ["./start.sh"]
