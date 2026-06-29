"""
ACIP-X1 — Accident Detection + Emergency Response (Day 18 / C4)

Detection: every incoming telemetry sample's G-force (accel_x/y/z) is
checked against a crash threshold. Normal driving — even hard braking
or aggressive cornering — stays well under 1g combined; the Invisible
Mechanic feature (C7) already flags "harsh" events above ~0.3g. A real
collision produces a sharp spike well above that, typically several g's
within milliseconds. We use a threshold of 3.5g combined (net of the
resting ~1g gravity on accel_z) as "Moderate" and 6.0g+ as "Severe" —
comfortably above anything normal driving (or the simulator's current
driving cycle) would produce, while still being demoable by manually
posting a high-G telemetry sample.

Response, once a crash is detected:
    1. Log an AccidentEvent with location, speed, G-force, severity.
    2. "Notify" emergency contacts for that vehicle (simulated — no real
       SMS/call gateway exists, so this records who *would* be contacted
       and in what order, which is what the dashboard displays).
    3. "Alert" anyone within a 1km radius — both other vehicles (other
       vehicle_ids present in telemetry) and any phones running the app
       that have shared their location (NearbyDevice) — by checking real
       GPS positions against the crash location, not a hardcoded list.

This module never raises on missing data — if a vehicle has no GPS fix
or no emergency contacts configured yet, it degrades gracefully and
reports that rather than failing.
"""
import json
import math
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models.vehicle_telemetry import VehicleTelemetry
from backend.models.emergency_contact import EmergencyContact
from backend.models.accident_event import AccidentEvent
from backend.models.nearby_device import NearbyDevice
from backend.services.sms_service import send_crash_alerts

MODERATE_G_THRESHOLD = 3.5
SEVERE_G_THRESHOLD = 6.0
RESTING_Z_G = 1.0          # accel_z reads ~1.0g at rest due to gravity
ALERT_RADIUS_KM = 1.0


def _haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two GPS points, in kilometers."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_combined_g(accel_x, accel_y, accel_z):
    """
    Combined G-force magnitude, net of the resting 1g on the vertical
    axis so a stationary car reads ~0g rather than ~1g.
    """
    ax = accel_x or 0.0
    ay = accel_y or 0.0
    az = (accel_z or RESTING_Z_G) - RESTING_Z_G
    return math.sqrt(ax ** 2 + ay ** 2 + az ** 2)


