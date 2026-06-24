"""API routes package."""

from fastapi import APIRouter
from . import ai, practice

api_router = APIRouter()

api_router.include_router(ai.router)
api_router.include_router(practice.router, prefix="/practice")