"""
ACIP-X1 — Unified Voice Assistant (Day 20 / single conversational surface)

Replaces having three separate AI chat surfaces (breakdown chat,
general car chat) with ONE conversation that's grounded in whatever
is actually happening with the vehicle right now — accident,
breakdown, or normal — determined by vehicle_situation_service.py.

The owner always talks to the same "car" in the same place; what the
car says is shaped by real data, not by which tab they happened to open.

Conversation is kept in-memory per vehicle (see car_chat_service.py's
docstring for the same reasoning — this is a live session, not a
permanent record like a BreakdownEvent or AccidentEvent, which already
separately persist their own incident data).
"""
from datetime import datetime
from sqlalchemy.orm import Session

from backend.services.gemini_client import generate_reply, CAR_PERSONALITY
from backend.services.vehicle_situation_service import get_current_situation

_conversations: dict[str, list] = {}
_last_situation_type: dict[str, str] = {}


def _build_accident_instruction(accident: dict) -> str:
    severity = accident["severity"]
    contacts_notified = accident.get("contacts_notified") or []
    sms_results = accident.get("sms_results") or {}
    total_sent = sms_results.get("total_sent", 0)
    total_attempted = sms_results.get("total_attempted", 0)
    sms_enabled = sms_results.get("sms_enabled", False)

    if not sms_enabled:
        contacts_text = (
            "IMPORTANT: SMS notifications are not configured on this system — "
            "your emergency contacts have NOT been notified. You must tell the "
            "owner this clearly and urge them to call their emergency contacts "
            "or emergency services themselves right now."
        )
    elif total_sent == 0 and total_attempted > 0:
        contacts_text = (
            f"IMPORTANT: I attempted to notify {total_attempted} contact(s) by SMS, "
            "but ALL of those messages FAILED to send. Your emergency contacts have "
            "NOT actually been reached. You must tell the owner this clearly and "
            "urge them to call their emergency contacts or emergency services "
            "themselves right now — do not claim they've been notified."
        )
    elif total_sent < total_attempted:
        contacts_text = (
            f"I successfully notified {total_sent} of {total_attempted} attempted "
            "contact(s) by SMS — but not all of them. Tell the owner which ones "
            "may not have gotten through and suggest they also call directly if "
            "possible."
        )
    elif contacts_notified:
        contacts_text = f"I've successfully notified {total_sent} emergency contact(s) by SMS."
    else:
        contacts_text = "No emergency contacts are configured for this vehicle."

    return (
        f"{CAR_PERSONALITY}\n\n"
        "URGENT: You have just detected a crash/accident. This is the single "
        "most serious situation you can be in. Drop all playfulness — be "
        "calm, direct, and focused entirely on your owner's safety.\n\n"
        f"Crash severity detected: {severity}\n"
        f"{contacts_text}\n\n"
        "Never claim a notification succeeded unless explicitly told it did "
        "above — if it failed, say so plainly and urge the owner to act "
        "themselves; their safety depends on accurate information, not "
        "reassurance that isn't true.\n\n"
        "Your first priority: check if they're okay and able to respond. "
        "If they seem hurt or confused, urge them to call emergency services "
        "directly (police/ambulance) — don't let politeness slow that down. "
        "If they're okay, reassure them, confirm what you've already done "
        "(notified contacts), and ask if they need anything else. Keep "
        "responses short (1-3 sentences) — this is not the moment for long "
        "explanations."
    )


def _build_breakdown_instruction(breakdown: dict) -> str:
    root_cause = breakdown.get("root_cause")
    nearest_help = breakdown.get("nearest_help") or []

    if root_cause:
        fault_context = (
            f"Diagnosed issue: {root_cause['title']}\n"
            f"Details: {root_cause['problem']}\n"
            f"Recommended fix: {root_cause.get('solution', 'Not specified')}\n"
            f"Estimated cost: {root_cause.get('cost', 'Not specified')}"
        )
    else:
        fault_context = (
            "No specific electrical fault was detected — this may be "
            "mechanical (e.g. a flat tyre) or something sensors can't catch."
        )

    if nearest_help:
        nearest = nearest_help[0]
        help_context = (
            f"Nearest help: {nearest['name']} ({nearest['type']}), "
            f"{nearest['distance_km']} km away, phone {nearest['phone']}. "
            f"Other options are also available if asked."
        )
    else:
        help_context = "No nearby help options found yet."

    return (
        f"{CAR_PERSONALITY}\n\n"
        "You have just broken down. Your owner may be stressed or in an "
        "unfamiliar location — this is serious and practical, so dial back "
        "playfulness and prioritize being calm, clear, and reassuring.\n\n"
        f"{fault_context}\n"
        f"{help_context}\n\n"
        "Proactively mention the nearest help and that you can discuss "
        "distance/contacting them if relevant — don't make them ask first. "
        "If asked about ETA, give an honest estimate based on the distance "
        "(typical city driving ~25-30 km/h for a tow truck/mechanic) but "
        "make clear it's an estimate, not a guarantee. Keep responses "
        "concise (2-4 sentences) unless asked for more detail. Never invent "
        "technical details not given above."
    )


