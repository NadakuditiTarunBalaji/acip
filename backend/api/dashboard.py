from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.config.database import get_db
from backend.services.dashboard_service import (
    calculate_real_health_score,
    get_health_trend
)
from backend.services.problem_engine import run_diagnostics
from backend.services.invisible_mechanic_service import get_invisible_mechanic_report
from backend.services.predictive_alerts_service import get_predictive_alerts

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"]
)


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Real-time vehicle health summary calculated from
    actual sensor data vs actual calibration limits
    """
    return calculate_real_health_score(db)


@router.get("/diagnostics")
def get_diagnostics(vehicle_id: str = "VEH001", db: Session = Depends(get_db)):
    """
    Day 16 (C2) — Problem -> Solution -> Cost Engine.
    Runs every live signal against the real calibration limits and
    returns a customer-friendly Problem/Solution/Cost/Impact card for
    each one (including healthy systems).
    """
    return run_diagnostics(db, vehicle_id)


@router.get("/invisible-mechanic")
def get_invisible_mechanic(vehicle_id: str = "VEH001", db: Session = Depends(get_db)):
    """
    Day 17 (C7) — Invisible Mechanic.
    Analyzes recent telemetry trends to predict when components will
    need attention, and produces a Driver Score.
    """
    return get_invisible_mechanic_report(db, vehicle_id)


@router.get("/predictive-alerts")
def get_predictive_alerts_api(vehicle_id: str = "VEH001", db: Session = Depends(get_db)):
    """
    Day 17 (C3) — Predictive Alerts.
    Re-frames Invisible Mechanic's trend projections as urgency-tiered
    alerts (soon / monitor / fine), distinct from C2's reactive
    Problem/Solution/Cost checks which only look at today's snapshot.
    """
    return get_predictive_alerts(db, vehicle_id)


@router.get("/health-trend")
def get_health_trend_api(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get health score trend over last N readings"""
    return get_health_trend(db, limit)


@router.get("/active-faults")
def get_active_faults(db: Session = Depends(get_db)):
    from backend.models.fault import Fault
    faults = db.query(Fault).filter(
        Fault.severity.in_(["High", "Critical"])
    ).all()
    return {
        "total": len(faults),
        "faults": [
            {
                "fault_id":   f.fault_id,
                "name":       f.fault_name,
                "root_cause": f.root_cause,
                "severity":   f.severity
            }
            for f in faults
        ]
    }


@router.get("/active-dtcs")
def get_active_dtcs(db: Session = Depends(get_db)):
    from backend.models.dtc import DTC
    dtcs = db.query(DTC).filter(
        DTC.severity.in_(["High", "Critical"])
    ).all()
    return {
        "total": len(dtcs),
        "dtcs": [
            {
                "dtc_id":      d.dtc_id,
                "description": d.description,
                "severity":    d.severity
            }
            for d in dtcs
        ]
    }


@router.get("/calibration-limits")
def get_calibration_limits(db: Session = Depends(get_db)):
    """Get all calibration limits — used by frontend for threshold display"""
    from backend.models.calibration import Calibration
    calibrations = db.query(Calibration).all()
    return {
        "total": len(calibrations),
        "limits": [
            {
                "cal_id":    c.cal_id,
                "parameter": c.parameter,
                "value":     c.value,
                "unit":      c.unit
            }
            for c in calibrations
        ]
    }