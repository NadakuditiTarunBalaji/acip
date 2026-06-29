from pydantic import BaseModel
from typing import Optional


class RequirementBase(BaseModel):
    req_id: str
    description: str
    category: str
    system: str


class RequirementCreate(RequirementBase):
    pass


class RequirementUpdate(BaseModel):
    description: Optional[str] = None
    category: Optional[str] = None
    system: Optional[str] = None


class RequirementResponse(RequirementBase):
    class Config:
        from_attributes = True