from sqlalchemy import Column, String
from backend.config.database import Base

class DTC(Base):
    __tablename__ = "dtcs"

    dtc_id = Column(String, primary_key=True)
    description = Column(String)
    severity = Column(String)
    