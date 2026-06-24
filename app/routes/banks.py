# app/routes/banks.py

from fastapi import APIRouter
from app.db import SessionLocal
from app.models import Bank

router = APIRouter()

@router.post("/banks")
def create_bank(name: str):
    db = SessionLocal()
    bank = Bank(name=name)
    db.add(bank)
    db.commit()
    return bank

@router.get("/banks")
def list_banks():
    db = SessionLocal()
    return db.query(Bank).all()