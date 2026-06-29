from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from backend.config.database import Base
from datetime import datetime


class CANFrame(Base):
    __tablename__ = "can_frames"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String)
    can_id = Column(String)
    dlc = Column(Integer)
    raw_data = Column(String)
    decoded_data = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)