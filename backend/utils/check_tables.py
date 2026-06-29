from backend.config.database import SessionLocal
from backend.models.requirement import Requirement

db = SessionLocal()

count = db.query(Requirement).count()

print("Requirement Count =", count)

db.close()