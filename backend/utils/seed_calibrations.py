from backend.config.database import SessionLocal
from backend.models.calibration import Calibration

db = SessionLocal()

calibrations = [
    Calibration(
        cal_id="CAL001",
        parameter="Engine Idle RPM",
        value=800,
        unit="RPM"
    ),
    Calibration(
        cal_id="CAL002",
        parameter="Battery Voltage Threshold",
        value=12.5,
        unit="V"
    ),
    Calibration(
        cal_id="CAL003",
        parameter="Coolant Temperature Limit",
        value=95,
        unit="C"
    )
]

db.add_all(calibrations)
db.commit()

print("Calibration records inserted successfully!")

db.close()