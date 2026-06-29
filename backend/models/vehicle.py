from sqlalchemy import Column, String, Integer
from backend.config.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vin = Column(String, unique=True)
    model = Column(String)
    manufacturer = Column(String)
    year = Column(Integer)
    owner_name = Column(String)
    owner_phone = Column(String)
    base_price = Column(Integer, nullable=True)  # owner-entered current/purchase value in INR, used for C9 resale estimate