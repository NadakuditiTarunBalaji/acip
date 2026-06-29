"""
ACIP-X1 — Vehicle Situation Detection (Day 20 / unified voice assistant)

A single source of truth for "what's actually happening with this
vehicle right now" — active breakdown, active accident, or normal —
so the unified voice assistant (Talk to Your Car) can ground itself
in whichever situation is real, instead of needing three separate
chat surfaces. Reuses Day 18/19's existing history queries rather
than re-deriving accident/breakdown state.

Priority when multiple things are true: accident takes priority over
breakdown (a crash is more urgent than a stop-and-diagnose), and
either takes priority over normal chat.
"""
from sqlalchemy.orm import Session

from backend.services.breakdown_service import get_breakdown_history
from backend.services.accident_service import get_accident_history
from backend.services.dashboard_service import calculate_real_health_score
from backend.services.invisible_mechanic_service import get_invisible_mechanic_report

ACCIDENT_ACTIVE_STATUSES = ("Detected", "Notified")
BREAKDOWN_ACTIVE_STATUS = "Active"


def get_current_situation(db: Session, vehicle_id: str = "VEH001") -> dict:
    """
    Returns {"type": "accident"|"breakdown"|"normal", "data": {...}} —
    data's shape depends on type:
      - accident: the active AccidentEvent dict
      - breakdown: the active BreakdownEvent dict
      - normal: {"health": ..., "driver_score": ...}
    """
    accidents = get_accident_history(db, vehicle_id, limit=5)
    active_accident = next((a for a in accidents if a["status"] in ACCIDENT_ACTIVE_STATUSES), None)
    if active_accident:
        return {"type": "accident", "data": active_accident}

    breakdowns = get_breakdown_history(db, vehicle_id)
    active_breakdown = next(
        (b for b in breakdowns["events"] if b["status"] == BREAKDOWN_ACTIVE_STATUS), None
    )
    if active_breakdown:
        return {"type": "breakdown", "data": active_breakdown}

    health = calculate_real_health_score(db, vehicle_id)
    mechanic_report = get_invisible_mechanic_report(db, vehicle_id)
    return {
        "type": "normal",
        "data": {"health": health, "driver_score": mechanic_report.get("driver_score")},
    }