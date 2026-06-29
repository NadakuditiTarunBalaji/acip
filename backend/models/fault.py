from sqlalchemy import Column, String
from backend.config.database import Base

class Fault(Base):
    __tablename__ = "faults"

    fault_id = Column(String, primary_key=True)
    fault_name = Column(String)
    root_cause = Column(String)
    severity = Column(String)