from sqlalchemy import Column, String
from backend.config.database import Base

class ECU(Base):
    __tablename__ = "ecus"

    ecu_id = Column(String, primary_key=True)
    ecu_name = Column(String)
    function = Column(String)