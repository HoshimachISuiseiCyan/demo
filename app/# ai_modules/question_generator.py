from __future__ import annotations

import random
from typing import Any

from app.models.schemas import ConceptRead
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService


class QuestionGenerator:
    def __init__(
        self,
        llm_service: LLMService,
        embedding_service: EmbeddingService,
        similarity_threshold: float = 0.93,
        max_attempts: int = 3,
    ):
        self.llm_service = llm_service
        self.embedding_service = embedding_service
        self.similarity_threshold = similarity_threshold
        self.max_attempts = max_attempts

    def generate(
        self,
        concept: ConceptRead,
        existing_questions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        existing_questions = existing_questions or []
        ban_texts = [q.get("question", "") for q in existing_questions if q.get("question")]

        for attempt in range(self.max_attempts):
            candidate = self._generate_with_llm(concept, ban_texts)
            candidate = self._normalize_question(candidate, concept.id)
            if not self._is_duplicate(candidate, existing_questions):
                return candidate

        fallback = self._fallback_question(concept)
        return self._normalize_question(fallback, concept.id)

    def _generate_with_llm(self, concept: ConceptRead, ban_texts: list[str]) -> dict[str, Any]:
        ban_hint = "\n".join([f"- {text}" for text in ban_texts[:5]])
        if not ban_hint:
            ban_hint = "- (无)"

        system_prompt = "你是考试命题专家。只输出 JSON，不要输出解释。"
        user_prompt = f"""
请基于以下知识点生成一道客观题（仅限单选题，A/B/C/D）：
- 知识点名称：{concept.name}
- 定义：{concept.definition}
- 关键要点：{concept.key_points}

输出格式（严格 JSON）：
{{
  "question": "题干",
  "options": ["A选项", "B选项", "C选项", "D选项"],
  "answer": "A",
  "difficulty": 1,
  "knowledge_id": {concept.id}
}}

命题要求：
1) 错误选项必须“看起来合理”，且与正确答案语义接近，不能明显荒谬。
2) 题目必须可客观判分。
3) 避免与以下历史题目重复：
{ban_hint}
"""
        return self.llm_service.generate_json(system_prompt, user_prompt)

    def _normalize_question(self, raw: dict[str, Any], knowledge_id: int) -> dict[str, Any]:
        question = str(raw.get("question", "")).strip() or "以下哪项描述最准确？"
        options_raw = raw.get("options", [])
        if not isinstance(options_raw, list):
            options_raw = [str(options_raw)]
        options = [str(item).strip() for item in options_raw if str(item).strip()]
        while len(options) < 4:
            options.append(f"备选项{len(options) + 1}")
        options = options[:4]

        answer = str(raw.get("answer", "A")).strip().upper()
        if answer not in {"A", "B", "C", "D"}:
            answer = "A"

        try:
            difficulty = int(raw.get("difficulty", 1))
        except (TypeError, ValueError):
            difficulty = 1
        difficulty = min(3, max(1, difficulty))

        return {
            "question": question,
            "options": options,
            "answer": answer,
            "difficulty": difficulty,
            "knowledge_id": knowledge_id,
        }

    def _is_duplicate(self, candidate: dict[str, Any], existing_questions: list[dict[str, Any]]) -> bool:
        candidate_text = candidate["question"] + " " + " ".join(candidate["options"])
        candidate_vec = self.embedding_service.embed(candidate_text)

        for item in existing_questions:
            embedding = item.get("embedding")
            if not embedding:
                existing_text = item.get("question", "") + " " + " ".join(item.get("options", []))
                embedding = self.embedding_service.embed(existing_text)
            score = self.embedding_service.similarity(candidate_vec, embedding)
            if score >= self.similarity_threshold:
                return True
        return False

    def _fallback_question(self, concept: ConceptRead) -> dict[str, Any]:
        correct = concept.definition
        near_wrong_1 = f"{concept.definition}（但忽略了适用边界）"
        near_wrong_2 = f"{concept.name}只与单一场景有关"
        near_wrong_3 = f"{concept.name}等同于其一个局部现象"

        options = [correct, near_wrong_1, near_wrong_2, near_wrong_3]
        random.shuffle(options)
        answer_index = options.index(correct)
        answer = ["A", "B", "C", "D"][answer_index]

        return {
            "question": f"关于“{concept.name}”，下列说法哪一项最准确？",
            "options": options,
            "answer": answer,
            "difficulty": 2,
            "knowledge_id": concept.id,
        }

