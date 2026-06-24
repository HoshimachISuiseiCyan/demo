import os
from dotenv import load_dotenv
import os

def get_llm_service():
    load_dotenv()  # 👈 强制加载（保险做法）

    return DoubaoLLMService(
        api_key=os.getenv("LLM_API_KEY"),
        model=os.getenv("LLM_MODEL"),
        base_url=os.getenv("LLM_BASE_URL"),
    )

from app.services.embedding_service import (
    SimpleHashEmbeddingService,
    SentenceTransformerEmbeddingService,
    APIEmbeddingService,
)
from app.services.llm_service import DoubaoLLMService


def get_embedding_service():
    mode = os.getenv("EMBEDDING_MODE", "simple")

    if mode == "sentence":
        return SentenceTransformerEmbeddingService("all-MiniLM-L6-v2")

    elif mode == "api":
        return APIEmbeddingService(
            api_key=os.getenv("EMBEDDING_API_KEY"),
            model="text-embedding-3-small",
            base_url=os.getenv("EMBEDDING_BASE_URL"),
        )

    return SimpleHashEmbeddingService()


def get_llm_service():
    print("DEBUG:", os.getenv("LLM_API_KEY"))
    return DoubaoLLMService(
    api_key=os.getenv("LLM_API_KEY"),
    model=os.getenv("LLM_MODEL"),
    base_url=os.getenv("LLM_BASE_URL"),
)