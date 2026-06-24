# app/routes/questions.py

from fastapi import APIRouter
from app.db import SessionLocal
from app.models import Question
from app.services.ai_service import AIService
import json

router = APIRouter()
ai = AIService()

@router.post("/generate")
def generate(bank_id: int, text: str):
    db = SessionLocal()
    qs = ai.generate_questions(text)

    for q in qs:
        db.add(Question(
            bank_id=bank_id,
            question=q["question"],
            options=json.dumps(q["options"]),
            answer=q["answer"],
            knowledge=q["knowledge"]
        ))

    db.commit()
    return {"msg": "ok"}


@router.get("/questions")
def get_questions(bank_id: int):
    db = SessionLocal()
    return db.query(Question).filter_by(bank_id=bank_id).all()