"""
ACIP-X1 — Day 15e Migration (Trip Computer & Charging ETA)
Adds 3 new columns to vehicle_telemetry:
  - trip_duration_min  (elapsed time this trip/session, minutes)
  - avg_speed_kmh      (average speed this trip, km/h)
  - time_to_full_min   (estimated time to 100% SOC while charging, minutes)

SAFE TO RE-RUN — checks for existing columns before adding.
Does NOT touch any existing data.

Usage:
    python -m backend.utils.migrate_day15e_trip_computer
"""
import sqlite3
import os

DB_PATH = os.path.join("database", "sqlite", "acip.db")

NEW_COLUMNS = {
    "trip_duration_min": "REAL DEFAULT 0",
    "avg_speed_kmh": "REAL DEFAULT 0",
    "time_to_full_min": "REAL DEFAULT 0",
}


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}. Run init_db first.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 50)
    print("  ACIP-X1 — Day 15e Migration (Trip Computer)")
    print("=" * 50)

    cursor.execute("PRAGMA table_info(vehicle_telemetry)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    for col_name, col_def in NEW_COLUMNS.items():
        if col_name in existing_columns:
            print(f"  ⏭️  {col_name} already exists — skipping")
        else:
            cursor.execute(f"ALTER TABLE vehicle_telemetry ADD COLUMN {col_name} {col_def}")
            print(f"  ✅ Added column: {col_name}")

    conn.commit()
    conn.close()
    print("=" * 50)
    print("✅ Migration complete.")


if __name__ == "__main__":
    migrate()