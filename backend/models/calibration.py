from sqlalchemy import Column, String, Float
from backend.config.database import Base

class Calibration(Base):
    __tablename__ = "calibrations"

    cal_id = Column(String, primary_key=True)
    parameter = Column(String)
    value = Column(Float)
    unit = Column(String)