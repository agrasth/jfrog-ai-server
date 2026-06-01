import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

_EMBED_MODEL = "all-MiniLM-L6-v2"

# Automatically add a JFrog CLI-focused variant to any query.
# This ensures CLI command chunks are retrieved alongside conceptual docs.
_CLI_SUFFIX = " jf cli command"


class DocSearcher:
    def __init__(self, index_path: str, chunks_path: str) -> None:
        self._index = faiss.read_index(index_path)
        with open(chunks_path, encoding="utf-8") as f:
            self._chunks: list[dict] = json.load(f)
        self._embedder = SentenceTransformer(_EMBED_MODEL)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        # Search with original query AND a CLI-biased variant, merge unique results
        queries = [query, query + _CLI_SUFFIX]
        vecs = self._embedder.encode(queries, normalize_embeddings=True).astype(np.float32)

        seen: set[int] = set()
        merged: list[dict] = []

        for vec in vecs:
            scores, indices = self._index.search(vec.reshape(1, -1), top_k)
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or idx in seen:
                    continue
                seen.add(idx)
                chunk = self._chunks[idx].copy()
                chunk["score"] = float(score)
                merged.append(chunk)

        # Sort by score, return top_k
        merged.sort(key=lambda c: c["score"], reverse=True)
        return merged[:top_k]
