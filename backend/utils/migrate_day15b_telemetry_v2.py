"""
ACIP-X1 — Day 15b Migration (Telemetry v2)
Adds 15 new "crucial data" columns to the existing 'vehicle_telemetry' table:
  - Location & Motion : gps_lat, gps_lon, heading, accel_x, accel_y, accel_z
  - Odometer & Trip   : odometer_km, trip_distance_km, energy_per_100km
  - Brake System      : brake_pad_wear_pct, brake_fluid_level_pct
  - Charging & Range  : charging_status, charging_current, estimated_range_km
  - Environment       : ambient_temp

SAFE TO RE-RUN — only adds columns that don't already exist.
Does NOT delete or recreate the database (acip.db is untouched otherwise).

Usage:
    python -m backend.utils.migrate_day15b_telemetry_v2
"""
import sqlite3
import os

DB_PATH = os.path.join("database", "sqlite", "acip.db")

NEW_COLUMNS = {
    # Location & Motion
    "gps_lat": "REAL",
    "gps_lon": "REAL",
    "heading": "REAL",
    "accel_x": "REAL",
    "accel_y": "REAL",
    "accel_z": "REAL",
    # Odometer & Trip
    "odometer_km": "REAL",
    "trip_distance_km": "REAL",
    "energy_per_100km": "REAL",
    # Brake System
    "brake_pad_wear_pct": "REAL",
    "brake_fluid_level_pct": "REAL",
    # Charging & Range
    "charging_status": "INTEGER",
    "charging_current": "REAL",
    "estimated_range_km": "REAL",
    # Environment
    "ambient_temp": "REAL",
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
    print("  ACIP-X1 — Day 15b Telemetry Migration (v2)")
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