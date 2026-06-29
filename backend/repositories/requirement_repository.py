from sqlalchemy.orm import Session

from backend.models.requirement import Requirement


def get_all_requirements(db: Session):
    return db.query(Requirement).all()


def get_requirement_by_id(db: Session, req_id: str):
    return (
        db.query(Requirement)
        .filter(Requirement.req_id == req_id)
        .first()
    )


def create_requirement(
    db: Session,
    req_id: str,
    description: str,
    category: str,
    system: str
):
    requirement = Requirement(
        req_id=req_id,
        description=description,
        category=category,
        system=system
    )

    db.add(requirement)
    db.commit()
    db.refresh(requirement)

    return requirement


def update_requirement(
    db: Session,
    req_id: str,
    description: str,
    category: str,
    system: str
):
    requirement = (
        db.query(Requirement)
        .filter(Requirement.req_id == req_id)
        .first()
    )

    if requirement:
        requirement.description = description
        requirement.category = category
        requirement.system = system

        db.commit()
        db.refresh(requirement)

    return requirement


def delete_requirement(db: Session, req_id: str):
    requirement = (
        db.query(Requirement)
        .filter(Requirement.req_id == req_id)
        .first()
    )

    if requirement:
        db.delete(requirement)
        db.commit()

    return requirement