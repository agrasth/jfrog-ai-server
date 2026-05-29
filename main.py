import json
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from search import DocSearcher
from prompt import build_prompt

# Allow tests to inject a mock by setting main.LlamaRunner before reload.
# On first import this attribute doesn't exist yet, so import from llm.
# On reload (e.g. in tests), if LlamaRunner is already set in the module
# namespace (patched), keep it — don't overwrite with the real class.
if "LlamaRunner" not in sys.modules[__name__].__dict__:
    from llm import LlamaRunner  # noqa: E402

app = FastAPI()

_searcher: "DocSearcher | None" = None
_runner = None


def _get_searcher() -> DocSearcher:
    global _searcher
    if _searcher is None:
        _searcher = DocSearcher(
            index_path=os.getenv("INDEX_PATH", "output/faiss.index"),
            chunks_path=os.getenv("CHUNKS_PATH", "output/chunks.json"),
        )
    return _searcher


def _get_runner():
    global _runner
    if _runner is None:
        _runner = LlamaRunner(  # type: ignore[name-defined]
            model_path=os.getenv("MODEL_PATH", "models/llama3-8b-q4.gguf")
        )
    return _runner


class ChatRequest(BaseModel):
    query: str
    history: list[dict] | None = None


def _event_stream(query: str, history: list[dict] | None = None):
    searcher = _get_searcher()
    runner = _get_runner()
    chunks = searcher.search(query)
    prompt = build_prompt(query, chunks, history=history)
    for token in runner.stream(prompt):
        yield f"data: {json.dumps(token)}\n\n"
    yield "data: [DONE]\n\n"
    sources = list({c["source"] for c in chunks})
    yield f"data: {json.dumps({'sources': sources})}\n\n"


@app.post("/v1/chat")
def chat(req: ChatRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    if len(req.query) > 500:
        raise HTTPException(status_code=400, detail="Query too long, keep under 500 characters")
    return StreamingResponse(_event_stream(req.query, req.history), media_type="text/event-stream")


@app.get("/health")
def health():
    return {"status": "ok"}
