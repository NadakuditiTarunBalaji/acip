from backend.config.database import SessionLocal
from backend.models.vehicle_data import VehicleData

db = SessionLocal()

vehicle_records = [
    VehicleData(
        rpm=800,
        battery_temp=35,
        coolant_temp=85,
        speed=0
    ),
    VehicleData(
        rpm=2500,
        battery_temp=38,
        coolant_temp=92,
        speed=60
    ),
    VehicleData(
        rpm=3200,
        battery_temp=40,
        coolant_temp=96,
        speed=100
    )
]

db.add_all(vehicle_records)
db.commit()

print("Vehicle data inserted successfully!")

db.close()