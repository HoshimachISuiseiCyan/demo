from __future__ import annotations

import hashlib
import math
from abc import ABC, abstractmethod
from typing import Iterable

import numpy as np
from openai import OpenAI


class EmbeddingService(ABC):
    dimension: int

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError

    def similarity(self, vec1: Iterable[float], vec2: Iterable[float]) -> float:
        a = np.array(list(vec1), dtype=np.float32)
        b = np.array(list(vec2), dtype=np.float32)
        if a.size == 0 or b.size == 0:
            return 0.0
        if a.size != b.size:
            size = min(a.size, b.size)
            a = a[:size]
            b = b[:size]
        denom = float(np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)


class SentenceTransformerEmbeddingService(EmbeddingService):
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)
        self.dimension = int(self._model.get_sentence_embedding_dimension())

    def embed(self, text: str) -> list[float]:
        vector = self._model.encode(text, normalize_embeddings=True)
        return [float(v) for v in vector]


class APIEmbeddingService(EmbeddingService):
    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self.dimension = 1536

    def embed(self, text: str) -> list[float]:
        response = self._client.embeddings.create(model=self._model, input=text)
        vector = response.data[0].embedding
        self.dimension = len(vector)
        return [float(v) for v in vector]


class SimpleHashEmbeddingService(EmbeddingService):
    """
    开发兜底实现：无模型依赖，确保系统可运行。
    正式环境建议改为 Sentence-BERT 或 API Embedding。
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def embed(self, text: str) -> list[float]:
        vec = np.zeros(self.dimension, dtype=np.float32)
        tokens = text.lower().split()
        if not tokens:
            return vec.tolist()

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for i in range(0, len(digest), 4):
                chunk = digest[i : i + 4]
                if len(chunk) < 4:
                    continue
                slot = int.from_bytes(chunk, "little") % self.dimension
                vec[slot] += 1.0

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec.tolist()


def clamp_01(value: float) -> float:
    if math.isnan(value):
        return 0.0
    return max(0.0, min(1.0, value))

