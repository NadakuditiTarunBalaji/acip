from sqlalchemy.orm import Session

from backend.models.insurance_claim import InsuranceClaim


def get_all_insurance_claims(db: Session):
    return db.query(InsuranceClaim).all()


def get_insurance_claim_by_id(db: Session, claim_id: str):
    return (
        db.query(InsuranceClaim)
        .filter(InsuranceClaim.claim_id == claim_id)
        .first()
    )


def create_insurance_claim(
    db: Session,
    claim_id: str,
    status: str,
    description: str
):
    claim = InsuranceClaim(
        claim_id=claim_id,
        status=status,
        description=description
    )

    db.add(claim)
    db.commit()
    db.refresh(claim)

    return claim


def update_insurance_claim(
    db: Session,
    claim_id: str,
    status: str,
    description: str
):
    claim = (
        db.query(InsuranceClaim)
        .filter(InsuranceClaim.claim_id == claim_id)
        .first()
    )

    if claim:
        claim.status = status
        claim.description = description

        db.commit()
        db.refresh(claim)

    return claim


def delete_insurance_claim(db: Session, claim_id: str):
    claim = (
        db.query(InsuranceClaim)
        .filter(InsuranceClaim.claim_id == claim_id)
        .first()
    )

    if claim:
        db.delete(claim)
        db.commit()

    return claim