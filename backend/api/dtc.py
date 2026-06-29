from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.config.database import get_db
from backend.services.dtc_service import (
    fetch_dtcs,
    add_dtc,
    modify_dtc,
    remove_dtc
)

router = APIRouter(
    prefix="/api/dtcs",
    tags=["DTCs"]
)


class DTCCreate(BaseModel):
    dtc_id: str
    description: str
    severity: str


@router.get("/")
def get_dtcs(db: Session = Depends(get_db)):
    return fetch_dtcs(db)


@router.post("/")
def add_dtc_api(
    dtc: DTCCreate,
    db: Session = Depends(get_db)
):
    return add_dtc(
        db,
        dtc.dtc_id,
        dtc.description,
        dtc.severity
    )


@router.get("/{dtc_id}")
def get_dtc(
    dtc_id: str,
    db: Session = Depends(get_db)
):
    from backend.repositories.dtc_repository import get_dtc_by_id
    return get_dtc_by_id(db, dtc_id)


@router.put("/{dtc_id}")
def update_dtc_api(
    dtc_id: str,
    dtc: DTCCreate,
    db: Session = Depends(get_db)
):
    return modify_dtc(
        db,
        dtc_id,
        dtc.description,
        dtc.severity
    )


@router.delete("/{dtc_id}")
def delete_dtc_api(
    dtc_id: str,
    db: Session = Depends(get_db)
):
    return remove_dtc(
        db,
        dtc_id
    )