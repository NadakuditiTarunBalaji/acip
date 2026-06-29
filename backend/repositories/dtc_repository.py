from sqlalchemy.orm import Session

from backend.models.dtc import DTC


def get_all_dtcs(db: Session):
    return db.query(DTC).all()


def get_dtc_by_id(db: Session, dtc_id: str):
    return (
        db.query(DTC)
        .filter(DTC.dtc_id == dtc_id)
        .first()
    )


def create_dtc(
    db: Session,
    dtc_id: str,
    description: str,
    severity: str
):
    dtc = DTC(
        dtc_id=dtc_id,
        description=description,
        severity=severity
    )

    db.add(dtc)
    db.commit()
    db.refresh(dtc)

    return dtc


def update_dtc(
    db: Session,
    dtc_id: str,
    description: str,
    severity: str
):
    dtc = (
        db.query(DTC)
        .filter(DTC.dtc_id == dtc_id)
        .first()
    )

    if dtc:
        dtc.description = description
        dtc.severity = severity

        db.commit()
        db.refresh(dtc)

    return dtc


def delete_dtc(db: Session, dtc_id: str):
    dtc = (
        db.query(DTC)
        .filter(DTC.dtc_id == dtc_id)
        .first()
    )

    if dtc:
        db.delete(dtc)
        db.commit()

    return dtc