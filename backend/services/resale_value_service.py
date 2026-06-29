"""
ACIP-X1 — Resale Value Maximizer (Day 21 / C9)

Estimates the vehicle's current resale value and shows exactly what
fixing active issues would be worth — both grounded in REAL data:
- base_price: owner-entered once (we have no market pricing API or
  make/model/year data wired in, so this can't be invented honestly)
- health_score, issues, warnings: Day 16's calculate_real_health_score
- odometer: Day 15 simulator's live telemetry (used only if present —
  never assumed, since not every vehicle reading includes it yet)
- repair costs per issue: the same cost ranges already shown in the
  Alerts & Issues tab, so "fix this -> value goes up by X" is the
  literal same number the owner would pay a mechanic, not a separate
  invented figure.

The formula is intentionally simple and explainable, not a black box:
    estimated_value = base_price x health_multiplier - unresolved_repair_cost - odometer_deduction

health_multiplier maps the 0-100 health score to a 0.70-1.00 range —
even a "Critical" vehicle keeps most of its value (the chassis/battery
pack/motor are still worth something), while a perfect health score
loses nothing to the multiplier.
"""
import re
from sqlalchemy.orm import Session

from backend.models.vehicle import Vehicle
from backend.services.dashboard_service import calculate_real_health_score, get_latest_telemetry

# Health score 0 -> multiplier 0.70, health score 100 -> multiplier 1.00.
MIN_MULTIPLIER = 0.70
MAX_MULTIPLIER = 1.00

# Odometer deduction: a simple, clearly-labeled INR-per-km rate, applied
# only when real odometer data exists. This is a deliberately modest
# rate (typical EV depreciation guidance) since we're not claiming
# precision here, just a directionally honest adjustment.
INR_PER_KM_DEPRECIATION = 1.5


def _get_vehicle(db: Session, vehicle_id: str) -> Vehicle | None:
    return db.query(Vehicle).filter(Vehicle.vin == vehicle_id).first() or \
        db.query(Vehicle).first()  # fall back to the single seeded vehicle if vin doesn't match vehicle_id


def _parse_cost_midpoint(cost_str: str) -> int:
    """
    Extracts the midpoint of a cost range string like '₹2,000 - ₹15,000'
    or '₹0 - ₹500 (charging cost)'. Returns 0 if nothing parseable is
    found, rather than guessing a number.
    """
    numbers = re.findall(r"[\d,]+", cost_str)
    cleaned = [int(n.replace(",", "")) for n in numbers if n.replace(",", "").isdigit()]
    if not cleaned:
        return 0
    if len(cleaned) == 1:
        return cleaned[0]
    return round((cleaned[0] + cleaned[1]) / 2)


def get_resale_estimate(db: Session, vehicle_id: str = "VEH001") -> dict:
    """
    Returns the current resale estimate, what's dragging it down, and
    what fixing each issue would recover — or needs_base_price=True if
    the owner hasn't entered a base price yet, since we won't invent one.
    """
    vehicle = _get_vehicle(db, vehicle_id)
    if vehicle is None or not vehicle.base_price:
        return {"needs_base_price": True, "vehicle_id": vehicle_id}

    base_price = vehicle.base_price
    health = calculate_real_health_score(db, vehicle_id)
    health_score = health["health_score"]

    multiplier = MIN_MULTIPLIER + (MAX_MULTIPLIER - MIN_MULTIPLIER) * (health_score / 100)
    value_after_health = base_price * multiplier

    # Only critical issues count against resale value here — warnings
    # are minor/early signals that a buyer wouldn't reasonably negotiate
    # on, but unresolved critical issues are exactly what a buyer (or
    # their mechanic) would flag and discount for.
    fixable_issues = []
    total_repair_cost = 0
    for issue in health["issues"]:
        cost = _parse_cost_midpoint(issue.get("cost", ""))
        total_repair_cost += cost
        fixable_issues.append({
            "parameter": issue["parameter"],
            "message": issue["message"],
            "estimated_repair_cost": cost,
            "value_recovered_if_fixed": cost,  # fixing it removes exactly this deduction
        })

    odometer_deduction = 0
    latest = get_latest_telemetry(db, vehicle_id)
    odometer_km = latest.odometer_km if latest and latest.odometer_km else None
    if odometer_km:
        odometer_deduction = round(odometer_km * INR_PER_KM_DEPRECIATION)

    current_value = round(value_after_health - total_repair_cost - odometer_deduction)
    current_value = max(current_value, 0)

    potential_value = round(value_after_health - odometer_deduction)
    potential_value = max(potential_value, current_value)

    return {
        "needs_base_price": False,
        "vehicle_id": vehicle_id,
        "base_price": base_price,
        "health_score": health_score,
        "health_status": health["status"],
        "odometer_km": odometer_km,
        "odometer_deduction": odometer_deduction,
        "current_estimated_value": current_value,
        "potential_value_if_all_fixed": potential_value,
        "total_value_recoverable": potential_value - current_value,
        "fixable_issues": fixable_issues,
    }


def set_base_price(db: Session, vehicle_id: str, base_price: int) -> dict:
    """Stores the owner-entered base price — the one piece of this
    feature we genuinely can't derive from telemetry, since we have
    no real make/model/year market data wired into this project."""
    vehicle = _get_vehicle(db, vehicle_id)
    if vehicle is None:
        return {"updated": False, "error": "No vehicle record found"}
    vehicle.base_price = base_price
    db.commit()
    return {"updated": True, "vehicle_id": vehicle_id, "base_price": base_price}