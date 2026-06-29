from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.config.database import get_db
from backend.services.fault_service import (
    fetch_faults,
    add_fault,
    modify_fault,
    remove_fault
)

router = APIRouter(
    prefix="/api/faults",
    tags=["Faults"]
)


class FaultCreate(BaseModel):
    fault_id: str
    fault_name: str
    root_cause: str
    severity: str


@router.get("/")
def get_faults(db: Session = Depends(get_db)):
    return fetch_faults(db)


@router.post("/")
def add_fault_api(
    fault: FaultCreate,
    db: Session = Depends(get_db)
):
    return add_fault(
        db,
        fault.fault_id,
        fault.fault_name,
        fault.root_cause,
        fault.severity
    )


@router.get("/{fault_id}")
def get_fault(
    fault_id: str,
    db: Session = Depends(get_db)
):
    from backend.repositories.fault_repository import get_fault_by_id
    return get_fault_by_id(db, fault_id)


@router.put("/{fault_id}")
def update_fault_api(
    fault_id: str,
    fault: FaultCreate,
    db: Session = Depends(get_db)
):
    return modify_fault(
        db,
        fault_id,
        fault.fault_name,
        fault.root_cause,
        fault.severity
    )


@router.delete("/{fault_id}")
def delete_fault_api(
    fault_id: str,
    db: Session = Depends(get_db)
):
    return remove_fault(
        db,
        fault_id
    )