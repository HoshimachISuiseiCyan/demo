from __future__ import annotations

import re
from typing import Any

from app.services.embedding_service import EmbeddingService, clamp_01
from app.services.llm_service import LLMService
from app.utils.text_splitter import split_text


class KnowledgeExtractor:
    def __init__(
        self,
        llm_service: LLMService,
        embedding_service: EmbeddingService,
        max_chunk_chars: int = 1200,
        chunk_overlap_chars: int = 150,
        similarity_threshold: float = 0.86,
    ):
        self.llm_service = llm_service
        self.embedding_service = embedding_service
        self.max_chunk_chars = max_chunk_chars
        self.chunk_overlap_chars = chunk_overlap_chars
        self.similarity_threshold = similarity_threshold

    def extract(self, raw_text: str) -> dict[str, Any]:
        text = raw_text.strip()
        if not text:
            return {"concepts": []}

        chunks = split_text(
            text=text,
            max_chars=self.max_chunk_chars,
            overlap_chars=self.chunk_overlap_chars,
        )
        all_concepts: list[dict[str, Any]] = []
        for chunk in chunks:
            all_concepts.extend(self._extract_from_chunk(chunk))

        merged = self._merge_similar_concepts(all_concepts)
        return {"concepts": merged}

    def _extract_from_chunk(self, chunk: str) -> list[dict[str, Any]]:
        system_prompt = (
            "你是知识抽取助手。只返回 JSON，不允许 markdown，不允许解释文字。"
        )
        user_prompt = f"""
从以下文本中抽取关键知识点，输出严格 JSON：

{{
  "concepts": [
    {{
      "id": 1,
      "name": "概念名",
      "definition": "定义",
      "key_points": ["要点1", "要点2"],
      "importance": 0.0
    }}
  ]
}}

规则：
1) importance 必须在 0~1。
2) key_points 至少 1 条。
3) 只保留可学习、可考核的客观知识点。

文本：
\"\"\"{chunk}\"\"\"
"""
        try:
            payload = self.llm_service.generate_json(system_prompt, user_prompt)
            concepts = payload.get("concepts", [])
            if isinstance(concepts, list):
                return [self._normalize_concept(c, index + 1) for index, c in enumerate(concepts)]
        except Exception:
            pass
        return self._fallback_extract(chunk)

    def _fallback_extract(self, chunk: str) -> list[dict[str, Any]]:
        # LLM 不可用时的兜底：按句子生成可用概念，保证流程不断。
        sentences = re.split(r"[。！？.!?]", chunk)
        concepts: list[dict[str, Any]] = []
        for sentence in sentences:
            cleaned = sentence.strip()
            if len(cleaned) < 20:
                continue
            name = cleaned[:18]
            concepts.append(
                {
                    "id": len(concepts) + 1,
                    "name": name,
                    "definition": cleaned,
                    "key_points": [cleaned[:40]],
                    "importance": 0.5,
                }
            )
            if len(concepts) >= 6:
                break
        return concepts

    def _normalize_concept(self, raw: dict[str, Any], fallback_id: int) -> dict[str, Any]:
        name = str(raw.get("name", "")).strip() or f"概念{fallback_id}"
        definition = str(raw.get("definition", "")).strip() or name

        key_points_raw = raw.get("key_points", [])
        if not isinstance(key_points_raw, list):
            key_points_raw = [str(key_points_raw)]
        key_points = [str(item).strip() for item in key_points_raw if str(item).strip()]
        if not key_points:
            key_points = [definition[:80]]

        try:
            importance = clamp_01(float(raw.get("importance", 0.5)))
        except (TypeError, ValueError):
            importance = 0.5

        return {
            "id": fallback_id,
            "name": name,
            "definition": definition,
            "key_points": key_points[:8],
            "importance": importance,
        }

    def _merge_similar_concepts(self, concepts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        merged_vectors: list[list[float]] = []

        for concept in concepts:
            candidate = self._normalize_concept(concept, fallback_id=len(merged) + 1)
            candidate_vec = self.embedding_service.embed(
                f"{candidate['name']} {candidate['definition']}"
            )

            hit_index = -1
            hit_score = 0.0
            for idx, vector in enumerate(merged_vectors):
                score = self.embedding_service.similarity(candidate_vec, vector)
                if score > hit_score:
                    hit_index = idx
                    hit_score = score

            if hit_index >= 0 and hit_score >= self.similarity_threshold:
                current = merged[hit_index]
                current["importance"] = max(current["importance"], candidate["importance"])
                if len(candidate["definition"]) > len(current["definition"]):
                    current["definition"] = candidate["definition"]
                merged_points = list(dict.fromkeys(current["key_points"] + candidate["key_points"]))
                current["key_points"] = merged_points[:10]
                continue

            merged.append(candidate)
            merged_vectors.append(candidate_vec)

        for index, item in enumerate(merged, start=1):
            item["id"] = index
        return merged

