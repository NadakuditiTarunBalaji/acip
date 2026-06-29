"""
ACIP-X1 — General Car Chat / Voice Assistant (Day 20 / C10)

Unlike breakdown_chat_service.py (grounded in one specific breakdown
event), this is the car's general-purpose conversational assistant —
"Hey ACIP, how is my car doing today?" from the original product
vision. Grounded in current overall health, active issues/warnings,
and the driver score, all pulled from existing Day 16/17 services
rather than recomputed here.

Conversation is kept in-memory per vehicle for this MVP rather than
persisted to the DB — unlike a breakdown (a discrete incident worth a
permanent record), a casual "how's my car doing" chat is closer to a
live assistant session. If conversation needed to survive a server
restart, this would move to a DB table the same way BreakdownEvent
does it.
"""
from sqlalchemy.orm import Session

from backend.services.gemini_client import generate_reply, CAR_PERSONALITY
from backend.services.dashboard_service import calculate_real_health_score
from backend.services.invisible_mechanic_service import get_invisible_mechanic_report

# In-memory conversation store, keyed by vehicle_id. Acceptable for a
# single-process demo; see module docstring for why this isn't in the DB.
_conversations: dict[str, list] = {}


def _build_system_instruction(db: Session, vehicle_id: str) -> str:
    """Grounds the chat in the car's actual current condition — health
    score, active issues, and driving pattern — so answers reflect
    real data rather than the model guessing."""
    health = calculate_real_health_score(db, vehicle_id)
    mechanic_report = get_invisible_mechanic_report(db, vehicle_id)
    driver_score = mechanic_report.get("driver_score")

    issues_text = "; ".join(i["message"] for i in health["issues"]) if health["issues"] else "none"
    warnings_text = "; ".join(w["message"] for w in health["warnings"]) if health["warnings"] else "none"
    driver_text = (
        f"{driver_score['style']} ({driver_score['harsh_pct']}% harsh events)"
        if driver_score else "not enough data yet"
    )

    status_context = (
        f"Current health score: {health['health_score']}% ({health['status']})\n"
        f"Active issues: {issues_text}\n"
        f"Active warnings: {warnings_text}\n"
        f"Owner's recent driving style: {driver_text}"
    )

    return (
        f"{CAR_PERSONALITY}\n\n"
        "This is a normal, everyday conversation — your owner is just "
        "checking in or asking something casual, not in an emergency. "
        "Be relaxed and friendly.\n\n"
        f"Here's your actual current state:\n{status_context}\n\n"
        "Ground every answer in this real data — if asked about health, "
        "issues, or driving habits, refer to the numbers above rather "
        "than inventing anything. If asked something you genuinely don't "
        "have data for, say so honestly. Keep responses conversational "
        "and brief (1-3 sentences) unless asked for more detail."
    )


def get_conversation(vehicle_id: str = "VEH001") -> list:
    """Returns the existing conversation, seeding a friendly opener if
    this is the first message of the session."""
    if vehicle_id not in _conversations:
        _conversations[vehicle_id] = [
            {"role": "assistant", "content": "Hey! I'm here — what would you like to know?"}
        ]
    return _conversations[vehicle_id]


def send_message(db: Session, vehicle_id: str, user_message: str) -> dict:
    """Sends the owner's message to Gemini, grounded in the car's
    current real health/driving data. Never raises — see
    gemini_client.generate_reply for the graceful-failure contract."""
    conversation = get_conversation(vehicle_id)
    system_instruction = _build_system_instruction(db, vehicle_id)
    result = generate_reply(system_instruction, conversation, user_message)
    _conversations[vehicle_id] = result["conversation"]
    return result


def reset_conversation(vehicle_id: str = "VEH001"):
    """Clears the session — useful for a 'new conversation' button."""
    _conversations.pop(vehicle_id, None)