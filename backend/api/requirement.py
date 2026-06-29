from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.config.database import get_db
from backend.models.requirement import Requirement
from backend.services.requirement_service import fetch_requirements
from backend.repositories.requirement_repository import (
    create_requirement,
    update_requirement,
    delete_requirement
)

router = APIRouter(
    prefix="/api/requirements",
    tags=["Requirements"]
)


class RequirementCreate(BaseModel):
    req_id: str
    description: str
    category: str
    system: str


@router.get("/")
def get_requirements(db: Session = Depends(get_db)):
    return fetch_requirements(db)


@router.get("/{req_id}")
def get_requirement_by_id(req_id: str, db: Session = Depends(get_db)):
    return db.query(Requirement).filter(Requirement.req_id == req_id).first()


@router.post("/")
def add_requirement(requirement: RequirementCreate, db: Session = Depends(get_db)):
    return create_requirement(db, requirement.req_id, requirement.description,
                              requirement.category, requirement.system)


@router.put("/{req_id}")
def edit_requirement(req_id: str, requirement: RequirementCreate, db: Session = Depends(get_db)):
    return update_requirement(db, req_id, requirement.description,
                              requirement.category, requirement.system)


@router.delete("/{req_id}")
def remove_requirement(req_id: str, db: Session = Depends(get_db)):
    return delete_requirement(db, req_id)