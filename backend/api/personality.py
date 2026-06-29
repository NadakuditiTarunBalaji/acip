"""
ACIP-X1 — AI Car Personality & Voice Assistant API (Day 20 / C6 + C10)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.config.database import get_db
from backend.services.personality_service import get_proactive_messages
from backend.services.car_chat_service import get_conversation, send_message, reset_conversation
from backend.services.unified_voice_service import (
    get_conversation as get_unified_conversation,
    send_message as send_unified_message,
    reset_conversation as reset_unified_conversation,
)

router = APIRouter(
    prefix="/api/personality",
    tags=["AI Car Personality & Voice Assistant (C6 + C10)"]
)


class ChatMessageRequest(BaseModel):
    message: str


@router.get("/greeting/{vehicle_id}")
def proactive_messages(vehicle_id: str, db: Session = Depends(get_db)):
    """The car's proactive, personality-driven messages right now —
    health-aware greeting plus an optional driving-habit observation."""
    return get_proactive_messages(db, vehicle_id)


@router.get("/chat/{vehicle_id}")
def get_chat(vehicle_id: str):
    """Returns the current general car chat conversation, seeding a
    friendly opener if this is a new session."""
    return {"vehicle_id": vehicle_id, "conversation": get_conversation(vehicle_id)}


@router.post("/chat/{vehicle_id}")
def post_chat_message(vehicle_id: str, body: ChatMessageRequest, db: Session = Depends(get_db)):
    """Sends the owner's message to the car's AI personality, grounded
    in its real current health/driving data."""
    result = send_message(db, vehicle_id, body.message)
    return {
        "vehicle_id": vehicle_id,
        "conversation": result["conversation"],
        "ai_available": result["ai_available"],
    }


@router.delete("/chat/{vehicle_id}")
def clear_chat(vehicle_id: str):
    """Starts a fresh conversation."""
    reset_conversation(vehicle_id)
    return {"cleared": True, "vehicle_id": vehicle_id}


@router.get("/voice/{vehicle_id}")
def get_voice_conversation(vehicle_id: str, db: Session = Depends(get_db)):
    """
    The unified voice assistant — single conversational surface that
    grounds itself in whatever is currently real for this vehicle
    (active accident > active breakdown > normal chat).
    """
    return get_unified_conversation(db, vehicle_id)


@router.post("/voice/{vehicle_id}")
def post_voice_message(vehicle_id: str, body: ChatMessageRequest, db: Session = Depends(get_db)):
    return send_unified_message(db, vehicle_id, body.message)


@router.delete("/voice/{vehicle_id}")
def clear_voice_conversation(vehicle_id: str):
    reset_unified_conversation(vehicle_id)
    return {"cleared": True, "vehicle_id": vehicle_id}