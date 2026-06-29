from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.config.database import get_db
from backend.models.signal import Signal
from backend.services.signal_service import fetch_signals
from backend.repositories.signal_repository import (
    create_signal,
    update_signal,
    delete_signal
)

router = APIRouter(
    prefix="/api/signals",
    tags=["Signals"]
)


class SignalCreate(BaseModel):
    signal_id: str
    signal_name: str
    unit: str
    min_value: float
    max_value: float
    ecu_id: str


@router.get("/")
def get_signals(db: Session = Depends(get_db)):
    return fetch_signals(db)


@router.get("/{signal_id}")
def get_signal_by_id(signal_id: str, db: Session = Depends(get_db)):
    return db.query(Signal).filter(Signal.signal_id == signal_id).first()


@router.post("/")
def add_signal(signal: SignalCreate, db: Session = Depends(get_db)):
    return create_signal(db, signal.signal_id, signal.signal_name,
                         signal.unit, signal.min_value, signal.max_value, signal.ecu_id)


@router.put("/{signal_id}")
def edit_signal(signal_id: str, signal: SignalCreate, db: Session = Depends(get_db)):
    return update_signal(db, signal_id, signal.signal_name,
                         signal.unit, signal.min_value, signal.max_value, signal.ecu_id)


@router.delete("/{signal_id}")
def remove_signal(signal_id: str, db: Session = Depends(get_db)):
    return delete_signal(db, signal_id)