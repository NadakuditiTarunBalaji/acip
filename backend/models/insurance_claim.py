from sqlalchemy import Column, String, Integer
from backend.config.database import Base


class InsuranceClaim(Base):
    __tablename__ = "insurance_claims"

    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_id = Column(String, unique=True)
    status = Column(String)
    description = Column(String)