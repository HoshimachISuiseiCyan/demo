from sqlalchemy import Column, Integer, String, ForeignKey
from app.db import Base

class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    user_answer = Column(String)
    score = Column(Integer, default=0)