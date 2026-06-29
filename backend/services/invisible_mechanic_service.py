"""
ACIP-X1 — Invisible Mechanic (Day 17 / C3)

Where Day 16 (Problem -> Solution -> Cost) checks the CURRENT snapshot
against safety limits, Invisible Mechanic looks at TRENDS in recent
telemetry history and projects forward — answering "when will this
need attention?" instead of just "is this OK right now?"

Each insight returns:
    title        -> what's being tracked
    observation   -> what the data shows right now
    prediction    -> a forward-looking estimate (when / how much further)
    recommendation -> what the customer should do, if anything
    basis         -> how the estimate was derived (builds trust)

Also includes a Driving Behaviour Score (seed of C7 — Driver Score /
Eco-Driving Report), since it shares the same trend data.
"""
import math
from sqlalchemy.orm import Session
from backend.models.vehicle_telemetry import VehicleTelemetry


# Industry-typical baselines used when there isn't enough observed
# trend data yet (e.g., right after a fresh start) — these come from
# common EV service-life references, not from live data.
TYPICAL_BRAKE_PAD_LIFE_KM = 30000     # pads typically reach ~80% wear by here
BRAKE_PAD_REPLACE_THRESHOLD = 80.0
TYPICAL_SOH_80PCT_KM = 150000         # packs typically reach ~80% SOH by here
SOH_WARNING_THRESHOLD = 80.0
HARSH_ACCEL_THRESHOLD_G = 0.30        # |accel_x| or |accel_y| above this = "harsh" event


def _get_history(db: Session, vehicle_id: str, limit: int = 150):
    """Newest-first list of recent telemetry samples."""
    return (
        db.query(VehicleTelemetry)
        .filter(VehicleTelemetry.vehicle_id == vehicle_id)
        .order_by(VehicleTelemetry.id.desc())
        .limit(limit)
        .all()
    )


def _format_duration(days):
    """Turn a day-count into a readable string (days/months/years)."""
    if days < 1:
        return "less than a day"
    if days < 60:
        return f"~{days:.0f} days"
    months = days / 30.4
    if months < 24:
        return f"~{months:.0f} months"
    return f"~{months / 12:.1f} years"


def _insight(insight_id, category, title, observation, prediction, recommendation, basis):
    return {
        "id": insight_id,
        "category": category,
        "title": title,
        "observation": observation,
        "prediction": prediction,
        "recommendation": recommendation,
        "basis": basis,
    }


