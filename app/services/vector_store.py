from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from threading import Lock

import numpy as np

try:
    import faiss  # type: ignore
except Exception:  # pragma: no cover
    faiss = None


@dataclass
class SearchHit:
    item_id: str
    score: float


class VectorStore(ABC):
    @abstractmethod
    def add(self, item_id: str, vector: list[float]) -> None:
        raise NotImplementedError

    @abstractmethod
    def search(self, query_vector: list[float], top_k: int = 5, min_score: float = 0.0) -> list[SearchHit]:
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError


class NumpyVectorStore(VectorStore):
    def __init__(self, dimension: int):
        self.dimension = dimension
        self._ids: list[str] = []
        self._vectors: list[np.ndarray] = []
        self._lock = Lock()

    def add(self, item_id: str, vector: list[float]) -> None:
        vec = _normalize_vector(vector, self.dimension)
        with self._lock:
            self._ids.append(item_id)
            self._vectors.append(vec)

    def search(self, query_vector: list[float], top_k: int = 5, min_score: float = 0.0) -> list[SearchHit]:
        if top_k <= 0:
            return []
        query = _normalize_vector(query_vector, self.dimension)
        with self._lock:
            if not self._vectors:
                return []
            matrix = np.vstack(self._vectors)
            scores = matrix @ query
            order = np.argsort(scores)[::-1][:top_k]
            hits: list[SearchHit] = []
            for idx in order:
                score = float(scores[idx])
                if score >= min_score:
                    hits.append(SearchHit(item_id=self._ids[int(idx)], score=score))
            return hits

    def clear(self) -> None:
        with self._lock:
            self._ids.clear()
            self._vectors.clear()


class FAISSVectorStore(VectorStore):
    def __init__(self, dimension: int):
        if faiss is None:
            raise RuntimeError("faiss 未安装，无法使用 FAISSVectorStore")
        self.dimension = dimension
        self._index = faiss.IndexFlatIP(dimension)
        self._ids: list[str] = []
        self._lock = Lock()

    def add(self, item_id: str, vector: list[float]) -> None:
        vec = _normalize_vector(vector, self.dimension).reshape(1, -1).astype(np.float32)
        with self._lock:
            self._index.add(vec)
            self._ids.append(item_id)

    def search(self, query_vector: list[float], top_k: int = 5, min_score: float = 0.0) -> list[SearchHit]:
        if top_k <= 0:
            return []
        query = _normalize_vector(query_vector, self.dimension).reshape(1, -1).astype(np.float32)
        with self._lock:
            if self._index.ntotal == 0:
                return []
            scores, indices = self._index.search(query, top_k)

        hits: list[SearchHit] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            val = float(score)
            if val >= min_score:
                hits.append(SearchHit(item_id=self._ids[int(idx)], score=val))
        return hits

    def clear(self) -> None:
        with self._lock:
            self._index.reset()
            self._ids.clear()


def _normalize_vector(vector: list[float], target_dim: int) -> np.ndarray:
    arr = np.array(vector, dtype=np.float32)
    if arr.size == 0:
        return np.zeros(target_dim, dtype=np.float32)
    if arr.size < target_dim:
        arr = np.pad(arr, (0, target_dim - arr.size))
    elif arr.size > target_dim:
        arr = arr[:target_dim]
    norm = np.linalg.norm(arr)
    if norm > 0:
        arr = arr / norm
    return arr

