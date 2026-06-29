from backend.config.database import SessionLocal
from backend.models.calibration import Calibration

db = SessionLocal()

calibrations = db.query(Calibration).all()

print(f"Total Calibrations Found: {len(calibrations)}")

for cal in calibrations:
    print(
        f"ID: {cal.cal_id}, "
        f"Parameter: {cal.parameter}, "
        f"Value: {cal.value}, "
        f"Unit: {cal.unit}"
    )

db.close()