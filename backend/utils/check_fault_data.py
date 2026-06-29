from backend.config.database import SessionLocal
from backend.models.fault import Fault

db = SessionLocal()

faults = db.query(Fault).all()

print(f"Total Faults Found: {len(faults)}")

for fault in faults:
    print(
        f"ID: {fault.fault_id}, "
        f"Name: {fault.fault_name}, "
        f"Root Cause: {fault.root_cause}, "
        f"Severity: {fault.severity}"
    )

db.close()