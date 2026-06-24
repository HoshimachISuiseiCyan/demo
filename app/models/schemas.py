from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ConceptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    definition: str
    key_points: list[str] = Field(default_factory=list)
    importance: float = Field(ge=0.0, le=1.0)


class KnowledgeExtractionResponse(BaseModel):
    concepts: list[ConceptRead]


class UploadRequest(BaseModel):
    text: str = Field(min_length=1)


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    options: list[str]
    answer: str
    difficulty: int = Field(ge=1, le=3)
    knowledge_id: int


class QuestionListResponse(BaseModel):
    questions: list[QuestionRead]


class AnswerRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=64)
    question_id: int
    answer: str = Field(min_length=1, max_length=16)


class EvaluationResponse(BaseModel):
    correct: bool
    mastery: float = Field(ge=0.0, le=1.0)


class KnowledgeSearchItem(BaseModel):
    knowledge_id: int
    name: str
    definition: str
    score: float = Field(ge=0.0, le=1.0)


class KnowledgeSearchResponse(BaseModel):
    results: list[KnowledgeSearchItem]
