"""
ACIP-X1 — AI Car Personality, Proactive Messages (Day 20 / C6)

The car proactively greets its owner and comments on real trends in
its own data — not just answering when asked (that's the chat in
car_chat_service.py). This reuses Day 16's health score and Day 17's
driver-score/harsh-event data rather than re-deriving any of it, so
every "personality" observation is grounded in something the rest of
the dashboard already computed and displays elsewhere.

These messages are generated fresh each time get_proactive_messages()
is called (e.g. on dashboard load) — there's no need to persist them,
since they're derived live from current telemetry/health state and
should always reflect the car's current condition, not a stale snapshot.
"""
from datetime import datetime
from sqlalchemy.orm import Session

from backend.services.dashboard_service import calculate_real_health_score
from backend.services.invisible_mechanic_service import get_invisible_mechanic_report


def _time_of_day_greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


def _health_greeting_message(health: dict) -> str:
    """A greeting that reflects the car's actual current health score,
    not a generic 'hello' — this is the 'Good morning! Your car is
    100% healthy today' example from the original product vision."""
    greeting = _time_of_day_greeting()
    score = health["health_score"]
    status = health["status"]  # one of: Healthy, Warning, Poor, Critical

    if status == "Healthy":
        return f"{greeting}! I'm feeling great today — {score}% healthy. Have a safe drive!"
    elif status == "Warning":
        return (
            f"{greeting}. I'm at {score}% health right now — a few things could use "
            f"attention when you get a chance. Check the Alerts tab for details."
        )
    else:  # Poor or Critical
        return (
            f"{greeting}. I need to flag something — my health is down to {score}% "
            f"({status}). Please take a look at the Alerts tab before your next drive."
        )


def _driving_habit_message(driver_score: dict) -> str | None:
    """
    Reuses Day 17's already-computed driver_score (style + harsh event
    %) to comment on the owner's driving pattern — only speaks up if
    there's something genuinely worth noting, rather than commenting
    every single time.
    """
    if driver_score["samples"] < 20:
        return None  # not enough data yet to say anything meaningful

    style = driver_score["style"]
    harsh_pct = driver_score["harsh_pct"]

    if style == "Aggressive":
        return (
            f"I've noticed quite a bit of hard acceleration and braking lately "
            f"({harsh_pct}% of recent driving) — smoother inputs would help my "
            f"brakes and tyres last longer, and you'd get more range too."
        )
    elif style == "Smooth & Efficient":
        return "Your driving's been really smooth lately — that's easy on me and great for range. Thank you!"
    return None  # "Moderate" — nothing notable enough to mention proactively


def get_proactive_messages(db: Session, vehicle_id: str = "VEH001") -> dict:
    """
    Returns the car's proactive personality messages for right now:
    always a health-aware greeting, plus an optional driving-habit
    observation if the recent data shows something worth mentioning.
    """
    health = calculate_real_health_score(db, vehicle_id)
    mechanic_report = get_invisible_mechanic_report(db, vehicle_id)
    driver_score = mechanic_report.get("driver_score")

    messages = [_health_greeting_message(health)]

    if driver_score:
        habit_msg = _driving_habit_message(driver_score)
        if habit_msg:
            messages.append(habit_msg)

    return {
        "vehicle_id": vehicle_id,
        "messages": messages,
        "health_score": health["health_score"],
        "status": health["status"],
    }