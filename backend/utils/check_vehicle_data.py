from backend.config.database import SessionLocal
from backend.models.vehicle_data import VehicleData

db = SessionLocal()

records = db.query(VehicleData).all()

print(f"Total Vehicle Records Found: {len(records)}")

for record in records:
    print(
        f"ID: {record.id}, "
        f"RPM: {record.rpm}, "
        f"Battery Temp: {record.battery_temp}, "
        f"Coolant Temp: {record.coolant_temp}, "
        f"Speed: {record.speed}"
    )

db.close()