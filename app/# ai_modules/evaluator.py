from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.database import Knowledge, Mastery, Question, Record


class LearningEvaluator:
    """
    负责掌握度更新与自适应选题策略。
    选题综合 3 个信号：
    1) 低掌握度优先
    2) 高重要度优先
    3) 近期错题优先
    """

    def evaluate_answer(
        self,
        db: Session,
        user_id: str,
        question_id: int,
        user_answer: str,
    ) -> dict[str, float | bool]:
        question = db.get(Question, question_id)
        if question is None:
            raise ValueError("题目不存在")

        normalized = user_answer.strip().upper()[:1]
        correct = normalized == question.answer.upper()

        record = Record(
            user_id=user_id,
            question_id=question.id,
            correct=correct,
            time=datetime.utcnow(),
        )
        db.add(record)

        mastery = db.execute(
            select(Mastery).where(
                Mastery.user_id == user_id,
                Mastery.knowledge_id == question.knowledge_id,
            )
        ).scalar_one_or_none()
        if mastery is None:
            mastery = Mastery(user_id=user_id, knowledge_id=question.knowledge_id, score=0.0)
            db.add(mastery)
            db.flush()

        if correct:
            mastery.score += (1.0 - mastery.score) * 0.3
        else:
            mastery.score *= 0.7
        mastery.score = max(0.0, min(1.0, mastery.score))
        mastery.updated_at = datetime.utcnow()

        db.commit()
        return {"correct": correct, "mastery": round(float(mastery.score), 4)}

    def select_adaptive_knowledge(self, db: Session, user_id: str, limit: int = 5) -> list[Knowledge]:
        if limit <= 0:
            return []

        knowledge_items = db.execute(select(Knowledge)).scalars().all()
        if not knowledge_items:
            return []

        mastery_rows = db.execute(select(Mastery).where(Mastery.user_id == user_id)).scalars().all()
        mastery_map = {row.knowledge_id: float(row.score) for row in mastery_rows}

        recent_since = datetime.utcnow() - timedelta(days=7)
        mistake_rows = (
            db.query(Question.knowledge_id, func.count(Record.id))
            .join(Record, Record.question_id == Question.id)
            .filter(Record.user_id == user_id, Record.correct.is_(False), Record.time >= recent_since)
            .group_by(Question.knowledge_id)
            .all()
        )
        mistake_map = {int(kid): int(cnt) for kid, cnt in mistake_rows}

        scored: list[tuple[float, Knowledge]] = []
        for item in knowledge_items:
            mastery_score = 1.0 - mastery_map.get(item.id, 0.0)
            importance_score = max(0.0, min(1.0, float(item.importance)))
            mistake_score = min(1.0, mistake_map.get(item.id, 0) / 3.0)
            priority = mastery_score * 0.5 + importance_score * 0.3 + mistake_score * 0.2
            scored.append((priority, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]

