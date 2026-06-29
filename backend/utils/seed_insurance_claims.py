from backend.config.database import SessionLocal
from backend.models.insurance_claim import InsuranceClaim

db = SessionLocal()

claims = [
    InsuranceClaim(
        claim_id="CLM001",
        status="Approved",
        description="Engine overheating damage"
    ),
    InsuranceClaim(
        claim_id="CLM002",
        status="Pending",
        description="Battery replacement claim"
    ),
    InsuranceClaim(
        claim_id="CLM003",
        status="Rejected",
        description="Wheel sensor failure claim"
    )
]

db.add_all(claims)
db.commit()

print("Insurance claim records inserted successfully!")

db.close()