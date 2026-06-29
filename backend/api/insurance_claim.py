from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.config.database import get_db

from backend.services.insurance_service import (
    fetch_insurance,
    add_insurance_claim,
    modify_insurance_claim,
    remove_insurance_claim
)

router = APIRouter(
    prefix="/api/insurance",
    tags=["Insurance"]
)

# GET ALL
@router.get("/")
def get_insurance(
    db: Session = Depends(get_db)
):
    return fetch_insurance(db)


# CREATE
@router.post("/")
def create_insurance_api(
    claim_id: str,
    status: str,
    description: str,
    db: Session = Depends(get_db)
):
    return add_insurance_claim(
        db,
        claim_id,
        status,
        description
    )


# UPDATE
@router.put("/{claim_id}")
def update_insurance_api(
    claim_id: str,
    status: str,
    description: str,
    db: Session = Depends(get_db)
):
    return modify_insurance_claim(
        db,
        claim_id,
        status,
        description
    )


# DELETE
@router.delete("/{claim_id}")
def delete_insurance_api(
    claim_id: str,
    db: Session = Depends(get_db)
):
    return remove_insurance_claim(
        db,
        claim_id
    )