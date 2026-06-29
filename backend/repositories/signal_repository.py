from sqlalchemy.orm import Session

from backend.models.signal import Signal


def get_all_signals(db: Session):
    return db.query(Signal).all()


def get_signal_by_id(db: Session, signal_id: str):
    return (
        db.query(Signal)
        .filter(Signal.signal_id == signal_id)
        .first()
    )


def create_signal(
    db: Session,
    signal_id: str,
    signal_name: str,
    unit: str,
    min_value: float,
    max_value: float,
    ecu_id: str

    
):
    signal = Signal(
        signal_id=signal_id,
        signal_name=signal_name,
        unit=unit,
        min_value=min_value,
        max_value=max_value,
        ecu_id=ecu_id
    )

    db.add(signal)
    db.commit()
    db.refresh(signal)

    return signal


def update_signal(
    db: Session,
    signal_id: str,
    signal_name: str,
    unit: str,
    min_value: float,
    max_value: float,
    ecu_id: str
):
    signal = (
        db.query(Signal)
        .filter(Signal.signal_id == signal_id)
        .first()
    )

    if signal:
        signal.signal_name = signal_name
        signal.unit = unit
        signal.min_value = min_value
        signal.max_value = max_value
        signal.ecu_id = ecu_id

        db.commit()
        db.refresh(signal)

    return signal


def delete_signal(db: Session, signal_id: str):
    signal = (
        db.query(Signal)
        .filter(Signal.signal_id == signal_id)
        .first()
    )

    if signal:
        db.delete(signal)
        db.commit()

    return signal