def _build_normal_instruction(normal_data: dict) -> str:
    health = normal_data["health"]
    driver_score = normal_data.get("driver_score")

    issues_text = "; ".join(i["message"] for i in health["issues"]) if health["issues"] else "none"
    warnings_text = "; ".join(w["message"] for w in health["warnings"]) if health["warnings"] else "none"
    driver_text = (
        f"{driver_score['style']} ({driver_score['harsh_pct']}% harsh events)"
        if driver_score else "not enough data yet"
    )

    current_dt = datetime.now().strftime("%A, %B %d, %Y · %H:%M")

    status_context = (
        f"Current date and time: {current_dt}\n"
        f"Current health score: {health['health_score']}% ({health['status']})\n"
        f"Active issues: {issues_text}\n"
        f"Active warnings: {warnings_text}\n"
        f"Owner's recent driving style: {driver_text}"
    )

    return (
        f"{CAR_PERSONALITY}\n\n"
        "This is a normal, everyday conversation — your owner is just "
        "checking in or asking something casual, not in an emergency. "
        "Be relaxed and friendly, like a knowledgeable friend, not a "
        "rigid system. If asked something simple and ordinary — like "
        "today's date, the time, or general chitchat — just answer it "
        "naturally using the real date/time given below; don't refuse "
        "or act like you don't know just because it's not a 'vehicle' "
        "fact.\n\n"
        f"Here's your actual current state:\n{status_context}\n\n"
        "Ground every answer about health, issues, or driving habits in "
        "the real numbers above rather than inventing anything. Keep "
        "responses conversational and brief (1-3 sentences) unless "
        "asked for more detail."
    )


def _build_system_instruction(situation: dict) -> str:
    if situation["type"] == "accident":
        return _build_accident_instruction(situation["data"])
    elif situation["type"] == "breakdown":
        return _build_breakdown_instruction(situation["data"])
    else:
        return _build_normal_instruction(situation["data"])


def _opener_for_situation(situation: dict) -> str:
    """The first thing the car says when the conversation starts or
    when the situation has changed since the last message — so a
    breakdown or crash is announced rather than silently waited on."""
    if situation["type"] == "accident":
        severity = situation["data"]["severity"]
        sms_results = situation["data"].get("sms_results") or {}
        total_sent = sms_results.get("total_sent", 0)
        total_attempted = sms_results.get("total_attempted", 0)
        sms_enabled = sms_results.get("sms_enabled", False)

        if sms_enabled and total_sent > 0 and total_sent == total_attempted:
            contact_status = "I've already alerted your emergency contacts."
        elif sms_enabled and total_sent > 0:
            contact_status = f"I reached {total_sent} of your emergency contacts, but not all of them."
        else:
            contact_status = (
                "I tried to alert your emergency contacts but the messages "
                "didn't go through — please call them or emergency services "
                "yourself if you can."
            )
        return (
            f"I've detected a {severity.lower()} impact. {contact_status} "
            f"Are you okay? Please talk to me."
        )
    elif situation["type"] == "breakdown":
        root_cause = situation["data"].get("root_cause")
        nearest_help = situation["data"].get("nearest_help") or []
        if root_cause:
            opener = f"I've stopped — {root_cause['title'].lower()}. {root_cause['problem']}"
        else:
            opener = "I've reported a breakdown but couldn't pinpoint a specific fault."
        if nearest_help:
            nearest = nearest_help[0]
            opener += f" The nearest help is {nearest['name']}, about {nearest['distance_km']} km away."
        return opener + " What would you like to know?"
    else:
        return "Hey! I'm here — what would you like to know?"


def get_conversation(db: Session, vehicle_id: str = "VEH001") -> dict:
    """
    Returns the current conversation. If the situation has changed
    since the last call (e.g. normal -> breakdown, or breakdown ->
    accident), resets the conversation with a fresh opener for the
    new situation — the owner shouldn't have to notice and restart
    manually when something serious just happened.
    """
    situation = get_current_situation(db, vehicle_id)
    situation_type = situation["type"]
    previous_type = _last_situation_type.get(vehicle_id)

    if vehicle_id not in _conversations or previous_type != situation_type:
        _conversations[vehicle_id] = [
            {"role": "assistant", "content": _opener_for_situation(situation)}
        ]
        _last_situation_type[vehicle_id] = situation_type

    return {"situation_type": situation_type, "conversation": _conversations[vehicle_id]}


def send_message(db: Session, vehicle_id: str, user_message: str) -> dict:
    """Sends the owner's message to Gemini, grounded in whatever
    situation is currently real for this vehicle. Never raises — see
    gemini_client.generate_reply for the graceful-failure contract."""
    state = get_conversation(db, vehicle_id)
    situation = get_current_situation(db, vehicle_id)
    system_instruction = _build_system_instruction(situation)

    # Only send the most recent messages to Gemini — a long chat session
    # otherwise resends its ENTIRE history on every single message, which
    # measurably slows down response time as the conversation grows. The
    # full history is still stored and shown to the user; only the API
    # call itself gets the trimmed window.
    _RECENT_HISTORY_LIMIT = 12
    recent_history = state["conversation"][-_RECENT_HISTORY_LIMIT:]

    result = generate_reply(system_instruction, recent_history, user_message)
    full_conversation = state["conversation"] + result["conversation"][len(recent_history):]
    _conversations[vehicle_id] = full_conversation
    return {
        "situation_type": situation["type"],
        "conversation": full_conversation,
        "ai_available": result["ai_available"],
    }


def reset_conversation(vehicle_id: str = "VEH001"):
    _conversations.pop(vehicle_id, None)
    _last_situation_type.pop(vehicle_id, None)