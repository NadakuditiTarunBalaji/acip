from backend.config.database import SessionLocal
from backend.models.dtc import DTC

db = SessionLocal()

dtcs = [
    DTC(
        dtc_id="DTC001",
        description="Engine Overheating",
        severity="High"
    ),
    DTC(
        dtc_id="DTC002",
        description="Low Battery Voltage",
        severity="Medium"
    ),
    DTC(
        dtc_id="DTC003",
        description="Wheel Speed Sensor Fault",
        severity="High"
    )
]

db.add_all(dtcs)
db.commit()

print("DTC records inserted successfully!")

db.close()