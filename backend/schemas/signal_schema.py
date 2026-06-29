from pydantic import BaseModel
from typing import Optional


class SignalBase(BaseModel):
    signal_id: str
    signal_name: str
    unit: str
    min_value: float
    max_value: float
    ecu_id: str


class SignalCreate(SignalBase):
    pass


class SignalUpdate(BaseModel):
    signal_name: Optional[str] = None
    unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    ecu_id: Optional[str] = None


class SignalResponse(SignalBase):
    class Config:
        from_attributes = True