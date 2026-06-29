from sqlalchemy.orm import Session
from backend.models.vehicle_telemetry import VehicleTelemetry
from backend.models.calibration import Calibration
from backend.models.dtc import DTC
from backend.models.fault import Fault


def get_calibration_value(db: Session, parameter: str, default: float) -> float:
    """Fetch calibration limit from DB — real value not hardcoded"""
    cal = db.query(Calibration).filter(
        Calibration.parameter.ilike(f"%{parameter}%")
    ).first()
    return cal.value if cal else default


def get_latest_telemetry(db: Session, vehicle_id: str = "VEH001"):
    """Return the most recent live telemetry row for a vehicle (Day 15 simulator)."""
    return (
        db.query(VehicleTelemetry)
        .filter(VehicleTelemetry.vehicle_id == vehicle_id)
        .order_by(VehicleTelemetry.id.desc())
        .first()
    )


def calculate_real_health_score(db: Session, vehicle_id: str = "VEH001") -> dict:
    """
    Calculate real vehicle health score from the LATEST LIVE TELEMETRY
    (Day 15 CAN simulator -> vehicle_telemetry table) vs actual
    calibration limits stored in DB.
    """
    latest = get_latest_telemetry(db, vehicle_id)

    issues = []
    warnings = []
    health_score = 100.0

    # ── Get calibration limits from DB ────────────────────────
    coolant_limit      = get_calibration_value(db, "Coolant_Temperature",     95.0)
    battery_temp_lim   = get_calibration_value(db, "Battery_Overtemperature", 45.0)
    soc_warning        = get_calibration_value(db, "SOC_Warning",             20.0)
    soc_critical       = get_calibration_value(db, "SOC_Critical",            10.0)
    motor_speed_max    = get_calibration_value(db, "Motor_Speed",          12000.0)
    overvoltage_limit  = get_calibration_value(db, "Battery_Overvoltage",    420.0)
    undervoltage_limit = get_calibration_value(db, "Battery_Undervoltage",   280.0)

    if latest:
        # Coolant temp check
        if latest.coolant_temp and latest.coolant_temp > coolant_limit:
            issues.append({
                "parameter": "Coolant Temperature",
                "value": latest.coolant_temp,
                "limit": coolant_limit,
                "severity": "Critical",
                "message": f"Engine overheating: {latest.coolant_temp}°C > limit {coolant_limit}°C",
                "solution": "Stop vehicle immediately. Check coolant level and radiator.",
                "cost": "₹2,000 - ₹15,000"
            })
            health_score -= 25

        # Battery temp check
        if latest.battery_temp and latest.battery_temp > battery_temp_lim:
            issues.append({
                "parameter": "Battery Temperature",
                "value": latest.battery_temp,
                "limit": battery_temp_lim,
                "severity": "Critical",
                "message": f"Battery overheating: {latest.battery_temp}°C > limit {battery_temp_lim}°C",
                "solution": "Reduce charging rate. Check thermal management system.",
                "cost": "₹5,000 - ₹25,000"
            })
            health_score -= 20

        # RPM check
        if latest.rpm and latest.rpm > motor_speed_max:
            issues.append({
                "parameter": "Motor Speed",
                "value": latest.rpm,
                "limit": motor_speed_max,
                "severity": "High",
                "message": f"Motor overspeed: {latest.rpm} RPM > limit {motor_speed_max} RPM",
                "solution": "Reduce throttle. Check motor control ECU.",
                "cost": "₹3,000 - ₹20,000"
            })
            health_score -= 15

        # SOC checks — now read directly from live telemetry
        soc = latest.soc if latest.soc is not None else 100

        if soc < soc_critical:
            issues.append({
                "parameter": "State of Charge",
                "value": soc,
                "limit": soc_critical,
                "severity": "Critical",
                "message": f"Battery critically low: {soc}% < {soc_critical}%",
                "solution": "Charge vehicle immediately. Find nearest charging station.",
                "cost": "₹0 - ₹500 (charging cost)"
            })
            health_score -= 20
        elif soc < soc_warning:
            warnings.append({
                "parameter": "State of Charge",
                "value": soc,
                "limit": soc_warning,
                "severity": "Medium",
                "message": f"Battery low: {soc}% < {soc_warning}%",
                "solution": "Plan charging within next 30 minutes.",
                "cost": "₹0 - ₹500 (charging cost)"
            })
            health_score -= 10

        # Battery voltage checks — now read directly from live telemetry
        battery_voltage = latest.battery_voltage if latest.battery_voltage is not None else 385

        if battery_voltage > overvoltage_limit:
            issues.append({
                "parameter": "Battery Voltage",
                "value": battery_voltage,
                "limit": overvoltage_limit,
                "severity": "High",
                "message": f"Battery overvoltage: {battery_voltage}V > {overvoltage_limit}V",
                "solution": "Stop charging immediately. Check BMS.",
                "cost": "₹10,000 - ₹50,000"
            })
            health_score -= 20
        elif battery_voltage < undervoltage_limit:
            issues.append({
                "parameter": "Battery Voltage",
                "value": battery_voltage,
                "limit": undervoltage_limit,
                "severity": "High",
                "message": f"Battery undervoltage: {battery_voltage}V < {undervoltage_limit}V",
                "solution": "Charge vehicle. Check battery health.",
                "cost": "₹5,000 - ₹30,000"
            })
            health_score -= 20

        # 12V Auxiliary battery check (Day 15c)
        if latest.aux_battery_voltage is not None and latest.aux_battery_voltage < 12.0:
            issues.append({
                "parameter": "12V Battery",
                "value": latest.aux_battery_voltage,
                "limit": 12.0,
                "severity": "High",
                "message": f"12V battery low: {latest.aux_battery_voltage}V < 12.0V",
                "solution": "Jump-start may be needed. Have the 12V battery tested/replaced.",
                "cost": "₹3,500 - ₹5,000"
            })
            health_score -= 15

        # Brake pad wear check (Day 15b)
        if latest.brake_pad_wear_pct is not None and latest.brake_pad_wear_pct >= 80:
            issues.append({
                "parameter": "Brake Pads",
                "value": latest.brake_pad_wear_pct,
                "limit": 80,
                "severity": "High",
                "message": f"Brake pads worn: {latest.brake_pad_wear_pct}% (replace at 80%)",
                "solution": "Replace brake pads soon.",
                "cost": "₹3,000 - ₹5,000"
            })
            health_score -= 10

        # Tyre pressure checks
        tyres = {
            "Front Left":  latest.tyre_pressure_fl,
            "Front Right": latest.tyre_pressure_fr,
            "Rear Left":   latest.tyre_pressure_rl,
            "Rear Right":  latest.tyre_pressure_rr,
        }
        for label, psi in tyres.items():
            if psi is not None and not (28 <= psi <= 36):
                warnings.append({
                    "parameter": f"Tyre Pressure ({label})",
                    "value": psi,
                    "severity": "Medium",
                    "message": f"{label} tyre pressure {psi} PSI is outside the 28-36 PSI range",
                    "solution": "Check and adjust tyre pressure.",
                    "cost": "₹0 - ₹200 (air top-up)"
                })
                health_score -= 5

    # ── Count diagnostic catalog size (NOT live faults — see Day 16) ──
    active_dtcs   = db.query(DTC).filter(DTC.severity == "High").count()
    active_faults = db.query(Fault).filter(Fault.severity.in_(["High", "Critical"])).count()

    # ── Final health score ────────────────────────────────────
    health_score = max(round(health_score, 1), 0)

    if health_score >= 80:
        status = "Healthy"
        color  = "green"
    elif health_score >= 60:
        status = "Warning"
        color  = "orange"
    elif health_score >= 40:
        status = "Poor"
        color  = "red"
    else:
        status = "Critical"
        color  = "darkred"

    return {
        "health_score":   health_score,
        "status":         status,
        "color":          color,
        "issues":         issues,
        "warnings":       warnings,
        "total_issues":   len(issues),
        "total_warnings": len(warnings),
        "latest_readings": {
            "rpm":             latest.rpm             if latest else 0,
            "speed":           latest.speed           if latest else 0,
            "coolant_temp":    latest.coolant_temp    if latest else 0,
            "battery_temp":    latest.battery_temp    if latest else 0,
            "soc":             latest.soc             if latest else 0,
            "battery_voltage": latest.battery_voltage if latest else 0,
        },
        "timestamp":     str(latest.timestamp) if latest else None,
        "active_dtcs":   active_dtcs,
        "active_faults": active_faults,
    }


def get_health_trend(db: Session, limit: int = 10, vehicle_id: str = "VEH001") -> list:
    """Get health score trend from the last N live telemetry records."""
    records = (
        db.query(VehicleTelemetry)
        .filter(VehicleTelemetry.vehicle_id == vehicle_id)
        .order_by(VehicleTelemetry.id.desc())
        .limit(limit)
        .all()
    )
    records.reverse()  # oldest -> newest, for a left-to-right chart

    coolant_limit    = get_calibration_value(db, "Coolant_Temperature", 95.0)
    battery_temp_lim = get_calibration_value(db, "Battery_Overtemperature", 45.0)

    trend = []
    for r in records:
        score = 100.0
        if r.coolant_temp and r.coolant_temp > coolant_limit:
            score -= 25
        if r.battery_temp and r.battery_temp > battery_temp_lim:
            score -= 20
        if r.rpm and r.rpm > 6000:
            score -= 15

        trend.append({
            "timestamp":    str(r.timestamp),
            "health_score": max(round(score, 1), 0),
            "rpm":          r.rpm,
            "speed":        r.speed,
            "coolant_temp": r.coolant_temp,
            "battery_temp": r.battery_temp,
        })

    return trend