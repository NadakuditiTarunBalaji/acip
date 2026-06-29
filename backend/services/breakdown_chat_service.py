"""
ACIP-X1 — Breakdown Chat Assistant (Day 19 / C5)

Lets the owner have a real conversation with an AI assistant during a
breakdown, grounded in the actual diagnosed fault rather than generic
advice. Uses the shared Gemini client and car personality voice (see
gemini_client.py) so this sounds like the same "character" as the
general car chat (Day 20 / C6+C10), not a separate cold support bot.
"""
from backend.services.gemini_client import generate_reply, CAR_PERSONALITY


def _build_system_instruction(breakdown_event: dict) -> str:
    """
    Grounds every response in the actual diagnosed fault for this
    specific breakdown — not a generic 'you're a helpful car assistant'
    prompt. root_cause may be None (e.g. a fault-free stop), in which
    case the assistant is told that explicitly rather than inventing one.
    """
    root_cause = breakdown_event.get("root_cause")
    if root_cause:
        fault_context = (
            f"Diagnosed issue: {root_cause['title']}\n"
            f"Details: {root_cause['problem']}\n"
            f"Recommended fix: {root_cause.get('solution', 'Not specified')}\n"
            f"Estimated cost: {root_cause.get('cost', 'Not specified')}\n"
            f"Impact if ignored: {root_cause.get('impact', 'Not specified')}"
        )
    else:
        fault_context = (
            "No specific electrical fault was detected by your diagnostics. "
            "The breakdown may be mechanical (e.g. a flat tyre) or something "
            "your sensors can't directly detect."
        )

    return (
        f"{CAR_PERSONALITY}\n\n"
        "Right now you have just broken down and your owner may be "
        "stressed or in an unfamiliar location — this is a serious, "
        "practical moment, so dial back the playfulness and prioritize "
        "being calm, clear, and reassuring.\n\n"
        f"{fault_context}\n\n"
        "Ground every answer in this specific diagnosis. If asked something "
        "unrelated to the breakdown, gently redirect back to helping right "
        "now. Keep responses concise (2-4 sentences) unless the owner asks "
        "for more detail. Never invent technical details not given above — "
        "if you don't know something specific, say so and suggest they "
        "confirm with a technician."
    )


def get_or_start_conversation(breakdown_event: dict) -> list:
    """
    Returns the existing conversation if one exists, or seeds a new one
    with an opening message from the assistant — the owner's first
    experience should feel like the assistant already knows what
    happened, not an empty chat box.
    """
    existing = breakdown_event.get("conversation")
    if existing:
        return existing

    root_cause = breakdown_event.get("root_cause")
    if root_cause:
        opener = (
            f"Hey — I've stopped myself because {root_cause['title'].lower()}. "
            f"{root_cause['problem']} What would you like to know?"
        )
    else:
        opener = (
            "I've reported a breakdown but couldn't pinpoint a specific "
            "electrical fault — this might be something like a flat tyre. "
            "Tell me what you're noticing and I'll try to help."
        )

    return [{"role": "assistant", "content": opener}]


def send_message(breakdown_event: dict, conversation: list, user_message: str) -> dict:
    """Sends the owner's message to Gemini, grounded in this breakdown's
    diagnosed fault. Never raises — see generate_reply for the
    graceful-failure contract."""
    system_instruction = _build_system_instruction(breakdown_event)
    return generate_reply(system_instruction, conversation, user_message)