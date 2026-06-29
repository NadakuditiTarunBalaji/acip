"""
ACIP-X1 — Resale Value Maximizer API (Day 21 / C9)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.config.database import get_db
from backend.services.resale_value_service import get_resale_estimate, set_base_price
from backend.services.health_certificate_service import get_health_certificate

router = APIRouter(
    prefix="/api/resale",
    tags=["Resale Value Maximizer (C9)"]
)


class BasePriceRequest(BaseModel):
    base_price: int


@router.get("/estimate/{vehicle_id}")
def resale_estimate(vehicle_id: str, db: Session = Depends(get_db)):
    """Current estimated resale value, grounded in real health data,
    plus exactly what fixing active issues would recover."""
    return get_resale_estimate(db, vehicle_id)


@router.post("/base-price/{vehicle_id}")
def update_base_price(vehicle_id: str, body: BasePriceRequest, db: Session = Depends(get_db)):
    """Owner-entered base/current market price — the one input we
    can't derive from telemetry, since no real market pricing data
    is wired into this project."""
    return set_base_price(db, vehicle_id, body.base_price)


@router.get("/certificate/{vehicle_id}")
def health_certificate(vehicle_id: str, db: Session = Depends(get_db)):
    """The shareable AI Health Certificate — current health, incident
    track record, and resale estimate, all traceable to real recorded
    data rather than the seller's word."""
    return get_health_certificate(db, vehicle_id)