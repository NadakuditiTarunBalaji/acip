from sqlalchemy import Column, String, Integer, Float, DateTime
from backend.config.database import Base
from datetime import datetime


class NearbyDevice(Base):
    """
    A phone running the ACIP-X1 app, sharing its location so it can
    receive a proximity push-alert if an accident is detected within
    ALERT_RADIUS_KM (Day 18 / C4). This is distinct from EmergencyContact:
    an emergency contact is someone tied to a specific vehicle who is
    always notified on a crash; a NearbyDevice is anyone with the app
    open who happens to be physically close when a crash happens —
    they don't need to know the vehicle owner at all in a real deployment.

    For the demo, we seed a couple of named devices (e.g. a friend's or
    colleague's phone) positioned near the vehicle's live GPS location so
    the radius alert has something real to find rather than always
    being empty.
    """
    __tablename__ = "nearby_devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_name = Column(String)
    phone = Column(String)
    gps_lat = Column(Float)
    gps_lon = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)