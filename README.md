# jfrog-ai-server

> FastAPI inference server powering [jf chat](https://github.com/jfrog/jfrog-cli) — the AI documentation assistant built into JFrog CLI.

Receives queries from `jf chat`, retrieves relevant documentation chunks via FAISS vector search, feeds them to a local Llama 3 8B model, and streams the answer back as Server-Sent Events.

---

## How it works

```
POST /v1/chat  {"query": "how do I publish a Maven artifact?"}
    ↓
search.py      → embeds query, searches FAISS index, returns top-3 chunks
    ↓
prompt.py      → builds prompt: system + doc chunks + conversation history + question
    ↓
llm.py         → Llama 3 8B GGUF streams tokens
    ↓
SSE stream     → tokens sent to jf CLI in real time
```

**Zero cost per query.** No OpenAI. No Anthropic. No per-token billing.

---

## Quickstart

### 1. Get the model and index

Download from Artifactory:
```bash
mkdir -p models output
jf rt download ai-chat/llama3-8b-q4.gguf models/ --server-id your-server
jf rt download ai-chat/faiss.index output/
jf rt download ai-chat/chunks.json output/
```

Or build the index locally using [jfrog-ai-indexer](https://github.com/agrasth/jfrog-ai-indexer).

Download Llama 3 8B GGUF from HuggingFace:
```bash
hf download bartowski/Meta-Llama-3-8B-Instruct-GGUF \
  Meta-Llama-3-8B-Instruct-Q4_K_M.gguf \
  --local-dir models
mv models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf models/llama3-8b-q4.gguf
```

### 2. Install and run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

INDEX_PATH=output/faiss.index \
CHUNKS_PATH=output/chunks.json \
MODEL_PATH=models/llama3-8b-q4.gguf \
uvicorn main:app --port 8080
```

### 3. Test it

```bash
curl -s http://localhost:8080/health
# → {"status":"ok"}

curl -N -X POST http://localhost:8080/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "how do I publish a Maven artifact?"}'
# → streams SSE response
```

---

## Docker

```bash
docker build -t jf-chat-server .

docker run -p 8080:8080 \
  -v $(pwd)/output:/data \
  -v $(pwd)/models:/models \
  jf-chat-server
```

The container pulls `faiss.index`, `chunks.json`, and `llama3-8b-q4.gguf` from mounted volumes (or Artifactory via env vars).

---

## API

### `POST /v1/chat`

```json
{
  "query": "how do I configure Xray policies?",
  "history": [
    {"role": "user", "content": "what is Xray?"},
    {"role": "assistant", "content": "Xray is JFrog's security scanner..."}
  ]
}
```

Response: `text/event-stream` (SSE)

```
data: "To configure"
data: " an Xray policy"
...
data: [DONE]
data: {"sources": ["rdme-security/docs/xray.md"]}
```

### `GET /health`

```json
{"status": "ok"}
```

---

## Configuration

| Env var | Default | Description |
|---|---|---|
| `INDEX_PATH` | `output/faiss.index` | Path to FAISS index |
| `CHUNKS_PATH` | `output/chunks.json` | Path to chunks metadata |
| `MODEL_PATH` | `models/llama3-8b-q4.gguf` | Path to Llama 3 GGUF model |

---

## Fine-tuning (optional)

To fine-tune the model on JFrog-specific Q&A pairs:

```bash
# Generate training data first (see jfrog-ai-indexer)
pip install -r requirements-finetune.txt
python finetune.py
# → models/jfrog-llama3-finetuned-q4.gguf (~4.7GB, requires GPU 16GB+)

# Deploy
cp models/jfrog-llama3-finetuned-q4.gguf models/llama3-8b-q4.gguf
# Restart server
```

---

## Tech stack

- **Python 3.11**
- [FastAPI](https://fastapi.tiangolo.com/) — web framework
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) — Llama 3 8B inference (GGUF, CPU)
- [sentence-transformers](https://www.sbert.net/) — query embedding
- [faiss-cpu](https://github.com/facebookresearch/faiss) — vector similarity search
- [Unsloth](https://github.com/unslothai/unsloth) + [TRL](https://github.com/huggingface/trl) — fine-tuning (optional)

---

## Related repos

- **[jfrog-ai-indexer](https://github.com/agrasth/jfrog-ai-indexer)** — builds the FAISS index this server uses
- **[jfrog-cli](https://github.com/jfrog/jfrog-cli)** — the `jf chat` command lives here
