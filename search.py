import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

_EMBED_MODEL = "all-MiniLM-L6-v2"


class DocSearcher:
    def __init__(self, index_path: str, chunks_path: str) -> None:
        self._index = faiss.read_index(index_path)
        with open(chunks_path, encoding="utf-8") as f:
            self._chunks: list[dict] = json.load(f)
        self._embedder = SentenceTransformer(_EMBED_MODEL)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        vec = self._embedder.encode([query], normalize_embeddings=True).astype(np.float32)
        scores, indices = self._index.search(vec, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            chunk = self._chunks[idx].copy()
            chunk["score"] = float(score)
            results.append(chunk)
        return results
