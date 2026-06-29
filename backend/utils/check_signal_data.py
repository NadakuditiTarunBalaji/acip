from backend.config.database import SessionLocal
from backend.models.signal import Signal

db = SessionLocal()

signals = db.query(Signal).all()

print(f"Total Signals Found: {len(signals)}")

for signal in signals:
    print(
        f"ID: {signal.signal_id}, "
        f"Name: {signal.signal_name}, "
        f"Unit: {signal.unit}, "
        f"Range: {signal.min_value} - {signal.max_value}, "
        f"ECU: {signal.ecu_id}"
    )

db.close()