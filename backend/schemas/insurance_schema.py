from pydantic import BaseModel
from typing import Optional


class InsuranceClaimBase(BaseModel):
    claim_id: str
    status: str
    description: str


class InsuranceClaimCreate(InsuranceClaimBase):
    pass


class InsuranceClaimUpdate(BaseModel):
    status: Optional[str] = None
    description: Optional[str] = None


class InsuranceClaimResponse(InsuranceClaimBase):
    class Config:
        from_attributes = True


class InsurancePolicyBase(BaseModel):
    policy_id: str
    vehicle_id: str
    provider: str
    coverage_type: str
    premium_amount: float
    status: str


class InsurancePolicyCreate(InsurancePolicyBase):
    pass


class InsurancePolicyUpdate(BaseModel):
    provider: Optional[str] = None
    coverage_type: Optional[str] = None
    premium_amount: Optional[float] = None
    status: Optional[str] = None


class InsurancePolicyResponse(InsurancePolicyBase):
    class Config:
        from_attributes = True