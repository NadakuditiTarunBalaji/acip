from backend.config.database import SessionLocal
from backend.models.requirement import Requirement

db = SessionLocal()

requirements = db.query(Requirement).all()

print(f"Total Requirements Found: {len(requirements)}")

for req in requirements:
    print(
        f"ID: {req.req_id}, "
        f"Description: {req.description}, "
        f"Category: {req.category}, "
        f"System: {req.system}"
    )

db.close()