def get_invisible_mechanic_report(db: Session, vehicle_id: str = "VEH001") -> dict:
    history = _get_history(db, vehicle_id, limit=150)

    if not history:
        return {"vehicle_id": vehicle_id, "samples_used": 0, "insights": [], "driver_score": None}

    newest = history[0]
    oldest = history[-1]
    n = len(history)

    insights = []

    # ══════════════════════════════════════════════════════════════
    # 1. BRAKE PAD LIFE PREDICTION
    # ══════════════════════════════════════════════════════════════
    current_wear = newest.brake_pad_wear_pct or 0
    delta_wear = (newest.brake_pad_wear_pct or 0) - (oldest.brake_pad_wear_pct or 0)
    delta_odo = (newest.odometer_km or 0) - (oldest.odometer_km or 0)
    remaining_pct = max(0, BRAKE_PAD_REPLACE_THRESHOLD - current_wear)

    if delta_odo > 0.05 and delta_wear > 0:
        # Enough observed driving to derive a real wear rate
        wear_rate_per_km = delta_wear / delta_odo
        remaining_km = remaining_pct / wear_rate_per_km if wear_rate_per_km > 0 else float("inf")
        basis = f"Based on your last {delta_odo:.2f}km of driving (observed wear rate)."
    else:
        # Not enough movement yet — fall back to a typical-life baseline
        typical_rate_per_km = BRAKE_PAD_REPLACE_THRESHOLD / TYPICAL_BRAKE_PAD_LIFE_KM
        remaining_km = remaining_pct / typical_rate_per_km if typical_rate_per_km > 0 else float("inf")
        basis = f"Based on a typical brake pad life of ~{TYPICAL_BRAKE_PAD_LIFE_KM:,} km (not enough recent driving to measure your own rate yet)."

    if remaining_km == float("inf") or remaining_km > 200000:
        prediction = "Pads are essentially not wearing right now — no replacement needed for the foreseeable future."
        recommendation = "No action needed."
    else:
        remaining_days = remaining_km / 40  # ~40km/day average usage assumption
        duration_str = _format_duration(remaining_days)
        prediction = f"At this rate, brake pads should reach the {BRAKE_PAD_REPLACE_THRESHOLD:.0f}% replacement point in approximately {remaining_km:,.0f} km ({duration_str} at a typical ~40km/day)."
        recommendation = "No action needed yet — this is for planning your next service." if remaining_km > 2000 else "Consider booking a brake inspection soon."

    insights.append(_insight(
        "BRAKE_PAD_LIFE", "Brakes",
        "Brake Pad Life Remaining",
        f"Brake pads are currently {current_wear:.1f}% worn.",
        prediction, recommendation, basis,
    ))

    # ══════════════════════════════════════════════════════════════
    # 2. BATTERY HEALTH (SOH) LONG-TERM OUTLOOK
    # ══════════════════════════════════════════════════════════════
    soh = newest.soh or 100
    odo = newest.odometer_km or 0
    degraded_so_far = 100 - soh

    if degraded_so_far > 0.01 and odo > 0:
        degradation_rate_per_km = degraded_so_far / odo
        remaining_degradation = max(0, soh - SOH_WARNING_THRESHOLD)
        remaining_km = remaining_degradation / degradation_rate_per_km if degradation_rate_per_km > 0 else float("inf")
        basis = f"Based on {degraded_so_far:.1f}% degradation observed over {odo:,.0f} km so far."
    else:
        # No measurable degradation yet — use an industry-typical curve
        remaining_km = TYPICAL_SOH_80PCT_KM - odo
        basis = f"Based on a typical EV pack reaching {SOH_WARNING_THRESHOLD:.0f}% health around {TYPICAL_SOH_80PCT_KM:,} km (your pack shows no measurable degradation yet)."

    if remaining_km <= 0:
        prediction = f"Battery health is at or near the {SOH_WARNING_THRESHOLD:.0f}% threshold — a battery health check is recommended."
        recommendation = "Book a battery health inspection at your next service."
    else:
        remaining_days = remaining_km / 40  # ~40km/day average usage assumption
        duration_str = _format_duration(remaining_days)
        prediction = f"At the current pace, battery health is projected to reach the {SOH_WARNING_THRESHOLD:.0f}% threshold around {odo + remaining_km:,.0f} km on the odometer ({remaining_km:,.0f} km from now, roughly {duration_str} at a typical ~40km/day)."
        recommendation = "No action needed — this is normal long-term wear, shown for planning purposes."

    insights.append(_insight(
        "BATTERY_SOH_OUTLOOK", "Battery",
        "Battery Health Long-Term Outlook",
        f"Battery health (SOH) is currently {soh:.1f}% of original capacity at {odo:,.0f} km.",
        prediction, recommendation, basis,
    ))

    # ══════════════════════════════════════════════════════════════
    # 3. TYRE PRESSURE TREND (slow-leak check)
    # ══════════════════════════════════════════════════════════════
    tyre_fields = {
        "tyre_pressure_fl": "Front Left",
        "tyre_pressure_fr": "Front Right",
        "tyre_pressure_rl": "Rear Left",
        "tyre_pressure_rr": "Rear Right",
    }
    LEAK_THRESHOLD_PSI = 2.0
    leaking_tyres = []
    for field, label in tyre_fields.items():
        newest_p = getattr(newest, field, None) or 0
        oldest_p = getattr(oldest, field, None) or 0
        drop = oldest_p - newest_p
        if drop >= LEAK_THRESHOLD_PSI:
            leaking_tyres.append((label, drop, newest_p))

    if leaking_tyres:
        details = "; ".join(f"{label} dropped {drop:.1f} PSI (now {now:.1f} PSI)" for label, drop, now in leaking_tyres)
        insights.append(_insight(
            "TYRE_PRESSURE_TREND", "Tyres",
            "Possible Slow Tyre Leak Detected",
            f"{details} over the last {n} readings.",
            "If this trend continues, one or more tyres could become significantly under-inflated within a few days.",
            "Check tyre pressure and inspect for punctures or valve leaks soon.",
            f"Based on comparing your {n} most recent readings.",
        ))
    else:
        insights.append(_insight(
            "TYRE_PRESSURE_TREND", "Tyres",
            "Tyre Pressure Trend",
            "All four tyre pressures have been stable.",
            "No slow leaks detected — pressures should remain in the healthy range for now.",
            "No action needed.",
            f"Based on comparing your {n} most recent readings.",
        ))

    # ══════════════════════════════════════════════════════════════
    # DRIVER SCORE (seed of C7 — Eco-Driving Report)
    # ══════════════════════════════════════════════════════════════
    harsh_events = 0
    sum_abs_x = 0.0
    sum_abs_y = 0.0
    sum_epk = 0.0
    epk_count = 0
    for h in history:
        ax = abs(h.accel_x or 0)
        ay = abs(h.accel_y or 0)
        sum_abs_x += ax
        sum_abs_y += ay
        if ax > HARSH_ACCEL_THRESHOLD_G or ay > HARSH_ACCEL_THRESHOLD_G:
            harsh_events += 1
        if h.energy_per_100km is not None:
            sum_epk += h.energy_per_100km
            epk_count += 1

    avg_abs_x = sum_abs_x / n
    avg_abs_y = sum_abs_y / n
    avg_epk = (sum_epk / epk_count) if epk_count else 0
    harsh_pct = harsh_events / n * 100

    # Score: starts at 100, deduct for harsh events and poor efficiency
    score = 100 - harsh_pct * 1.5
    if avg_epk > 16:
        score -= min(20, (avg_epk - 16) * 2)
    score = max(0, min(100, round(score)))

    if score >= 85:
        style, style_color = "Smooth & Efficient", "#3fb950"
        driver_tip = "Great driving! Smooth acceleration and braking like this helps your brakes, tyres, and battery last longer."
    elif score >= 60:
        style, style_color = "Moderate", "#d29922"
        driver_tip = "Try easing off the accelerator a bit and braking earlier — smoother inputs improve range and reduce wear."
    else:
        style, style_color = "Aggressive", "#f85149"
        driver_tip = "Frequent hard acceleration/braking detected. This increases wear on brakes and tyres and reduces your real-world range."

    driver_score = {
        "score": score,
        "style": style,
        "style_color": style_color,
        "harsh_events": harsh_events,
        "samples": n,
        "harsh_pct": round(harsh_pct, 1),
        "avg_energy_per_100km": round(avg_epk, 1),
        "tip": driver_tip,
    }

    return {
        "vehicle_id": vehicle_id,
        "samples_used": n,
        "insights": insights,
        "driver_score": driver_score,
    }