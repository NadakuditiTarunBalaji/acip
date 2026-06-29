from pydantic import BaseModel
from typing import Optional


class CalibrationBase(BaseModel):
    cal_id: str
    parameter: str
    value: float
    unit: str


class CalibrationCreate(CalibrationBase):
    pass


class CalibrationUpdate(BaseModel):
    parameter: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None


class CalibrationResponse(CalibrationBase):
    class Config:
        from_attributes = True