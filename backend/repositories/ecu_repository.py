from sqlalchemy.orm import Session

from backend.models.ecu import ECU


def get_all_ecus(db: Session):
    return db.query(ECU).all()


def get_ecu_by_id(db: Session, ecu_id: str):
    return (
        db.query(ECU)
        .filter(ECU.ecu_id == ecu_id)
        .first()
    )


def create_ecu(
    db: Session,
    ecu_id: str,
    ecu_name: str,
    function: str
):
    ecu = ECU(
        ecu_id=ecu_id,
        ecu_name=ecu_name,
        function=function
    )

    db.add(ecu)
    db.commit()
    db.refresh(ecu)

    return ecu


def update_ecu(
    db: Session,
    ecu_id: str,
    ecu_name: str,
    function: str
):
    ecu = (
        db.query(ECU)
        .filter(ECU.ecu_id == ecu_id)
        .first()
    )

    if ecu:
        ecu.ecu_name = ecu_name
        ecu.function = function

        db.commit()
        db.refresh(ecu)

    return ecu


def delete_ecu(db: Session, ecu_id: str):
    ecu = (
        db.query(ECU)
        .filter(ECU.ecu_id == ecu_id)
        .first()
    )

    if ecu:
        db.delete(ecu)
        db.commit()

    return ecu