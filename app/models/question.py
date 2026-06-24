from sqlalchemy import Column, Integer, String, Text, ForeignKey
from app.db import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    bank_id = Column(Integer, ForeignKey("banks.id"))
    stem = Column(Text)
    answer = Column(String)