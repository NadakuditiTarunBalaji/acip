"""
ACIP-X1 — Breakdown AI Assistance (Day 19 / C5)

If the vehicle breaks down mid-road, this module diagnoses the exact
problem (reusing the same calibration-based checks Day 16's
problem_engine.py already runs — not duplicating that logic), then
lets the owner have a real conversation with an AI assistant grounded
in that diagnosis (see breakdown_chat_service.py), and connects them
to the nearest help.

Trigger: automatic only. check_for_breakdown() runs after every
telemetry post (same pattern as Day 18's check_for_crash) and looks
for the genuine "car physically can't continue" signature: stopped
(speed=0, rpm=0), not deliberately parked-and-charging, and at least
one CRITICAL fault present in problem_engine's checks. A normal red
light or a charging stop never qualifies.

"Nearest help" is simulated — no real towing/garage API exists yet,
so this returns a short, distance-sorted list of nearby service
contacts with realistic Indian contact details, consistent with how
Day 18's nearby-vehicle alerts were real math against simulated
positions rather than a real third-party integration.
"""
import json
import math
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models.vehicle_telemetry import VehicleTelemetry
from backend.models.breakdown_event import BreakdownEvent
from backend.services.dashboard_service import get_latest_telemetry
from backend.services.problem_engine import run_diagnostics

# A handful of simulated nearby service points, offset from the
# vehicle's live GPS position each time a breakdown is reported, the
# same way Day 18 repositions Karthik's demo phone — so "nearest help"
# always has something real (if simulated) to show, regardless of
# where the car has actually driven to.
_SERVICE_TEMPLATES = [
    {"name": "Sri Balaji Auto Care",      "type": "Multi-brand garage", "phone": "+91-9840012345", "offset_km": 1.2},
    {"name": "EV PitStop Service Center", "type": "EV specialist",     "phone": "+91-9884098765", "offset_km": 2.4},
    {"name": "ACIP Roadside Assist",      "type": "Towing & roadside", "phone": "+91-9000111222", "offset_km": 3.1},
]


def _offset_position(lat, lon, offset_km):
    """Same helper pattern as Day 18 — places a point offset_km away from (lat, lon)."""
    lat = lat if lat is not None else 13.0827
    lon = lon if lon is not None else 80.2707
    dlat = offset_km / 111.0
    dlon = offset_km / (111.0 * math.cos(math.radians(lat)))
    return lat + dlat, lon + dlon


def _haversine_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return None
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _diagnose_root_cause(db: Session, vehicle_id: str):
    """
    Reuses Day 16's problem_engine checks rather than re-implementing
    fault detection — pulls out only the critical issues, since those
    are what would actually strand a vehicle.
    """
    diagnostics = run_diagnostics(db, vehicle_id)
    critical_issues = [c for c in diagnostics["checks"] if c["status"] == "critical"]
    return critical_issues, diagnostics


def _build_guidance(critical_issues: list) -> list:
    """
    Turns the diagnosed critical issue(s) into plain-language,
    step-by-step instructions for the owner — the "AI guides owner
    step by step" part of C5. Falls back to general safety steps if
    no specific critical issue was found (e.g. a manually-reported
    breakdown with no clear electrical signature, like a flat tyre).
    """
    if not critical_issues:
        return [
            "Move the vehicle to the side of the road if it's safe to do so.",
            "Turn on your hazard lights so other drivers can see you.",
            "Check for anything visibly wrong — flat tyre, smoke, fluid leaks.",
            "If you can't identify the issue, request nearest help below.",
        ]

    steps = [
        "Move the vehicle to the side of the road if it's safe to do so.",
        "Turn on your hazard lights so other drivers can see you.",
    ]
    top = critical_issues[0]
    category = top["category"]

    if category == "Battery & BMS":
        steps.append(f"Issue identified: {top['title']}. Do not attempt to keep driving — this can damage the battery further.")
        steps.append("Do not attempt to jump-start or fast-charge until a technician inspects the pack.")
    elif "Motor" in category or "Powertrain" in category:
        steps.append(f"Issue identified: {top['title']}. Avoid pressing the accelerator repeatedly — this won't help and may worsen the fault.")
    elif category == "Brakes & Tyres":
        steps.append(f"Issue identified: {top['title']}. Do not continue driving — braking performance may be compromised.")
    elif category == "12V & Auxiliary":
        steps.append(f"Issue identified: {top['title']}. Many onboard systems depend on this — avoid running accessories like AC or infotainment to conserve power.")
    else:
        steps.append(f"Issue identified: {top['title']}.")

    steps.append(f"Recommended fix: {top.get('solution', 'Contact a service center for inspection.')}")
    steps.append("Request nearest help below if you're unable to resolve this yourself.")
    return steps


