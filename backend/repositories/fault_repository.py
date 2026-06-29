from sqlalchemy.orm import Session

from backend.models.fault import Fault


def get_all_faults(db: Session):
    return db.query(Fault).all()


def get_fault_by_id(db: Session, fault_id: str):
    return (
        db.query(Fault)
        .filter(Fault.fault_id == fault_id)
        .first()
    )


def create_fault(
    db: Session,
    fault_id: str,
    fault_name: str,
    root_cause: str,
    severity: str
):
    fault = Fault(
        fault_id=fault_id,
        fault_name=fault_name,
        root_cause=root_cause,
        severity=severity
    )

    db.add(fault)
    db.commit()
    db.refresh(fault)

    return fault


def update_fault(
    db: Session,
    fault_id: str,
    fault_name: str,
    root_cause: str,
    severity: str
):
    fault = (
        db.query(Fault)
        .filter(Fault.fault_id == fault_id)
        .first()
    )

    if fault:
        fault.fault_name = fault_name
        fault.root_cause = root_cause
        fault.severity = severity

        db.commit()
        db.refresh(fault)

    return fault


def delete_fault(db: Session, fault_id: str):
    fault = (
        db.query(Fault)
        .filter(Fault.fault_id == fault_id)
        .first()
    )

    if fault:
        db.delete(fault)
        db.commit()

    return fault