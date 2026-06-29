"""
ACIP-X1 — AI Chat Assistant for Engineers API (Day 22 / E9)
"""
from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.engineer_chat_service import ask, get_conversation, reset_conversation

router = APIRouter(
    prefix="/api/engineer-chat",
    tags=["AI Chat Assistant for Engineers (E9)"]
)


class QuestionRequest(BaseModel):
    question: str


@router.post("/ask/{session_id}")
def ask_question(session_id: str, body: QuestionRequest):
    """Ask the engineering assistant a natural-language question —
    it will search the Knowledge Graph or run impact analysis as
    needed, grounded in real project data."""
    return ask(session_id, body.question)


@router.delete("/reset/{session_id}")
def reset_chat(session_id: str):
    reset_conversation(session_id)
    return {"cleared": True, "session_id": session_id}