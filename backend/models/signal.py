from sqlalchemy import Column, String, Float
from backend.config.database import Base

class Signal(Base):
    __tablename__ = "signals"

    signal_id = Column(String, primary_key=True)
    signal_name = Column(String)
    unit = Column(String)
    min_value = Column(Float)
    max_value = Column(Float)
    ecu_id = Column(String)