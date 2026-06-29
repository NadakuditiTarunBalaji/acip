from pydantic import BaseModel
from typing import Optional


class ECUBase(BaseModel):
    ecu_id: str
    ecu_name: str
    function: str


class ECUCreate(ECUBase):
    pass


class ECUUpdate(BaseModel):
    ecu_name: Optional[str] = None
    function: Optional[str] = None


class ECUResponse(ECUBase):
    class Config:
        from_attributes = True