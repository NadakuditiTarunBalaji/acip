from backend.config.database import SessionLocal
from backend.models.requirement import Requirement

db = SessionLocal()

requirements = [
    Requirement(
        req_id="REQ001",
        description="Brake Monitoring",
        category="Safety",
        system="ABS"
    ),
    Requirement(
        req_id="REQ002",
        description="Engine Temperature Monitoring",
        category="Powertrain",
        system="Engine"
    ),
    Requirement(
        req_id="REQ003",
        description="Battery Voltage Monitoring",
        category="Electrical",
        system="Battery"
    )
]

db.add_all(requirements)
db.commit()

print("Requirements inserted successfully!")

db.close()