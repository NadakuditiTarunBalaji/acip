"""
ACIP-X1 — Vehicle Destination Model (Day 15d — Navigation)

Stores the customer's chosen destination for a vehicle. The CAN simulator
reads this to steer the simulated drive towards the destination; the
dashboard reads it to show distance remaining / ETA and plot it on the map.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from backend.config.database import Base


class VehicleDestination(Base):
    __tablename__ = "vehicle_destinations"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, unique=True, index=True)

    dest_name = Column(String)
    dest_lat = Column(Float)
    dest_lon = Column(Float)

    status = Column(String, default="active")  # active | arrived
    set_at = Column(DateTime, default=datetime.utcnow)