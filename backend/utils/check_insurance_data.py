from backend.config.database import SessionLocal
from backend.models.insurance_claim import InsuranceClaim

db = SessionLocal()

claims = db.query(InsuranceClaim).all()

print(f"Total Insurance Claims Found: {len(claims)}")

for claim in claims:
    print(
        f"ID: {claim.claim_id}, "
        f"Status: {claim.status}, "
        f"Description: {claim.description}"
    )

db.close()