"""
ACIP-X1 — Predictive Alerts (Day 17 / C3)

This is distinct from both:
  - C2 (Problem/Solution/Cost): reacts to TODAY'S snapshot crossing a safety limit
  - C7 (Invisible Mechanic):     explains a TREND and projects forward, as
                                  informational insight cards you have to go read

C3 takes those same forward projections and re-frames them as ALERTS —
each one tagged with an urgency tier (Soon / Monitor / Fine) based on how
close the projected date/distance is, so a vehicle owner gets a clear,
notification-style answer to "is there anything I should actually act on
soon?" without having to read every insight and do the mental math
themselves.

Urgency tiers (estimated time until the threshold is reached):
    SOON     -> within ~60 days        -> should act / book a service soon
    MONITOR  -> within ~60-365 days    -> not urgent, but worth tracking
    FINE     -> beyond ~365 days       -> no concern, shown for transparency
"""
from sqlalchemy.orm import Session
from backend.services.invisible_mechanic_service import get_invisible_mechanic_report

SOON_DAYS = 60
MONITOR_DAYS = 365
ASSUMED_KM_PER_DAY = 40  # same assumption used in invisible_mechanic_service


def _alert(alert_id, category, severity, title, message, action, days_until=None, eta_km=None):
    return {
        "id": alert_id,
        "category": category,
        "severity": severity,          # "soon" | "monitor" | "fine"
        "title": title,
        "message": message,
        "action": action,
        "days_until": round(days_until, 0) if days_until is not None else None,
        "eta_km": round(eta_km, 0) if eta_km is not None else None,
    }


def _severity_from_days(days_until):
    if days_until is None:
        return "fine"
    if days_until <= SOON_DAYS:
        return "soon"
    if days_until <= MONITOR_DAYS:
        return "monitor"
    return "fine"


def _extract_km_remaining(prediction_text, observation_text):
    """
    Invisible Mechanic insights carry their projection inside a human-readable
    sentence rather than a raw number. We re-derive the underlying remaining-km
    figure here by re-reading the same telemetry math via the report's insight
    IDs, rather than parsing the sentence — see get_predictive_alerts() below,
    which pulls the structured numbers directly instead of this helper.
    """
    return None  # kept as a placeholder; structured extraction happens below


