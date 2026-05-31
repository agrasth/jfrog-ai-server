#!/usr/bin/env bash
# Start the jf chat inference server.
# Downloads model + index from Artifactory if not already present.
set -e

ARTIFACTORY_URL="${ARTIFACTORY_URL:-https://ecosysjfrog.jfrog.io/artifactory}"
ARTIFACTORY_TOKEN="${ARTIFACTORY_TOKEN:-}"
INDEX_PATH="${INDEX_PATH:-output/faiss.index}"
CHUNKS_PATH="${CHUNKS_PATH:-output/chunks.json}"
MODEL_PATH="${MODEL_PATH:-models/llama3-8b-q4.gguf}"
PORT="${PORT:-8080}"

mkdir -p output models

_download() {
    local src="$1" dst="$2"
    if [ ! -f "$dst" ]; then
        echo "Downloading $dst from Artifactory..."
        curl -fL -H "Authorization: Bearer $ARTIFACTORY_TOKEN" \
             "$ARTIFACTORY_URL/ai-chat/$src" -o "$dst"
        echo "Done: $dst"
    else
        echo "Already present: $dst"
    fi
}

if [ -n "$ARTIFACTORY_TOKEN" ]; then
    _download "faiss.index"            "$INDEX_PATH"
    _download "chunks.json"            "$CHUNKS_PATH"
    _download "models/llama3-8b-q4.gguf" "$MODEL_PATH"
else
    echo "ARTIFACTORY_TOKEN not set — using local files (must exist at $INDEX_PATH, $CHUNKS_PATH, $MODEL_PATH)"
fi

exec uvicorn main:app --host 0.0.0.0 --port "$PORT"
