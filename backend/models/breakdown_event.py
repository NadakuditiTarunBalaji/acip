from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from backend.config.database import Base
from datetime import datetime


class BreakdownEvent(Base):
    """
    A breakdown incident — either auto-detected from telemetry (stopped
    + critical fault, not charging) or manually reported by the owner
    pressing "I broke down" (Day 19 / C5).
    """
    __tablename__ = "breakdown_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String, index=True)
    detected_at = Column(DateTime, default=datetime.utcnow)
    trigger = Column(String)          # "Automatic" or "Manual"
    gps_lat = Column(Float, nullable=True)
    gps_lon = Column(Float, nullable=True)
    root_cause_json = Column(Text, nullable=True)     # JSON: the top critical issue, if any
    guidance_json = Column(Text)                       # JSON list: step-by-step instructions
    nearest_help_json = Column(Text)                   # JSON list: simulated nearby service contacts
    conversation_json = Column(Text, nullable=True)    # JSON list: chat messages with the AI assistant
    status = Column(String, default="Active")          # "Active" | "Resolved"
    resolved_at = Column(DateTime, nullable=True)