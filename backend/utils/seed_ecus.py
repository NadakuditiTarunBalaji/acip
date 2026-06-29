from backend.config.database import SessionLocal
from backend.models.ecu import ECU

db = SessionLocal()

ecus = [
    ECU(
        ecu_id="ECU001",
        ecu_name="Engine Control Unit",
        function="Engine Management"
    ),
    ECU(
        ecu_id="ECU002",
        ecu_name="Brake Control Unit",
        function="ABS Control"
    ),
    ECU(
        ecu_id="ECU003",
        ecu_name="Battery Management System",
        function="Battery Monitoring"
    )
]

db.add_all(ecus)
db.commit()

print("ECU records inserted successfully!")

db.close()