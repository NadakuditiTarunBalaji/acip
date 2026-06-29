"""
ACIP-X1 — Breakdown AI Assistance API (Day 19 / C5)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.config.database import get_db
from backend.services.breakdown_service import (
    check_for_breakdown,
    get_breakdown_history,
    get_breakdown_by_id,
    save_conversation,
    resolve_breakdown,
)
from backend.services.breakdown_chat_service import get_or_start_conversation, send_message

router = APIRouter(
    prefix="/api/breakdown",
    tags=["Breakdown AI Assistance (C5)"]
)


class ChatMessageRequest(BaseModel):
    message: str


@router.get("/history/{vehicle_id}")
def breakdown_history(vehicle_id: str, db: Session = Depends(get_db)):
    return get_breakdown_history(db, vehicle_id)


@router.patch("/resolve/{breakdown_id}")
def resolve(breakdown_id: int, db: Session = Depends(get_db)):
    event = resolve_breakdown(db, breakdown_id)
    if not event:
        raise HTTPException(status_code=404, detail="Breakdown event not found")
    return {"resolved": True, "breakdown_id": breakdown_id}


@router.post("/check/{vehicle_id}")
def manual_check(vehicle_id: str, db: Session = Depends(get_db)):
    """
    Re-runs the automatic detection logic on demand — not a separate
    trigger mechanism, just lets the dashboard (or a demo) ask 'has
    this vehicle broken down right now?' without waiting for the next
    telemetry post. Trigger is still and only ever "Automatic".
    """
    event = check_for_breakdown(db, vehicle_id)
    if event is None:
        return {"breakdown_detected": False}
    return {"breakdown_detected": True, "breakdown_id": event.id, "trigger": event.trigger}


@router.get("/chat/{breakdown_id}")
def get_chat(breakdown_id: int, db: Session = Depends(get_db)):
    """
    Returns the conversation for this breakdown, seeding it with an
    opening assistant message grounded in the diagnosis if no
    conversation exists yet.
    """
    event = get_breakdown_by_id(db, breakdown_id)
    if not event:
        raise HTTPException(status_code=404, detail="Breakdown event not found")

    conversation = get_or_start_conversation(event)
    if not event["conversation"]:
        save_conversation(db, breakdown_id, conversation)
    return {"breakdown_id": breakdown_id, "conversation": conversation}


@router.post("/chat/{breakdown_id}")
def post_chat_message(breakdown_id: int, body: ChatMessageRequest, db: Session = Depends(get_db)):
    """
    Sends the owner's message to the AI assistant, grounded in this
    breakdown's diagnosed fault, and returns the updated conversation.
    """
    event = get_breakdown_by_id(db, breakdown_id)
    if not event:
        raise HTTPException(status_code=404, detail="Breakdown event not found")

    conversation = event["conversation"] or get_or_start_conversation(event)
    result = send_message(event, conversation, body.message)
    save_conversation(db, breakdown_id, result["conversation"])
    return {
        "breakdown_id": breakdown_id,
        "conversation": result["conversation"],
        "ai_available": result["ai_available"],
    }