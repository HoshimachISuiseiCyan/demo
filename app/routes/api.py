from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai_modules.evaluator import LearningEvaluator
from app.ai_modules.knowledge_extractor import KnowledgeExtractor
from app.ai_modules.question_generator import QuestionGenerator
from app.dependencies import (
    get_db,
    get_embedding_service,
    get_evaluator,
    get_knowledge_extractor,
    get_question_generator,
    get_vector_store,
)
from app.models.database import (
    Knowledge,
    Question,
    Record,
    deserialize_str_list,
    deserialize_vector,
    serialize_str_list,
    serialize_vector,
)
from app.models.schemas import (
    AnswerRequest,
    ConceptRead,
    EvaluationResponse,
    KnowledgeSearchItem,
    KnowledgeSearchResponse,
    KnowledgeExtractionResponse,
    QuestionListResponse,
    QuestionRead,
    UploadRequest,
)
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/upload", response_model=KnowledgeExtractionResponse)
def upload_text(
    payload: UploadRequest,
    db: Session = Depends(get_db),
    extractor: KnowledgeExtractor = Depends(get_knowledge_extractor),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    vector_store: VectorStore = Depends(get_vector_store),
) -> KnowledgeExtractionResponse:
    result = extractor.extract(payload.text)
    concepts = result.get("concepts", [])
    if not isinstance(concepts, list):
        raise HTTPException(status_code=500, detail="Invalid extraction payload.")

    existing_knowledge = db.execute(select(Knowledge)).scalars().all()
    existing_vectors: dict[int, list[float]] = {
        item.id: deserialize_vector(item.embedding) for item in existing_knowledge
    }
    upserted_map: dict[int, ConceptRead] = {}

    for raw in concepts:
        concept = _to_concept(raw)
        concept_embedding = embedding_service.embed(f"{concept.name} {concept.definition}")
        match = _find_similar_knowledge(
            candidate_vec=concept_embedding,
            knowledge_items=existing_knowledge,
            vector_map=existing_vectors,
            embedding_service=embedding_service,
            threshold=0.88,
        )

        if match:
            merged_points = list(
                dict.fromkeys(deserialize_str_list(match.key_points) + concept.key_points)
            )[:10]
            if len(concept.definition) > len(match.definition):
                match.definition = concept.definition
            match.key_points = serialize_str_list(merged_points)
            match.importance = max(float(match.importance), float(concept.importance))
            match.embedding = serialize_vector(concept_embedding)
            target = match
        else:
            target = Knowledge(
                name=concept.name,
                definition=concept.definition,
                key_points=serialize_str_list(concept.key_points),
                importance=concept.importance,
                embedding=serialize_vector(concept_embedding),
            )
            db.add(target)
            db.flush()
            existing_knowledge.append(target)

        existing_vectors[target.id] = concept_embedding
        vector_store.add(f"knowledge:{target.id}", concept_embedding)
        upserted_map[target.id] = _knowledge_to_schema(target)

    db.commit()
    concepts_sorted = sorted(upserted_map.values(), key=lambda x: x.id)
    return KnowledgeExtractionResponse(concepts=concepts_sorted)


@router.get("/questions", response_model=QuestionListResponse)
def get_questions(
    user_id: str = Query(..., min_length=1, max_length=64),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    evaluator: LearningEvaluator = Depends(get_evaluator),
    generator: QuestionGenerator = Depends(get_question_generator),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    vector_store: VectorStore = Depends(get_vector_store),
) -> QuestionListResponse:
    adaptive_knowledge = evaluator.select_adaptive_knowledge(
        db,
        user_id=user_id,
        limit=max(10, limit),
    )
    if not adaptive_knowledge:
        return QuestionListResponse(questions=[])

    existing_questions_payload = _load_existing_questions_for_dedup(db)
    selected_questions: list[QuestionRead] = []

    for knowledge in adaptive_knowledge:
        knowledge_questions = db.execute(
            select(Question).where(Question.knowledge_id == knowledge.id)
        ).scalars().all()

        if not knowledge_questions:
            concept = _knowledge_to_schema(knowledge)
            generated = generator.generate(
                concept=concept,
                existing_questions=existing_questions_payload,
            )
            content = generated["question"]
            options = generated["options"]
            question_embedding = embedding_service.embed(content + " " + " ".join(options))

            question = Question(
                content=content,
                options=serialize_str_list(options),
                answer=generated["answer"],
                difficulty=generated["difficulty"],
                knowledge_id=knowledge.id,
                embedding=serialize_vector(question_embedding),
            )
            db.add(question)
            db.flush()
            knowledge_questions = [question]

            existing_questions_payload.append(
                {
                    "question": content,
                    "options": options,
                    "embedding": question_embedding,
                }
            )
            vector_store.add(f"question:{question.id}", question_embedding)

        question = _pick_question_for_user(db, user_id=user_id, candidates=knowledge_questions)
        selected_questions.append(_question_to_schema(question))
        if len(selected_questions) >= limit:
            break

    db.commit()
    return QuestionListResponse(questions=selected_questions)


