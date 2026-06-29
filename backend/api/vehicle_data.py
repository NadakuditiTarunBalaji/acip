from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.config.database import get_db

from backend.services.vehicle_service import (
    fetch_vehicle_data,
    add_vehicle,
    modify_vehicle_data,
    remove_vehicle_data
)

router = APIRouter(
    prefix="/api/vehicle-data",
    tags=["Vehicle Data"]
)

# GET ALL
@router.get("/")
def get_vehicle_data(
    db: Session = Depends(get_db)
):
    return fetch_vehicle_data(db)


# CREATE
@router.post("/")
def create_vehicle_api(
    rpm: float,
    battery_temp: float,
    coolant_temp: float,
    speed: float,
    db: Session = Depends(get_db)
):
    return add_vehicle(
        db,
        rpm,
        battery_temp,
        coolant_temp,
        speed
    )


# UPDATE
@router.put("/{vehicle_id}")
def update_vehicle_api(
    vehicle_id: int,
    rpm: float,
    battery_temp: float,
    coolant_temp: float,
    speed: float,
    db: Session = Depends(get_db)
):
    return modify_vehicle_data(
        db,
        vehicle_id,
        rpm,
        battery_temp,
        coolant_temp,
        speed
    )


# DELETE
@router.delete("/{vehicle_id}")
def delete_vehicle_api(
    vehicle_id: int,
    db: Session = Depends(get_db)
):
    return remove_vehicle_data(
        db,
        vehicle_id
    )