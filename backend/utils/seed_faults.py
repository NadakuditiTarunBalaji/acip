from backend.config.database import SessionLocal
from backend.models.fault import Fault

db = SessionLocal()

faults = [
    Fault(
        fault_id="FAULT001",
        fault_name="Engine Overheating",
        root_cause="Cooling System Failure",
        severity="High"
    ),
    Fault(
        fault_id="FAULT002",
        fault_name="Battery Drain",
        root_cause="Charging System Failure",
        severity="Medium"
    ),
    Fault(
        fault_id="FAULT003",
        fault_name="Brake Failure",
        root_cause="Hydraulic Pressure Loss",
        severity="Critical"
    )
]

db.add_all(faults)
db.commit()

print("Fault records inserted successfully!")

db.close()