from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from backend.config.database import get_db
from backend.models.emergency_contact import EmergencyContact
from backend.models.vehicle_telemetry import VehicleTelemetry
from backend.models.nearby_device import NearbyDevice
from backend.schemas.emergency_schema import (
    EmergencyContactCreate,
    EmergencyContactResponse,
    NearbyDeviceResponse,
)
from backend.services.accident_service import (
    check_for_crash,
    get_accident_history,
    resolve_accident,
    compute_combined_g,
)

router = APIRouter(
    prefix="/api/emergency",
    tags=["Emergency Response — Accident Detection (C4)"]
)


def _offset_position(lat, lon, offset_km=0.4):
    """
    Returns a GPS point roughly offset_km away from (lat, lon), used to
    place a demo nearby-phone close enough to be inside the 1km alert
    radius regardless of where the vehicle has driven to.
    """
    import math
    dlat = offset_km / 111.0
    dlon = offset_km / (111.0 * math.cos(math.radians(lat or 13.0827)))
    return (lat or 13.0827) + dlat, (lon or 80.2707) + dlon


# ── Emergency Contacts ────────────────────────────────────
@router.get("/contacts/{vehicle_id}", response_model=List[EmergencyContactResponse])
def list_contacts(vehicle_id: str, db: Session = Depends(get_db)):
    return (
        db.query(EmergencyContact)
        .filter(EmergencyContact.vehicle_id == vehicle_id)
        .order_by(EmergencyContact.priority.asc())
        .all()
    )


@router.post("/contacts", response_model=EmergencyContactResponse)
def add_contact(contact: EmergencyContactCreate, db: Session = Depends(get_db)):
    record = EmergencyContact(**contact.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/contacts/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    record = db.query(EmergencyContact).filter(EmergencyContact.id == contact_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(record)
    db.commit()
    return {"deleted": True, "contact_id": contact_id}


# ── Nearby Devices (phones running the app) ───────────────
@router.get("/nearby-devices", response_model=List[NearbyDeviceResponse])
def list_nearby_devices(db: Session = Depends(get_db)):
    return db.query(NearbyDevice).all()


# ── Accident Events ────────────────────────────────────────
@router.get("/accidents/{vehicle_id}")
def accident_history(vehicle_id: str, limit: int = 20, db: Session = Depends(get_db)):
    return {
        "vehicle_id": vehicle_id,
        "events": get_accident_history(db, vehicle_id, limit),
    }


@router.patch("/accidents/{accident_id}/resolve")
def resolve(accident_id: int, mark_as: str = "Resolved", db: Session = Depends(get_db)):
    event = resolve_accident(db, accident_id, mark_as)
    if not event:
        raise HTTPException(status_code=404, detail="Accident event not found")
    return {"id": event.id, "status": event.status, "resolved_at": event.resolved_at}


@router.post("/demo-trigger/{vehicle_id}")
def demo_trigger_crash(vehicle_id: str, severity: str = "Severe", db: Session = Depends(get_db)):
    """
    Demo / test endpoint — manually injects a single high-G telemetry
    sample for the given vehicle to trigger real crash detection through
    the actual production code path (check_for_crash), rather than
    faking an AccidentEvent directly. Useful for showing the manager
    what happens without needing a real collision.
    """
    latest = (
        db.query(VehicleTelemetry)
        .filter(VehicleTelemetry.vehicle_id == vehicle_id)
        .order_by(VehicleTelemetry.timestamp.desc())
        .first()
    )
    if not latest:
        raise HTTPException(
            status_code=404,
            detail=f"No telemetry found for '{vehicle_id}' — start the CAN simulator first."
        )

    g_value = 7.0 if severity == "Severe" else 4.0

    # Move the demo nearby-phones close to the vehicle's current position
    # so the 1km radius alert has something real to find, regardless of
    # where the vehicle has driven to since the app started. Each phone
    # gets a slightly different offset so they show as distinct distances
    # rather than overlapping exactly.
    demo_offsets_km = {"Karthik": 0.4, "Naresh Reddy": 0.6}
    for owner_name, offset_km in demo_offsets_km.items():
        demo_phone = db.query(NearbyDevice).filter(NearbyDevice.owner_name == owner_name).first()
        if demo_phone:
            new_lat, new_lon = _offset_position(latest.gps_lat, latest.gps_lon, offset_km=offset_km)
            demo_phone.gps_lat = new_lat
            demo_phone.gps_lon = new_lon
            demo_phone.last_updated = datetime.utcnow()
    db.commit()

    demo_sample = VehicleTelemetry(
        vehicle_id=vehicle_id,
        rpm=0, speed=latest.speed, motor_torque=0,
        accelerator_position=0, regen_brake_level=0,
        battery_voltage=latest.battery_voltage,
        battery_current=latest.battery_current,
        battery_temp=latest.battery_temp,
        soc=latest.soc, soh=latest.soh,
        cell_voltage_min=latest.cell_voltage_min,
        cell_voltage_max=latest.cell_voltage_max,
        coolant_temp=latest.coolant_temp,
        inverter_temp=latest.inverter_temp,
        fuel_level=latest.fuel_level,
        tyre_pressure_fl=latest.tyre_pressure_fl,
        tyre_pressure_fr=latest.tyre_pressure_fr,
        tyre_pressure_rl=latest.tyre_pressure_rl,
        tyre_pressure_rr=latest.tyre_pressure_rr,
        gps_lat=latest.gps_lat, gps_lon=latest.gps_lon, heading=latest.heading,
        accel_x=g_value, accel_y=0.0, accel_z=1.0,
        odometer_km=latest.odometer_km,
        trip_distance_km=latest.trip_distance_km,
        energy_per_100km=latest.energy_per_100km,
        brake_pad_wear_pct=latest.brake_pad_wear_pct,
        brake_fluid_level_pct=latest.brake_fluid_level_pct,
        charging_status=0, charging_current=0,
        estimated_range_km=latest.estimated_range_km,
        ambient_temp=latest.ambient_temp,
        aux_battery_voltage=latest.aux_battery_voltage,
        washer_fluid_level_pct=latest.washer_fluid_level_pct,
        cabin_temp=latest.cabin_temp,
        timestamp=datetime.utcnow(),
    )
    db.add(demo_sample)
    db.commit()
    db.refresh(demo_sample)

    event = check_for_crash(db, demo_sample, is_demo=True)

    if not event:
        combined_g = compute_combined_g(demo_sample.accel_x, demo_sample.accel_y, demo_sample.accel_z)
        return {"triggered": False, "combined_g": round(combined_g, 2), "message": "G-force did not exceed threshold."}

    return {
        "triggered": True,
        "accident_id": event.id,
        "severity": event.severity,
        "combined_g": event.combined_g_force,
        "status": event.status,
    }