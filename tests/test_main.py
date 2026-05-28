import sys, os, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
import faiss
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock

def _make_index(tmpdir: str) -> tuple[str, str]:
    chunks = [{"text": "Use jf mvn deploy to publish a Maven artifact.", "source": "rdme-artifactory/maven.md", "section": "Maven"}]
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode([c["text"] for c in chunks], normalize_embeddings=True).astype(np.float32)
    index = faiss.IndexFlatIP(384)
    index.add(embeddings)
    idx_path = os.path.join(tmpdir, "faiss.index")
    chk_path = os.path.join(tmpdir, "chunks.json")
    faiss.write_index(index, idx_path)
    with open(chk_path, "w") as f:
        json.dump(chunks, f)
    return idx_path, chk_path

@pytest.fixture
def app_with_mock_llm(tmp_path):
    idx, chk = _make_index(str(tmp_path))
    os.environ["INDEX_PATH"] = idx
    os.environ["CHUNKS_PATH"] = chk
    os.environ["MODEL_PATH"] = "fake_model.gguf"

    mock_runner = MagicMock()
    mock_runner.stream.return_value = iter(["Use ", "jf mvn deploy", "."])

    with patch("main.LlamaRunner", return_value=mock_runner):
        import importlib
        import main as m
        importlib.reload(m)
        yield m.app

@pytest.mark.asyncio
async def test_health(app_with_mock_llm):
    async with AsyncClient(transport=ASGITransport(app=app_with_mock_llm), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_chat_streams_response(app_with_mock_llm):
    async with AsyncClient(transport=ASGITransport(app=app_with_mock_llm), base_url="http://test") as client:
        resp = await client.post("/v1/chat", json={"query": "how to publish maven?"})
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    body = resp.text
    assert "data:" in body

@pytest.mark.asyncio
async def test_empty_query_rejected(app_with_mock_llm):
    async with AsyncClient(transport=ASGITransport(app=app_with_mock_llm), base_url="http://test") as client:
        resp = await client.post("/v1/chat", json={"query": "  "})
    assert resp.status_code == 400

@pytest.mark.asyncio
async def test_long_query_rejected(app_with_mock_llm):
    async with AsyncClient(transport=ASGITransport(app=app_with_mock_llm), base_url="http://test") as client:
        resp = await client.post("/v1/chat", json={"query": "x" * 501})
    assert resp.status_code == 400
