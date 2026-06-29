from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.config.database import get_db
from backend.models.calibration import Calibration
from backend.services.calibration_service import fetch_calibrations
from backend.repositories.calibration_repository import (
    create_calibration,
    update_calibration,
    delete_calibration
)

router = APIRouter(
    prefix="/api/calibrations",
    tags=["Calibrations"]
)


class CalibrationCreate(BaseModel):
    cal_id: str
    parameter: str
    value: float
    unit: str


@router.get("/")
def get_calibrations(db: Session = Depends(get_db)):
    return fetch_calibrations(db)


@router.get("/{cal_id}")
def get_calibration_by_id(cal_id: str, db: Session = Depends(get_db)):
    return db.query(Calibration).filter(Calibration.cal_id == cal_id).first()


@router.post("/")
def add_calibration(calibration: CalibrationCreate, db: Session = Depends(get_db)):
    return create_calibration(db, calibration.cal_id, calibration.parameter,
                              calibration.value, calibration.unit)


@router.put("/{cal_id}")
def edit_calibration(cal_id: str, calibration: CalibrationCreate, db: Session = Depends(get_db)):
    return update_calibration(db, cal_id, calibration.parameter,
                              calibration.value, calibration.unit)


@router.delete("/{cal_id}")
def remove_calibration(cal_id: str, db: Session = Depends(get_db)):
    return delete_calibration(db, cal_id)