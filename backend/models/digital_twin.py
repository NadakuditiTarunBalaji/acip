from sqlalchemy import Column, String, Integer, DateTime, Text
from backend.config.database import Base
from datetime import datetime


class DigitalTwin(Base):
    __tablename__ = "digital_twins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String)
    twin_state = Column(Text)
    last_synced = Column(DateTime, default=datetime.utcnow)