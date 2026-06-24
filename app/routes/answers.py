# app/routes/answers.py

from fastapi import APIRouter
from app.db import SessionLocal
from app.models import Attempt

router = APIRouter()

@router.post("/answer")
def answer(question_id: int, is_correct: bool):
    db = SessionLocal()
    db.add(Attempt(question_id=question_id, is_correct=is_correct))
    db.commit()
    return {"msg": "saved"}