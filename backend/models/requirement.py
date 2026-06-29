from sqlalchemy import Column, String
from backend.config.database import Base

class Requirement(Base):
    __tablename__ = "requirements"

    req_id = Column(String, primary_key=True)
    description = Column(String)
    category = Column(String)
    system = Column(String)