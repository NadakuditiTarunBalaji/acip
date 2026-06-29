from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text
from backend.config.database import Base
from datetime import datetime


class AccidentEvent(Base):
    """
    A logged accident/crash incident (Day 18 / C4).
    Created automatically when incoming telemetry shows a G-force spike
    above the crash threshold. Stores enough context (location, speed,
    G-force, timestamp) to review what happened, and tracks whether
    emergency contacts / nearby vehicles were notified.
    """
    __tablename__ = "accident_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String, index=True)

    detected_at = Column(DateTime, default=datetime.utcnow)
    gps_lat = Column(Float)
    gps_lon = Column(Float)
    speed_at_impact = Column(Float)
    combined_g_force = Column(Float)
    accel_x = Column(Float)
    accel_y = Column(Float)
    accel_z = Column(Float)

    severity = Column(String)   # "Moderate" | "Severe"
    status = Column(String, default="Detected")  # Detected -> Notified -> Resolved -> False Alarm

    contacts_notified_json = Column(Text)    # JSON list of contacts notified + how
    nearby_vehicles_alerted_json = Column(Text)  # JSON list of nearby vehicle_ids alerted
    sms_results_json = Column(Text, nullable=True)  # JSON: real Twilio SMS send results, if SMS_ENABLED

    resolved_at = Column(DateTime, nullable=True)
    is_demo = Column(Boolean, default=False)  # True if triggered via the demo/test endpoint