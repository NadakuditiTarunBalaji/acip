from sqlalchemy import Column, String, Float, Integer, DateTime
from backend.config.database import Base
from datetime import datetime


class VehicleHealth(Base):
    __tablename__ = "vehicle_health"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String)
    health_score = Column(Float)
    status = Column(String)
    issues = Column(String)
    recommendation = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)