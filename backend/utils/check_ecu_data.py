from backend.config.database import SessionLocal
from backend.models.ecu import ECU

db = SessionLocal()

ecus = db.query(ECU).all()

print(f"Total ECUs Found: {len(ecus)}")

for ecu in ecus:
    print(
        f"ID: {ecu.ecu_id}, "
        f"Name: {ecu.ecu_name}, "
        f"Function: {ecu.function}"
    )

db.close()