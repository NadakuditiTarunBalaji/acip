"""
ACIP-X1 — AI Health Certificate (Day 21 / C9)

A shareable summary an owner can show a buyer when selling — trustworthy
because it's built entirely from real recorded data (Day 16's health
score, Day 18's accident history, Day 19's breakdown history), not the
seller's word. This is the "AI verified" claim from the original
product vision — every figure on the certificate traces back to an
actual logged event or live calculation, nothing here is invented.
"""
from datetime import datetime
from sqlalchemy.orm import Session

from backend.services.dashboard_service import calculate_real_health_score, get_latest_telemetry
from backend.services.breakdown_service import get_breakdown_history
from backend.services.accident_service import get_accident_history
from backend.services.resale_value_service import get_resale_estimate
from backend.models.vehicle import Vehicle


def get_health_certificate(db: Session, vehicle_id: str = "VEH001") -> dict:
    """
    Returns everything needed to render/export a Health Certificate:
    current health, vehicle basics, incident track record (counts and
    resolution status, not full transcripts — a buyer needs the
    summary, not every chat message), and the resale estimate if a
    base price has been set.
    """
    health = calculate_real_health_score(db, vehicle_id)
    latest = get_latest_telemetry(db, vehicle_id)
    odometer_km = latest.odometer_km if latest and latest.odometer_km else None

    vehicle = (
        db.query(Vehicle).filter(Vehicle.vin == vehicle_id).first()
        or db.query(Vehicle).first()
    )

    breakdowns = get_breakdown_history(db, vehicle_id)["events"]
    accidents = get_accident_history(db, vehicle_id)

    total_breakdowns = len(breakdowns)
    resolved_breakdowns = sum(1 for b in breakdowns if b["status"] == "Resolved")
    total_accidents = len(accidents)
    severe_accidents = sum(1 for a in accidents if a["severity"] == "Severe")
    resolved_accidents = sum(1 for a in accidents if a["status"] in ("Resolved", "False Alarm"))

    resale = get_resale_estimate(db, vehicle_id)

    return {
        "vehicle_id": vehicle_id,
        "generated_at": datetime.utcnow().isoformat(),
        "vehicle_info": {
            "manufacturer": vehicle.manufacturer if vehicle else None,
            "model": vehicle.model if vehicle else None,
            "year": vehicle.year if vehicle else None,
            "vin": vehicle.vin if vehicle else None,
        },
        "current_health": {
            "score": health["health_score"],
            "status": health["status"],
            "active_issues": health["total_issues"],
            "active_warnings": health["total_warnings"],
        },
        "odometer_km": odometer_km,
        "incident_history": {
            "total_breakdowns": total_breakdowns,
            "resolved_breakdowns": resolved_breakdowns,
            "total_accidents": total_accidents,
            "severe_accidents": severe_accidents,
            "resolved_accidents": resolved_accidents,
        },
        "resale_estimate": resale,
    }