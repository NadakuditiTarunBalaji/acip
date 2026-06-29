from backend.repositories.vehicle_repository import (
    get_all_vehicle_data,
    create_vehicle,
    update_vehicle_data,
    delete_vehicle_data
)

def fetch_vehicle_data(db):
    return get_all_vehicle_data(db)

def add_vehicle(
    db,
    rpm,
    battery_temp,
    coolant_temp,
    speed
):
    return create_vehicle(
        db,
        rpm,
        battery_temp,
        coolant_temp,
        speed
    )

def modify_vehicle_data(
    db,
    vehicle_id,
    rpm,
    battery_temp,
    coolant_temp,
    speed
):
    return update_vehicle_data(
        db,
        vehicle_id,
        rpm,
        battery_temp,
        coolant_temp,
        speed
    )

def remove_vehicle_data(
    db,
    vehicle_id
):
    return delete_vehicle_data(
        db,
        vehicle_id
    )