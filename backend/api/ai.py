from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from backend.config.database import get_db
from backend.models.dtc import DTC
from backend.models.fault import Fault
from backend.services.dashboard_service import get_calibration_value

router = APIRouter(
    prefix="/api/ai",
    tags=["AI Analysis"]
)


class DiagnosticRequest(BaseModel):
    vehicle_id: str
    rpm: Optional[float] = 0
    speed: Optional[float] = 0
    coolant_temp: Optional[float] = 30
    battery_voltage: Optional[float] = 380
    soc: Optional[float] = 80


@router.post("/diagnose")
def diagnose_vehicle(
    request: DiagnosticRequest,
    db: Session = Depends(get_db)
):
    """
    What-If Simulator — runs hypothetical EV sensor readings through the
    SAME calibration limits used by the Live Dashboard's health score
    (backend/services/dashboard_service.py), so results here stay
    consistent with what the customer sees live.
    """
    issues = []
    recommendations = []
    health_score = 100.0

    motor_speed_max    = get_calibration_value(db, "Motor_Speed",          12000.0)
    coolant_limit      = get_calibration_value(db, "Coolant_Temperature",     95.0)
    overvoltage_limit  = get_calibration_value(db, "Battery_Overvoltage",    420.0)
    undervoltage_limit = get_calibration_value(db, "Battery_Undervoltage",   280.0)
    soc_warning        = get_calibration_value(db, "SOC_Warning",             20.0)
    soc_critical       = get_calibration_value(db, "SOC_Critical",            10.0)

    # Motor RPM check
    if request.rpm > motor_speed_max:
        issues.append({
            "parameter": "Motor RPM",
            "value": request.rpm,
            "threshold": motor_speed_max,
            "severity": "High",
            "message": f"Motor overspeed: {request.rpm:.0f} RPM exceeds the {motor_speed_max:.0f} RPM limit",
            "solution": "Ease off the accelerator — motor speed is above the safe limit."
        })
        recommendations.append("Reduce throttle — motor speed exceeds the safe limit")
        health_score -= 20

    # Coolant temperature check
    if request.coolant_temp > coolant_limit:
        issues.append({
            "parameter": "Coolant Temperature",
            "value": request.coolant_temp,
            "threshold": coolant_limit,
            "severity": "Critical",
            "message": f"Coolant overheating: {request.coolant_temp:.1f}°C exceeds the {coolant_limit:.0f}°C limit",
            "solution": "Pull over safely and let the vehicle cool down before continuing."
        })
        recommendations.append("Pull over safely and let the vehicle cool down")
        health_score -= 25

    # Battery pack voltage checks
    if request.battery_voltage > overvoltage_limit:
        issues.append({
            "parameter": "Battery Voltage",
            "value": request.battery_voltage,
            "threshold": overvoltage_limit,
            "severity": "High",
            "message": f"Battery overvoltage: {request.battery_voltage:.1f}V exceeds the {overvoltage_limit:.0f}V limit",
            "solution": "Stop charging immediately and have the battery management system checked."
        })
        recommendations.append("Stop charging immediately — battery voltage is too high")
        health_score -= 20
    elif request.battery_voltage < undervoltage_limit:
        issues.append({
            "parameter": "Battery Voltage",
            "value": request.battery_voltage,
            "threshold": undervoltage_limit,
            "severity": "High",
            "message": f"Battery undervoltage: {request.battery_voltage:.1f}V is below the {undervoltage_limit:.0f}V limit",
            "solution": "Charge the vehicle and have the battery health checked."
        })
        recommendations.append("Charge the vehicle — battery voltage is too low")
        health_score -= 20

    # Battery SOC checks
    if request.soc < soc_critical:
        issues.append({
            "parameter": "Battery SOC",
            "value": request.soc,
            "threshold": soc_critical,
            "severity": "Critical",
            "message": f"Battery critically low: {request.soc:.1f}% is below {soc_critical:.0f}%",
            "solution": "Charge the vehicle immediately — find the nearest charging point."
        })
        recommendations.append("Charge the vehicle immediately — battery is critically low")
        health_score -= 20
    elif request.soc < soc_warning:
        issues.append({
            "parameter": "Battery SOC",
            "value": request.soc,
            "threshold": soc_warning,
            "severity": "Medium",
            "message": f"Battery low: {request.soc:.1f}% is below {soc_warning:.0f}%",
            "solution": "Plan to charge within the next 30 minutes."
        })
        recommendations.append("Plan to charge soon — battery is getting low")
        health_score -= 10

    if health_score >= 80:
        status = "Healthy"
    elif health_score >= 60:
        status = "Warning"
    else:
        status = "Critical"

    return {
        "vehicle_id": request.vehicle_id,
        "health_score": max(health_score, 0),
        "status": status,
        "issues": issues,
        "recommendations": recommendations,
        "total_issues": len(issues)
    }


@router.get("/analyze-dtc/{dtc_id}")
def analyze_dtc(
    dtc_id: str,
    db: Session = Depends(get_db)
):
    dtc = db.query(DTC).filter(DTC.dtc_id == dtc_id).first()
    if not dtc:
        return {"error": "DTC not found"}

    # Find related faults
    related_faults = db.query(Fault).filter(
        Fault.fault_name.contains(dtc.description.split()[0])
    ).all()

    return {
        "dtc": {
            "id": dtc.dtc_id,
            "description": dtc.description,
            "severity": dtc.severity
        },
        "related_faults": [
            {
                "fault_id": f.fault_id,
                "name": f.fault_name,
                "root_cause": f.root_cause,
                "severity": f.severity
            }
            for f in related_faults
        ],
        "recommendation": f"Inspect system related to: {dtc.description}"
    }