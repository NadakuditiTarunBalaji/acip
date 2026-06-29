from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json

from backend.config.database import get_db
from backend.models.can_frame import CANFrame

router = APIRouter(
    prefix="/api/can",
    tags=["CAN Bus"]
)


class CANFrameCreate(BaseModel):
    vehicle_id: str
    can_id: str
    dlc: int
    raw_data: str
    decoded_data: Optional[Dict[str, Any]] = {}


@router.post("/frame")
def receive_can_frame(
    frame: CANFrameCreate,
    db: Session = Depends(get_db)
):
    # Store CAN frame
    can_frame = CANFrame(
        vehicle_id=frame.vehicle_id,
        can_id=frame.can_id,
        dlc=frame.dlc,
        raw_data=frame.raw_data,
        decoded_data=json.dumps(frame.decoded_data)
    )
    db.add(can_frame)
    db.commit()
    db.refresh(can_frame)

    # Basic AI analysis on decoded data
    analysis = analyze_can_data(frame.decoded_data)

    return {
        "status": "received",
        "frame_id": can_frame.id,
        "vehicle_id": frame.vehicle_id,
        "analysis": analysis
    }


@router.get("/frames/{vehicle_id}")
def get_can_frames(
    vehicle_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    frames = (
        db.query(CANFrame)
        .filter(CANFrame.vehicle_id == vehicle_id)
        .order_by(CANFrame.timestamp.desc())
        .limit(limit)
        .all()
    )
    return frames


@router.get("/latest/{vehicle_id}")
def get_latest_frame(
    vehicle_id: str,
    db: Session = Depends(get_db)
):
    frame = (
        db.query(CANFrame)
        .filter(CANFrame.vehicle_id == vehicle_id)
        .order_by(CANFrame.timestamp.desc())
        .first()
    )
    return frame


def analyze_can_data(decoded_data: dict) -> dict:
    issues = []
    health_score = 100.0

    rpm = decoded_data.get("rpm", 0)
    speed = decoded_data.get("speed", 0)
    engine_temp = decoded_data.get("engine_temp", 0)
    battery_voltage = decoded_data.get("battery_voltage", 12.6)
    fuel_level = decoded_data.get("fuel_level", 100)

    if rpm > 6000:
        issues.append("High RPM detected")
        health_score -= 15
    if engine_temp > 95:
        issues.append("Engine overheating")
        health_score -= 20
    if battery_voltage < 12.0:
        issues.append("Low battery voltage")
        health_score -= 15
    if fuel_level < 10:
        issues.append("Critical fuel level")
        health_score -= 10

    if health_score >= 80:
        status = "Healthy"
    elif health_score >= 60:
        status = "Warning"
    else:
        status = "Critical"

    return {
        "health_score": max(health_score, 0),
        "status": status,
        "issues": issues
    }