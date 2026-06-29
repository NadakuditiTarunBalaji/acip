from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from backend.config.database import get_db
from backend.models.vehicle_telemetry import VehicleTelemetry
from backend.models.vehicle_destination import VehicleDestination
from backend.schemas.vehicle_schema import (
    VehicleTelemetryCreate,
    VehicleTelemetryResponse,
    DestinationCreate,
    DestinationResponse,
)
from backend.services.accident_service import check_for_crash
from backend.services.breakdown_service import check_for_breakdown

router = APIRouter(
    prefix="/api/telemetry",
    tags=["Vehicle Telemetry — Live CAN Data"]
)


@router.post("/", response_model=VehicleTelemetryResponse)
def create_telemetry(
    telemetry: VehicleTelemetryCreate,
    db: Session = Depends(get_db)
):
    """Receive one live telemetry sample from the CAN simulator / hardware."""
    record = VehicleTelemetry(**telemetry.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)

    # Day 18 (C4) — check every incoming sample for crash-level G-force.
    # Runs after commit so the telemetry itself is never blocked or lost
    # even if accident handling has an issue.
    check_for_crash(db, record)

    # Day 19 (C5) — check every incoming sample for a genuine breakdown
    # signature (stopped, not charging, critical fault present). Same
    # never-block-telemetry pattern as the crash check above.
    check_for_breakdown(db, record.vehicle_id)

    return record


@router.get("/latest/{vehicle_id}", response_model=VehicleTelemetryResponse)
def get_latest_telemetry(
    vehicle_id: str,
    db: Session = Depends(get_db)
):
    """Return the most recent telemetry sample for a vehicle."""
    record = (
        db.query(VehicleTelemetry)
        .filter(VehicleTelemetry.vehicle_id == vehicle_id)
        .order_by(VehicleTelemetry.timestamp.desc())
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"No telemetry found for vehicle '{vehicle_id}'. Is the CAN simulator running?"
        )
    return record


@router.get("/history/{vehicle_id}", response_model=List[VehicleTelemetryResponse])
def get_telemetry_history(
    vehicle_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Return the most recent N telemetry samples for a vehicle (newest first)."""
    records = (
        db.query(VehicleTelemetry)
        .filter(VehicleTelemetry.vehicle_id == vehicle_id)
        .order_by(VehicleTelemetry.timestamp.desc())
        .limit(limit)
        .all()
    )
    return records

# ══════════════════════════════════════════════════════════
#  Destination / Navigation (Day 15d)
# ══════════════════════════════════════════════════════════

@router.post("/destination", response_model=DestinationResponse)
def set_destination(dest: DestinationCreate, db: Session = Depends(get_db)):
    """
    Set (or replace) the destination for a vehicle.
    The CAN simulator will steer towards this point; the dashboard will
    show distance remaining / ETA and plot it on the map.
    """
    record = (
        db.query(VehicleDestination)
        .filter(VehicleDestination.vehicle_id == dest.vehicle_id)
        .first()
    )
    if record:
        record.dest_name = dest.dest_name
        record.dest_lat = dest.dest_lat
        record.dest_lon = dest.dest_lon
        record.status = "active"
        record.set_at = datetime.utcnow()
    else:
        record = VehicleDestination(
            vehicle_id=dest.vehicle_id,
            dest_name=dest.dest_name,
            dest_lat=dest.dest_lat,
            dest_lon=dest.dest_lon,
            status="active",
            set_at=datetime.utcnow(),
        )
        db.add(record)

    db.commit()
    db.refresh(record)
    return record


@router.get("/destination/{vehicle_id}", response_model=DestinationResponse)
def get_destination(vehicle_id: str, db: Session = Depends(get_db)):
    """Return the active destination for a vehicle, or 404 if none is set."""
    record = (
        db.query(VehicleDestination)
        .filter(VehicleDestination.vehicle_id == vehicle_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="No destination set")
    return record


@router.patch("/destination/{vehicle_id}/arrived", response_model=DestinationResponse)
def mark_arrived(vehicle_id: str, db: Session = Depends(get_db)):
    """Mark the current destination as 'arrived' (called by the CAN simulator)."""
    record = (
        db.query(VehicleDestination)
        .filter(VehicleDestination.vehicle_id == vehicle_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="No destination set")
    record.status = "arrived"
    db.commit()
    db.refresh(record)
    return record


@router.delete("/destination/{vehicle_id}")
def clear_destination(vehicle_id: str, db: Session = Depends(get_db)):
    """Clear the destination for a vehicle (stop navigation)."""
    record = (
        db.query(VehicleDestination)
        .filter(VehicleDestination.vehicle_id == vehicle_id)
        .first()
    )
    if record:
        db.delete(record)
        db.commit()
    return {"vehicle_id": vehicle_id, "cleared": True}