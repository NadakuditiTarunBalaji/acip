from backend.config.database import SessionLocal
from backend.repositories.requirement_repository import (
    get_all_requirements
)

db = SessionLocal()

requirements = get_all_requirements(db)

print(f"Total Records: {len(requirements)}")

for req in requirements:
    print(
        req.req_id,
        req.description,
        req.category,
        req.system
    )

db.close()