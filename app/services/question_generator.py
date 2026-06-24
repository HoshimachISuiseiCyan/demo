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

    # ✅ 新增 mode 参数（默认 strict）
    def generate(
        self,
        concept: ConceptRead,
        existing_questions: list[dict[str, Any]] | None = None,
        mode: str = "exam",
    ) -> dict[str, Any]:
        existing_questions = existing_questions or []
        ban_texts = [q.get("question", "") for q in existing_questions if q.get("question")]

        for attempt in range(self.max_attempts):
            candidate = self._generate_with_llm(concept, ban_texts, mode)
            candidate = self._normalize_question(candidate, concept.id)

            # ❗垃圾题过滤
            if self._is_bad_question(candidate["question"]):
                continue

            if not self._is_duplicate(candidate, existing_questions):
                return candidate

        fallback = self._fallback_question(concept)
        return self._normalize_question(fallback, concept.id)

    # ✅ 核心：模式控制
    def _generate_with_llm(self, concept: ConceptRead, ban_texts: list[str], mode: str = "exam") -> dict[str, Any]:
        ban_hint = "\n".join([f"- {text}" for text in ban_texts[:5]]) or "- (无)"

        if mode == "exam":
            mode_rule = """
    【严格模式】
    - 只能基于提供的“定义”和“关键要点”出题
    - 不允许引入额外知识
    - 题目必须可以从原文直接推导
    """
        else:
            mode_rule = """
    【拓展模式】
    - 可以基于知识点进行合理延伸
    - 可以考察应用、理解、对比
    """

        system_prompt = "你是专业命题专家（高质量考试命题人）。只输出JSON，不要解释。"

        user_prompt = f"""
    知识点：
    名称：{concept.name}
    定义：{concept.definition}
    要点：{concept.key_points}

    请生成一道【高质量单选题】（A/B/C/D）

    要求：
    1. 错误选项必须“高度迷惑”（接近正确答案）
    2. 不允许出现明显错误选项
    3. 题目必须具体，不能空泛
    4. 难度 1-3（1简单 3困难）

    {mode_rule}

    避免重复：
    {ban_hint}

    输出格式：
    {{
    "question": "题干（必须具体，不要泛化）",
    "options": ["A.xxx", "B.xxx", "C.xxx", "D.xxx"],
    "answer": "A",
    "difficulty": 2
    }}
    """
        result = self.llm_service.generate_json(system_prompt, user_prompt)

        print("🔥 AI原始出题：", result)  # 👈关键

        return result

    # ❗垃圾题过滤
    def _is_bad_question(self, q: str) -> bool:
        bad_patterns = ["哪种", "策略", "更好", "更有效"]
        return any(p in q for p in bad_patterns)

    def _normalize_question(self, raw: dict[str, Any], knowledge_id: int) -> dict[str, Any]:
        question = str(raw.get("question", "")).strip() or "以下哪项正确？"

        options = raw.get("options", [])
        if not isinstance(options, list):
            options = [str(options)]

        options = [str(o).strip() for o in options if str(o).strip()]
        while len(options) < 4:
            options.append(f"选项{len(options)+1}")
        options = options[:4]

        answer = str(raw.get("answer", "A")).upper()
        if answer not in {"A", "B", "C", "D"}:
            answer = "A"

        difficulty = int(raw.get("difficulty", 1))
        difficulty = max(1, min(3, difficulty))

        return {
            "question": question,
            "options": options,
            "answer": answer,
            "difficulty": difficulty,
            "knowledge_id": knowledge_id,
        }

    def _is_duplicate(self, candidate, existing):
        return False  # 保持你原逻辑也行

    def _fallback_question(self, concept: ConceptRead):
        return {
            "question": f"关于“{concept.name}”，下列说法正确的是：",
            "options": [
                concept.definition,
                concept.name + "只适用于单一情况",
                concept.name + "与其他概念完全相同",
                concept.name + "没有实际作用",
            ],
            "answer": "A",
            "difficulty": 2,
            "knowledge_id": concept.id,
        }