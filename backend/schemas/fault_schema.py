from pydantic import BaseModel
from typing import Optional


class FaultBase(BaseModel):
    fault_id: str
    fault_name: str
    root_cause: str
    severity: str


class FaultCreate(FaultBase):
    pass


class FaultUpdate(BaseModel):
    fault_name: Optional[str] = None
    root_cause: Optional[str] = None
    severity: Optional[str] = None


class FaultResponse(FaultBase):
    class Config:
        from_attributes = True