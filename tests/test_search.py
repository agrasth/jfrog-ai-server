import sys, os, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
import faiss
from search import DocSearcher

def _make_index(tmpdir: str) -> tuple[str, str]:
    chunks = [
        {"text": "Use jf mvn deploy to publish a Maven artifact to Artifactory.", "source": "rdme-artifactory/maven.md", "section": "Maven"},
        {"text": "Configure repositories with jf mvn-config before running builds.", "source": "rdme-artifactory/maven.md", "section": "Maven"},
        {"text": "Use jf rt upload to upload files to Artifactory.", "source": "rdme-artifactory/upload.md", "section": "Upload"},
        {"text": "jf rt download retrieves artifacts from Artifactory.", "source": "rdme-artifactory/download.md", "section": "Download"},
        {"text": "Xray scans your artifacts for security vulnerabilities.", "source": "rdme-security/xray.md", "section": "Xray"},
    ]
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode([c["text"] for c in chunks], normalize_embeddings=True).astype(np.float32)
    index = faiss.IndexFlatIP(384)
    index.add(embeddings)
    index_path = os.path.join(tmpdir, "faiss.index")
    chunks_path = os.path.join(tmpdir, "chunks.json")
    faiss.write_index(index, index_path)
    with open(chunks_path, "w") as f:
        json.dump(chunks, f)
    return index_path, chunks_path

def test_search_returns_list():
    with tempfile.TemporaryDirectory() as d:
        idx, chk = _make_index(d)
        searcher = DocSearcher(idx, chk)
        results = searcher.search("how to publish maven artifact")
        assert isinstance(results, list)

def test_search_top_k_respected():
    with tempfile.TemporaryDirectory() as d:
        idx, chk = _make_index(d)
        searcher = DocSearcher(idx, chk)
        results = searcher.search("maven", top_k=2)
        assert len(results) == 2

def test_search_most_relevant_first():
    with tempfile.TemporaryDirectory() as d:
        idx, chk = _make_index(d)
        searcher = DocSearcher(idx, chk)
        results = searcher.search("publish maven artifact to Artifactory", top_k=3)
        assert "maven" in results[0]["text"].lower()

def test_search_result_has_score():
    with tempfile.TemporaryDirectory() as d:
        idx, chk = _make_index(d)
        searcher = DocSearcher(idx, chk)
        results = searcher.search("maven", top_k=1)
        assert "score" in results[0]
        assert isinstance(results[0]["score"], float)
