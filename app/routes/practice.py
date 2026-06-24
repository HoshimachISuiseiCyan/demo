from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.services.evaluator import LearningEvaluator
from app.db import get_db

router = APIRouter()
evaluator = LearningEvaluator()


@router.post("/answer")
def answer(
    user_id: str,
    question_id: int,
    user_answer: str,
    db: Session = Depends(get_db),
):
    return evaluator.evaluate_answer(db, user_id, question_id, user_answer)

@router.get("/adaptive")
def adaptive(user_id: str, db: Session = Depends(get_db)):
    evaluator = LearningEvaluator()
    knowledge_list = evaluator.select_adaptive_knowledge(db, user_id)

    return [
        {
            "id": k.id,
            "name": k.name,
            "importance": k.importance
        }
        for k in knowledge_list
    ]