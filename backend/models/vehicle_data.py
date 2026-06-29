from sqlalchemy import Column, Integer, Float, DateTime
from backend.config.database import Base
from datetime import datetime

class VehicleData(Base):
    __tablename__ = "vehicle_data"

    id = Column(Integer, primary_key=True, autoincrement=True)

    rpm = Column(Float)
    battery_temp = Column(Float)
    coolant_temp = Column(Float)
    speed = Column(Float)

    timestamp = Column(DateTime, default=datetime.utcnow)