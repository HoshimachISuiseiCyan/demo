from __future__ import annotations

import json
from datetime import datetime
from typing import Generator

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from app.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


class Knowledge(Base):
    __tablename__ = "knowledge"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    definition = Column(Text, nullable=False)
    key_points = Column(Text, nullable=False, default="[]")
    importance = Column(Float, nullable=False, default=0.5)
    embedding = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    questions = relationship("Question", back_populates="knowledge")


class Question(Base):
    __tablename__ = "question"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    options = Column(Text, nullable=False, default="[]")
    answer = Column(String(1), nullable=False)
    difficulty = Column(Integer, nullable=False, default=1)
    knowledge_id = Column(Integer, ForeignKey("knowledge.id"), nullable=False, index=True)
    embedding = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    knowledge = relationship("Knowledge", back_populates="questions")
    records = relationship("Record", back_populates="question")


class Record(Base):
    __tablename__ = "record"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("question.id"), nullable=False, index=True)
    correct = Column(Boolean, nullable=False)
    time = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    question = relationship("Question", back_populates="records")


class Mastery(Base):
    __tablename__ = "mastery"
    __table_args__ = (UniqueConstraint("user_id", "knowledge_id", name="uix_user_knowledge"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    knowledge_id = Column(Integer, ForeignKey("knowledge.id"), nullable=False, index=True)
    score = Column(Float, nullable=False, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def serialize_vector(vector: list[float]) -> str:
    return json.dumps(vector, ensure_ascii=False)


def deserialize_vector(payload: str | None) -> list[float]:
    if not payload:
        return []
    try:
        value = json.loads(payload)
        if isinstance(value, list):
            return [float(v) for v in value]
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return []


def serialize_str_list(values: list[str]) -> str:
    return json.dumps(values, ensure_ascii=False)


def deserialize_str_list(payload: str | None) -> list[str]:
    if not payload:
        return []
    try:
        value = json.loads(payload)
        if isinstance(value, list):
            return [str(item) for item in value]
    except (json.JSONDecodeError, TypeError):
        pass
    return []

