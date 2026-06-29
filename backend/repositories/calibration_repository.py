from sqlalchemy.orm import Session

from backend.models.calibration import Calibration


def get_all_calibrations(db: Session):
    return db.query(Calibration).all()


def get_calibration_by_id(db: Session, cal_id: str):
    return (
        db.query(Calibration)
        .filter(Calibration.cal_id == cal_id)
        .first()
    )


def create_calibration(
    db: Session,
    cal_id: str,
    parameter: str,
    value: float,
    unit: str
):
    calibration = Calibration(
        cal_id=cal_id,
        parameter=parameter,
        value=value,
        unit=unit
    )

    db.add(calibration)
    db.commit()
    db.refresh(calibration)

    return calibration


def update_calibration(
    db: Session,
    cal_id: str,
    parameter: str,
    value: float,
    unit: str
):
    calibration = (
        db.query(Calibration)
        .filter(Calibration.cal_id == cal_id)
        .first()
    )

    if calibration:
        calibration.parameter = parameter
        calibration.value = value
        calibration.unit = unit

        db.commit()
        db.refresh(calibration)

    return calibration


def delete_calibration(db: Session, cal_id: str):
    calibration = (
        db.query(Calibration)
        .filter(Calibration.cal_id == cal_id)
        .first()
    )

    if calibration:
        db.delete(calibration)
        db.commit()

    return calibration