def check_for_crash(db: Session, telemetry: VehicleTelemetry, is_demo: bool = False):
    """
    Called after every telemetry sample is stored. Returns the created
    AccidentEvent if a crash was detected, otherwise None.
    """
    combined_g = compute_combined_g(telemetry.accel_x, telemetry.accel_y, telemetry.accel_z)

    if combined_g < MODERATE_G_THRESHOLD:
        return None

    severity = "Severe" if combined_g >= SEVERE_G_THRESHOLD else "Moderate"

    event = AccidentEvent(
        vehicle_id=telemetry.vehicle_id,
        detected_at=datetime.utcnow(),
        gps_lat=telemetry.gps_lat,
        gps_lon=telemetry.gps_lon,
        speed_at_impact=telemetry.speed,
        combined_g_force=round(combined_g, 2),
        accel_x=telemetry.accel_x,
        accel_y=telemetry.accel_y,
        accel_z=telemetry.accel_z,
        severity=severity,
        status="Detected",
        is_demo=is_demo,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    _respond_to_crash(db, event)
    return event


def _respond_to_crash(db: Session, event: AccidentEvent):
    """Simulates the emergency-response actions and records what happened."""
    contacts_notified = _notify_emergency_contacts(db, event)
    nearby_alerted = _alert_nearby_devices(db, event)

    event.contacts_notified_json = json.dumps(contacts_notified)
    event.nearby_vehicles_alerted_json = json.dumps(nearby_alerted)

    # Best-effort real SMS — failures here (no credentials, no network,
    # unverified number, etc.) are caught inside sms_service itself and
    # never raised, so they can never prevent the event from being
    # marked Notified or block the rest of the response.
    try:
        sms_summary = send_crash_alerts(
            contacts_notified, nearby_alerted, event.severity, event.gps_lat, event.gps_lon
        )
        event.sms_results_json = json.dumps(sms_summary)
    except Exception as e:
        event.sms_results_json = json.dumps({"sms_enabled": False, "error": str(e)})

    event.status = "Notified"
    db.commit()


def _notify_emergency_contacts(db: Session, event: AccidentEvent):
    contacts = (
        db.query(EmergencyContact)
        .filter(EmergencyContact.vehicle_id == event.vehicle_id)
        .order_by(EmergencyContact.priority.asc())
        .all()
    )
    notified = []
    for c in contacts:
        notified.append({
            "name": c.name,
            "relationship": c.relationship,
            "phone": c.phone,
            "channel": "SMS + Call (simulated)",
        })
    return notified


def _alert_nearby_devices(db: Session, event: AccidentEvent):
    """
    Find anyone within ALERT_RADIUS_KM of the crash location and alert
    them — both other vehicles (other vehicle_ids with telemetry) and
    phones running the app that have shared their GPS location
    (NearbyDevice). Real radius math against real stored data in both
    cases; nothing here is hardcoded to "always show an alert."
    """
    if event.gps_lat is None or event.gps_lon is None:
        return []

    alerted = []

    # ── Other vehicles ───────────────────────────────────
    other_vehicle_ids = (
        db.query(VehicleTelemetry.vehicle_id)
        .filter(VehicleTelemetry.vehicle_id != event.vehicle_id)
        .distinct()
        .all()
    )
    for (vid,) in other_vehicle_ids:
        latest = (
            db.query(VehicleTelemetry)
            .filter(VehicleTelemetry.vehicle_id == vid)
            .order_by(VehicleTelemetry.timestamp.desc())
            .first()
        )
        if not latest:
            continue
        dist = _haversine_km(event.gps_lat, event.gps_lon, latest.gps_lat, latest.gps_lon)
        if dist is not None and dist <= ALERT_RADIUS_KM:
            alerted.append({
                "type": "vehicle",
                "name": vid,
                "distance_km": round(dist, 3),
            })

    # ── Nearby phones running the app ────────────────────
    devices = db.query(NearbyDevice).all()
    for d in devices:
        dist = _haversine_km(event.gps_lat, event.gps_lon, d.gps_lat, d.gps_lon)
        if dist is not None and dist <= ALERT_RADIUS_KM:
            alerted.append({
                "type": "phone",
                "name": d.owner_name,
                "phone": d.phone,
                "distance_km": round(dist, 3),
            })

    # Closest first
    alerted.sort(key=lambda a: a["distance_km"])
    return alerted


def get_accident_history(db: Session, vehicle_id: str = "VEH001", limit: int = 20):
    events = (
        db.query(AccidentEvent)
        .filter(AccidentEvent.vehicle_id == vehicle_id)
        .order_by(AccidentEvent.detected_at.desc())
        .limit(limit)
        .all()
    )
    result = []
    for e in events:
        result.append({
            "id": e.id,
            "vehicle_id": e.vehicle_id,
            "detected_at": e.detected_at,
            "gps_lat": e.gps_lat,
            "gps_lon": e.gps_lon,
            "speed_at_impact": e.speed_at_impact,
            "combined_g_force": e.combined_g_force,
            "accel_x": e.accel_x,
            "accel_y": e.accel_y,
            "accel_z": e.accel_z,
            "severity": e.severity,
            "status": e.status,
            "is_demo": e.is_demo,
            "contacts_notified": json.loads(e.contacts_notified_json) if e.contacts_notified_json else [],
            "nearby_vehicles_alerted": json.loads(e.nearby_vehicles_alerted_json) if e.nearby_vehicles_alerted_json else [],
            "sms_results": json.loads(e.sms_results_json) if e.sms_results_json else None,
            "resolved_at": e.resolved_at,
        })
    return result


def resolve_accident(db: Session, accident_id: int, mark_as: str = "Resolved"):
    event = db.query(AccidentEvent).filter(AccidentEvent.id == accident_id).first()
    if not event:
        return None
    event.status = mark_as
    event.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(event)
    return event