from backend.config.database import SessionLocal
from backend.models.signal import Signal

db = SessionLocal()

signals = [
    Signal(
        signal_id="SIG001",
        signal_name="Engine Temperature",
        unit="C",
        min_value=-40,
        max_value=150,
        ecu_id="ECU001"
    ),
    Signal(
        signal_id="SIG002",
        signal_name="Battery Voltage",
        unit="V",
        min_value=0,
        max_value=24,
        ecu_id="ECU003"
    ),
    Signal(
        signal_id="SIG003",
        signal_name="Wheel Speed",
        unit="km/h",
        min_value=0,
        max_value=300,
        ecu_id="ECU002"
    )
]

db.add_all(signals)
db.commit()

print("Signal records inserted successfully!")

db.close()