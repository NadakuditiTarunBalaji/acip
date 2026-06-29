from sqlalchemy import Column, String, Float, Integer
from backend.config.database import Base


class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_id = Column(String, unique=True)
    vehicle_id = Column(String)
    provider = Column(String)
    coverage_type = Column(String)
    premium_amount = Column(Float)
    status = Column(String)