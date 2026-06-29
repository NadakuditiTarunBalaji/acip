"""
ACIP-X1 — Day 15 Migration
Adds new EV telemetry columns to the existing 'vehicle_telemetry' table.

SAFE TO RE-RUN — only adds columns that don't already exist.
Does NOT delete or recreate the database (acip.db is untouched otherwise).

Usage:
    python -m backend.utils.migrate_day15_telemetry
"""
import sqlite3
import os

DB_PATH = os.path.join("database", "sqlite", "acip.db")

NEW_COLUMNS = {
    "motor_torque": "REAL",
    "accelerator_position": "REAL",
    "regen_brake_level": "REAL",
    "battery_current": "REAL",
    "battery_temp": "REAL",
    "soc": "REAL",
    "soh": "REAL",
    "cell_voltage_min": "REAL",
    "cell_voltage_max": "REAL",
    "inverter_temp": "REAL",
}


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}. Run init_db first.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(vehicle_telemetry)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    if not existing_columns:
        print("❌ Table 'vehicle_telemetry' not found. Run init_db first.")
        conn.close()
        return

    print("=" * 50)
    print("  ACIP-X1 — Day 15 Telemetry Migration")
    print("=" * 50)

    added = []
    for col_name, col_type in NEW_COLUMNS.items():
        if col_name not in existing_columns:
            cursor.execute(
                f"ALTER TABLE vehicle_telemetry ADD COLUMN {col_name} {col_type}"
            )
            added.append(col_name)
            print(f"✅ Added column: {col_name} ({col_type})")
        else:
            print(f"⏭️  Column already exists: {col_name}")

    conn.commit()
    conn.close()

    print("-" * 50)
    if added:
        print(f"🎉 Migration complete — {len(added)} new column(s) added.")
    else:
        print("🎉 vehicle_telemetry already up to date — nothing to do.")
    print("=" * 50)


if __name__ == "__main__":
    migrate()