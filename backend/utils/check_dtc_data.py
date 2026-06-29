from backend.config.database import SessionLocal
from backend.models.dtc import DTC

db = SessionLocal()

dtcs = db.query(DTC).all()

print(f"Total DTCs Found: {len(dtcs)}")

for dtc in dtcs:
    print(
        f"ID: {dtc.dtc_id}, "
        f"Description: {dtc.description}, "
        f"Severity: {dtc.severity}"
    )

db.close()