from pydantic import BaseModel
from typing import Optional


class DTCBase(BaseModel):
    dtc_id: str
    description: str
    severity: str


class DTCCreate(DTCBase):
    pass


class DTCUpdate(BaseModel):
    description: Optional[str] = None
    severity: Optional[str] = None


class DTCResponse(DTCBase):
    class Config:
        from_attributes = True