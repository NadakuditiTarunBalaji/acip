from sqlalchemy.orm import Session

from backend.models.vehicle_data import VehicleData


def get_all_vehicle_data(db: Session):
    return db.query(VehicleData).all()


def get_vehicle_data_by_id(db: Session, vehicle_id: int):
    return (
        db.query(VehicleData)
        .filter(VehicleData.id == vehicle_id)
        .first()
    )


def create_vehicle(
    db: Session,
    rpm: float,
    battery_temp: float,
    coolant_temp: float,
    speed: float
):
    vehicle_data = VehicleData(
        rpm=rpm,
        battery_temp=battery_temp,
        coolant_temp=coolant_temp,
        speed=speed
    )

    db.add(vehicle_data)
    db.commit()
    db.refresh(vehicle_data)

    return vehicle_data


def update_vehicle_data(
    db: Session,
    vehicle_id: int,
    rpm: float,
    battery_temp: float,
    coolant_temp: float,
    speed: float
):
    vehicle_data = (
        db.query(VehicleData)
        .filter(VehicleData.id == vehicle_id)
        .first()
    )

    if vehicle_data:
        vehicle_data.rpm = rpm
        vehicle_data.battery_temp = battery_temp
        vehicle_data.coolant_temp = coolant_temp
        vehicle_data.speed = speed

        db.commit()
        db.refresh(vehicle_data)

    return vehicle_data


def delete_vehicle_data(
    db: Session,
    vehicle_id: int
):
    vehicle_data = (
        db.query(VehicleData)
        .filter(VehicleData.id == vehicle_id)
        .first()
    )

    if vehicle_data:
        db.delete(vehicle_data)
        db.commit()

    return vehicle_data