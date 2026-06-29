from sqlalchemy import Column, String, Integer
from backend.config.database import Base


class EmergencyContact(Base):
    """
    One or more emergency contacts per vehicle, used by the Accident
    Detection system (Day 18 / C4) to determine who gets notified when
    a crash is detected.
    """
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String, index=True)
    name = Column(String)
    relationship = Column(String)   # e.g. "Spouse", "Parent", "Friend"
    phone = Column(String)
    priority = Column(Integer, default=1)  # 1 = contacted first