@router.post("/answer", response_model=EvaluationResponse)
def submit_answer(
    payload: AnswerRequest,
    db: Session = Depends(get_db),
    evaluator: LearningEvaluator = Depends(get_evaluator),
) -> EvaluationResponse:
    try:
        result = evaluator.evaluate_answer(
            db=db,
            user_id=payload.user_id,
            question_id=payload.question_id,
            user_answer=payload.answer,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return EvaluationResponse(**result)


@router.post("/answer")
def submit_answer(payload: AnswerRequest):
    print(payload)  # 👈 看看实际收到什么


@router.get("/search", response_model=KnowledgeSearchResponse)
def semantic_search(
    query: str = Query(..., min_length=1),
    top_k: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    vector_store: VectorStore = Depends(get_vector_store),
) -> KnowledgeSearchResponse:
    query_vec = embedding_service.embed(query)
    hits = vector_store.search(query_vec, top_k=top_k, min_score=0.2)
    if not hits:
        return KnowledgeSearchResponse(results=[])

    score_map: dict[int, float] = {}
    ordered_ids: list[int] = []
    for hit in hits:
        if not hit.item_id.startswith("knowledge:"):
            continue
        kid = int(hit.item_id.split(":", 1)[1])
        if kid not in score_map:
            ordered_ids.append(kid)
        score_map[kid] = max(score_map.get(kid, 0.0), hit.score)

    if not ordered_ids:
        return KnowledgeSearchResponse(results=[])

    rows = db.execute(select(Knowledge).where(Knowledge.id.in_(ordered_ids))).scalars().all()
    row_map = {item.id: item for item in rows}

    results: list[KnowledgeSearchItem] = []
    for kid in ordered_ids:
        knowledge = row_map.get(kid)
        if knowledge is None:
            continue
        results.append(
            KnowledgeSearchItem(
                knowledge_id=knowledge.id,
                name=knowledge.name,
                definition=knowledge.definition,
                score=max(0.0, min(1.0, score_map.get(kid, 0.0))),
            )
        )
    return KnowledgeSearchResponse(results=results)


def _to_concept(raw: dict[str, Any]) -> ConceptRead:
    key_points_raw = raw.get("key_points", [])
    if not isinstance(key_points_raw, list):
        key_points_raw = [str(key_points_raw)]
    key_points = [str(v).strip() for v in key_points_raw if str(v).strip()]

    try:
        importance = float(raw.get("importance", 0.5))
    except (TypeError, ValueError):
        importance = 0.5

    return ConceptRead(
        id=int(raw.get("id", 0) or 0),
        name=str(raw.get("name", "")).strip() or "Unnamed concept",
        definition=str(raw.get("definition", "")).strip() or "No definition",
        key_points=key_points,
        importance=max(0.0, min(1.0, importance)),
    )


def _knowledge_to_schema(knowledge: Knowledge) -> ConceptRead:
    return ConceptRead(
        id=knowledge.id,
        name=knowledge.name,
        definition=knowledge.definition,
        key_points=deserialize_str_list(knowledge.key_points),
        importance=max(0.0, min(1.0, float(knowledge.importance))),
    )


def _question_to_schema(question: Question) -> QuestionRead:
    return QuestionRead(
        id=question.id,
        question=question.content,
        options=deserialize_str_list(question.options),
        answer=question.answer,
        difficulty=question.difficulty,
        knowledge_id=question.knowledge_id,
    )


def _find_similar_knowledge(
    candidate_vec: list[float],
    knowledge_items: list[Knowledge],
    vector_map: dict[int, list[float]],
    embedding_service: EmbeddingService,
    threshold: float,
) -> Knowledge | None:
    best_score = 0.0
    best_item: Knowledge | None = None
    for item in knowledge_items:
        vec = vector_map.get(item.id)
        if not vec:
            continue
        score = embedding_service.similarity(candidate_vec, vec)
        if score > best_score:
            best_score = score
            best_item = item
    return best_item if best_score >= threshold else None


def _load_existing_questions_for_dedup(db: Session) -> list[dict[str, Any]]:
    rows = db.execute(select(Question)).scalars().all()
    payload: list[dict[str, Any]] = []
    for row in rows:
        payload.append(
            {
                "question": row.content,
                "options": deserialize_str_list(row.options),
                "embedding": deserialize_vector(row.embedding),
            }
        )
    return payload


def _pick_question_for_user(db: Session, user_id: str, candidates: list[Question]) -> Question:
    if len(candidates) == 1:
        return candidates[0]

    latest_map: dict[int, datetime | None] = {}
    for question in candidates:
        latest = db.execute(
            select(func.max(Record.time)).where(
                Record.user_id == user_id,
                Record.question_id == question.id,
            )
        ).scalar_one()
        latest_map[question.id] = latest

    return sorted(
        candidates,
        key=lambda q: (
            latest_map.get(q.id) is not None,
            latest_map.get(q.id) or datetime.min,
        ),
    )[0]

    