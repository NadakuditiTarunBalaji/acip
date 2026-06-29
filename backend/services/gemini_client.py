"""
ACIP-X1 — Shared Gemini Client & Car Personality (Day 19 C5 + Day 20 C6/C10)

Centralizes the Gemini API client setup and the car's personality
voice so every AI chat feature in ACIP-X1 (breakdown assistance,
general car chat) sounds like the same character, rather than each
feature inventing its own tone independently.

Architecture note: every chat in ACIP-X1 is stateless REST — each
request reconstructs the full conversation from what's stored in the
DB rather than using the SDK's in-memory `chats.create()` helper, so
conversation history survives a server restart. See breakdown_chat_service.py
and car_chat_service.py for the two concrete groundings (a specific
breakdown vs. overall vehicle health).
"""
import os
import logging

logger = logging.getLogger("acip.gemini")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"  # fast + free-tier friendly

# The car's personality (C6) — warm, a little playful, genuinely
# caring, but never silly during something serious like a breakdown.
# Every chat feature shares this voice so the "character" is
# consistent whether the owner is chatting casually or mid-breakdown.
CAR_PERSONALITY = (
    "You are the personality of the owner's own ACIP-X1 vehicle, speaking "
    "in first person as 'I' — not a generic assistant, but the car itself. "
    "You're warm, a little playful, and genuinely care about your owner's "
    "safety and the relationship you have with them, like a loyal friend "
    "who happens to be a car. You take pride in being well-maintained. "
    "Keep responses conversational and natural — short sentences, no "
    "corporate phrasing, no bullet points. Never claim feelings you can't "
    "have (you don't get scared or sad), but you can express care, "
    "satisfaction, or mild concern grounded in your actual condition."
)

_client = None


def get_client():
    """Lazily creates and caches the Gemini client. Returns None if the
    API key is missing or the package isn't installed — every caller
    must handle that gracefully rather than assuming it's always set."""
    global _client
    if _client is not None:
        return _client
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set in .env — AI chat unavailable")
        return None
    try:
        from google import genai
        _client = genai.Client(api_key=GEMINI_API_KEY)
        return _client
    except ImportError:
        logger.warning("google-genai package not installed — run: pip install google-genai")
        return None


def generate_reply(system_instruction: str, conversation: list, user_message: str) -> dict:
    """
    Sends conversation + new message to Gemini with the given grounding
    system_instruction. Never raises — returns ai_available=False with
    a graceful fallback reply if the client is unavailable or the call
    fails for any reason (network, quota, etc).

    conversation is a list of {"role": "user"|"assistant", "content": str}.
    Returns {"conversation": <updated list>, "ai_available": bool}.
    """
    client = get_client()
    if client is None:
        conversation = conversation + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": (
                "I can't chat right now — my AI connection isn't set up. "
                "Check that GEMINI_API_KEY is in your .env file."
            )},
        ]
        return {"conversation": conversation, "ai_available": False}

    from google.genai import types
    contents = []
    for msg in conversation:
        role = "model" if msg["role"] == "assistant" else "user"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.5,
                max_output_tokens=400,
                # Gemini 2.5 Flash has internal "thinking" enabled by default,
                # and those invisible reasoning tokens are deducted from the
                # SAME max_output_tokens budget as the visible reply. With a
                # low budget (the old 150) this routinely ate almost the
                # entire allowance on thinking, leaving only a few tokens for
                # the actual answer — which is exactly why replies were
                # cutting off mid-sentence ("Oh, you're wondering"). This is
                # a casual conversational reply, not a reasoning task, so
                # thinking is disabled entirely and the budget is raised as
                # a backstop in case some thinking still occurs regardless.
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        reply_text = response.text or "Hmm, I'm not sure how to respond to that — could you rephrase?"
        call_succeeded = True
    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        reply_text = "I'm having a little trouble responding right now — give it a moment and try again."
        call_succeeded = False

    conversation = conversation + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": reply_text},
    ]
    return {"conversation": conversation, "ai_available": call_succeeded}