def _find_nearest_help(vehicle_lat, vehicle_lon):
    """
    Returns simulated nearby service contacts, positioned relative to
    the vehicle's current location and sorted by distance — same
    "real math, simulated data" approach as Day 18's radius alerts.
    """
    results = []
    for svc in _SERVICE_TEMPLATES:
        svc_lat, svc_lon = _offset_position(vehicle_lat, vehicle_lon, svc["offset_km"])
        dist = _haversine_km(vehicle_lat, vehicle_lon, svc_lat, svc_lon)
        results.append({
            "name": svc["name"],
            "type": svc["type"],
            "phone": svc["phone"],
            "distance_km": round(dist, 1) if dist is not None else None,
        })
    results.sort(key=lambda s: s["distance_km"] or 999)
    return results


def check_for_breakdown(db: Session, vehicle_id: str = "VEH001"):
    """
    Automatic detection — call this after every telemetry post, same
    pattern as Day 18's check_for_crash. Only creates a BreakdownEvent
    when the genuine "stranded" signature is present: stopped, not
    charging, and at least one critical fault. A red light or a
    deliberate charging stop never qualifies, since neither has a
    critical fault alongside speed=0.
    """
    t = get_latest_telemetry(db, vehicle_id)
    if t is None:
        return None

    is_stopped = (t.speed or 0) == 0 and (t.rpm or 0) == 0
    is_charging = (t.charging_status or 0) == 1
    if not is_stopped or is_charging:
        return None

    critical_issues, diagnostics = _diagnose_root_cause(db, vehicle_id)
    if not critical_issues:
        return None  # stopped, but nothing critical — likely just parked

    # Avoid creating duplicate events for the same ongoing breakdown —
    # if there's already an unresolved breakdown for this vehicle, skip.
    existing = (
        db.query(BreakdownEvent)
        .filter(BreakdownEvent.vehicle_id == vehicle_id, BreakdownEvent.status == "Active")
        .first()
    )
    if existing:
        return existing

    return _create_breakdown_event(db, vehicle_id, t, critical_issues, trigger="Automatic")


def _create_breakdown_event(db: Session, vehicle_id: str, t: VehicleTelemetry,
                             critical_issues: list, trigger: str):
    guidance = _build_guidance(critical_issues)
    nearest_help = _find_nearest_help(t.gps_lat, t.gps_lon)

    event = BreakdownEvent(
        vehicle_id=vehicle_id,
        detected_at=datetime.utcnow(),
        trigger=trigger,
        gps_lat=t.gps_lat,
        gps_lon=t.gps_lon,
        root_cause_json=json.dumps(critical_issues[0]) if critical_issues else None,
        guidance_json=json.dumps(guidance),
        nearest_help_json=json.dumps(nearest_help),
        status="Active",
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_breakdown_history(db: Session, vehicle_id: str = "VEH001"):
    events = (
        db.query(BreakdownEvent)
        .filter(BreakdownEvent.vehicle_id == vehicle_id)
        .order_by(BreakdownEvent.detected_at.desc())
        .all()
    )
    return {
        "vehicle_id": vehicle_id,
        "events": [
            {
                "id": e.id,
                "vehicle_id": e.vehicle_id,
                "detected_at": e.detected_at,
                "trigger": e.trigger,
                "gps_lat": e.gps_lat,
                "gps_lon": e.gps_lon,
                "root_cause": json.loads(e.root_cause_json) if e.root_cause_json else None,
                "guidance": json.loads(e.guidance_json) if e.guidance_json else [],
                "nearest_help": json.loads(e.nearest_help_json) if e.nearest_help_json else [],
                "conversation": json.loads(e.conversation_json) if e.conversation_json else [],
                "status": e.status,
                "resolved_at": e.resolved_at,
            }
            for e in events
        ],
    }


def get_breakdown_by_id(db: Session, breakdown_id: int):
    """Returns one breakdown event as a plain dict, or None — used by
    the chat endpoints to ground the AI in this specific incident."""
    e = db.query(BreakdownEvent).filter(BreakdownEvent.id == breakdown_id).first()
    if not e:
        return None
    return {
        "id": e.id,
        "vehicle_id": e.vehicle_id,
        "root_cause": json.loads(e.root_cause_json) if e.root_cause_json else None,
        "guidance": json.loads(e.guidance_json) if e.guidance_json else [],
        "nearest_help": json.loads(e.nearest_help_json) if e.nearest_help_json else [],
        "conversation": json.loads(e.conversation_json) if e.conversation_json else [],
        "status": e.status,
    }


def save_conversation(db: Session, breakdown_id: int, conversation: list):
    e = db.query(BreakdownEvent).filter(BreakdownEvent.id == breakdown_id).first()
    if not e:
        return None
    e.conversation_json = json.dumps(conversation)
    db.commit()
    return e


def resolve_breakdown(db: Session, breakdown_id: int):
    event = db.query(BreakdownEvent).filter(BreakdownEvent.id == breakdown_id).first()
    if not event:
        return None
    event.status = "Resolved"
    event.resolved_at = datetime.utcnow()
    db.commit()
    return event