def get_predictive_alerts(db: Session, vehicle_id: str = "VEH001") -> dict:
    im_report = get_invisible_mechanic_report(db, vehicle_id)

    if im_report["samples_used"] == 0:
        return {
            "vehicle_id": vehicle_id,
            "samples_used": 0,
            "alerts": [],
            "summary": {"soon": 0, "monitor": 0, "fine": 0, "total": 0},
        }

    alerts = []

    # We recompute the same underlying remaining-km/remaining-days figures
    # that invisible_mechanic_service derives internally, so each alert here
    # carries a real days_until value to sort/tier by — rather than trying to
    # parse them back out of the prose sentences in `insights`.
    from backend.models.vehicle_telemetry import VehicleTelemetry

    history = (
        db.query(VehicleTelemetry)
        .filter(VehicleTelemetry.vehicle_id == vehicle_id)
        .order_by(VehicleTelemetry.id.desc())
        .limit(150)
        .all()
    )
    newest = history[0]
    oldest = history[-1]

    # ── Brake pad alert ──────────────────────────────────────
    BRAKE_THRESHOLD = 80.0
    TYPICAL_BRAKE_LIFE_KM = 30000
    current_wear = newest.brake_pad_wear_pct or 0
    delta_wear = (newest.brake_pad_wear_pct or 0) - (oldest.brake_pad_wear_pct or 0)
    delta_odo = (newest.odometer_km or 0) - (oldest.odometer_km or 0)
    remaining_pct = max(0, BRAKE_THRESHOLD - current_wear)

    if delta_odo > 0.05 and delta_wear > 0:
        wear_rate_per_km = delta_wear / delta_odo
        remaining_km = remaining_pct / wear_rate_per_km if wear_rate_per_km > 0 else float("inf")
    else:
        typical_rate_per_km = BRAKE_THRESHOLD / TYPICAL_BRAKE_LIFE_KM
        remaining_km = remaining_pct / typical_rate_per_km if typical_rate_per_km > 0 else float("inf")

    days_until = (remaining_km / ASSUMED_KM_PER_DAY) if remaining_km != float("inf") else None
    severity = _severity_from_days(days_until)
    if remaining_pct <= 0:
        msg = f"Brake pads are at {current_wear:.0f}% wear — at or past the {BRAKE_THRESHOLD:.0f}% replacement point."
        action = "Book a brake inspection / pad replacement now."
        severity = "soon"
    elif severity == "soon":
        msg = f"Brake pads are at {current_wear:.0f}% wear and projected to need replacement within about {days_until:.0f} days."
        action = "Book a brake inspection / pad replacement soon."
    elif severity == "monitor":
        msg = f"Brake pads are at {current_wear:.0f}% wear, projected to reach the replacement point in roughly {days_until:.0f} days."
        action = "No action yet — keep an eye on it at your next routine service."
    else:
        msg = f"Brake pads are at {current_wear:.0f}% wear with no near-term concern."
        action = "No action needed."
    alerts.append(_alert("BRAKE_PAD_ALERT", "Brakes", severity,
                          "Brake Pad Replacement Outlook", msg, action,
                          days_until=days_until, eta_km=remaining_km if remaining_km != float("inf") else None))

    # ── Battery SOH alert ────────────────────────────────────
    SOH_THRESHOLD = 80.0
    TYPICAL_SOH_KM = 150000
    soh = newest.soh or 100
    odo = newest.odometer_km or 0
    degraded_so_far = 100 - soh

    if degraded_so_far > 0.01 and odo > 0:
        degradation_rate_per_km = degraded_so_far / odo
        remaining_degradation = max(0, soh - SOH_THRESHOLD)
        remaining_km = remaining_degradation / degradation_rate_per_km if degradation_rate_per_km > 0 else float("inf")
    else:
        remaining_km = max(0, TYPICAL_SOH_KM - odo)

    days_until = (remaining_km / ASSUMED_KM_PER_DAY) if remaining_km != float("inf") else None
    severity = _severity_from_days(days_until)
    if remaining_km <= 0:
        msg = f"Battery health (SOH) is at {soh:.0f}% — at or past the {SOH_THRESHOLD:.0f}% threshold."
        action = "Book a battery health check now."
        severity = "soon"
    elif severity == "soon":
        msg = f"Battery health (SOH) is at {soh:.0f}% and projected to reach the {SOH_THRESHOLD:.0f}% threshold within about {days_until:.0f} days."
        action = "Book a battery health check soon."
    elif severity == "monitor":
        msg = f"Battery health (SOH) is at {soh:.0f}%, projected to reach the {SOH_THRESHOLD:.0f}% threshold in roughly {days_until:.0f} days."
        action = "No action yet — this is normal long-term wear, shown for planning."
    else:
        msg = f"Battery health (SOH) is at {soh:.0f}% with no near-term concern."
        action = "No action needed."
    alerts.append(_alert("BATTERY_SOH_ALERT", "Battery", severity,
                          "Battery Health Outlook", msg, action,
                          days_until=days_until, eta_km=remaining_km if remaining_km != float("inf") else None))

    # ── Tyre slow-leak alert (already near-term by nature — treat as immediate "soon" if detected) ──
    LEAK_THRESHOLD_PSI = 2.0
    tyre_fields = {
        "tyre_pressure_fl": "Front Left", "tyre_pressure_fr": "Front Right",
        "tyre_pressure_rl": "Rear Left", "tyre_pressure_rr": "Rear Right",
    }
    leaking = []
    for field, label in tyre_fields.items():
        newest_p = getattr(newest, field, None) or 0
        oldest_p = getattr(oldest, field, None) or 0
        if (oldest_p - newest_p) >= LEAK_THRESHOLD_PSI:
            leaking.append(label)

    if leaking:
        alerts.append(_alert("TYRE_LEAK_ALERT", "Tyres", "soon",
                              "Possible Slow Tyre Leak",
                              f"{', '.join(leaking)} showing a pressure drop over recent readings — consistent with a slow leak.",
                              "Check tyre pressure and inspect for punctures within the next few days.",
                              days_until=7))
    else:
        alerts.append(_alert("TYRE_LEAK_ALERT", "Tyres", "fine",
                              "Tyre Pressure Outlook", "No slow leaks detected.",
                              "No action needed.", days_until=None))

    summary = {
        "soon": sum(1 for a in alerts if a["severity"] == "soon"),
        "monitor": sum(1 for a in alerts if a["severity"] == "monitor"),
        "fine": sum(1 for a in alerts if a["severity"] == "fine"),
        "total": len(alerts),
    }

    # Sort soon-first so the most urgent items surface at the top of any list
    severity_order = {"soon": 0, "monitor": 1, "fine": 2}
    alerts.sort(key=lambda a: severity_order[a["severity"]])

    return {
        "vehicle_id": vehicle_id,
        "samples_used": im_report["samples_used"],
        "alerts": alerts,
        "summary": summary,
    }