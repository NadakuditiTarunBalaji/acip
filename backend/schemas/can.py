from pydantic import BaseModel
from typing import Dict, Any


class CANFrameCreate(BaseModel):
    vehicle_id: int
    can_id: str
    dlc: int
    raw_data: str
    decoded_data: Dict[str, Any]