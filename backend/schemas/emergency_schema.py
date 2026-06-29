from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class EmergencyContactBase(BaseModel):
    vehicle_id: str
    name: str
    relationship: str
    phone: str
    priority: int = 1


class EmergencyContactCreate(EmergencyContactBase):
    pass


class EmergencyContactResponse(EmergencyContactBase):
    id: int

    class Config:
        from_attributes = True


class AccidentEventResponse(BaseModel):
    id: int
    vehicle_id: str
    detected_at: datetime
    gps_lat: Optional[float]
    gps_lon: Optional[float]
    speed_at_impact: Optional[float]
    combined_g_force: Optional[float]
    severity: Optional[str]
    status: str
    is_demo: bool

    class Config:
        from_attributes = True


class AccidentEventDetail(AccidentEventResponse):
    accel_x: Optional[float]
    accel_y: Optional[float]
    accel_z: Optional[float]
    contacts_notified: List[dict] = []
    nearby_vehicles_alerted: List[dict] = []
    resolved_at: Optional[datetime]


class NearbyDeviceResponse(BaseModel):
    id: int
    owner_name: str
    phone: str
    gps_lat: Optional[float]
    gps_lon: Optional[float]
    last_updated: datetime

    class Config:
        from_attributes = True