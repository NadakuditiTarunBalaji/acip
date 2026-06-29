"""
ACIP-X1 — Day 15c Migration (Telemetry v3)
Adds 6 final "crucial data" columns to the existing 'vehicle_telemetry' table:
  - aux_battery_voltage    : 12V auxiliary battery voltage (V)
  - washer_fluid_level_pct : Windshield washer fluid level (%)
  - cabin_temp             : Cabin air temperature (C)
  - ac_setpoint_temp       : AC target/setpoint temperature (C)
  - headlamp_status        : 0=OK, 1=Fault/Bulb failure
  - dcdc_converter_temp    : DC-DC converter temperature (C)

SAFE TO RE-RUN — only adds columns that don't already exist.
Does NOT delete or recreate the database (acip.db is untouched otherwise).

Usage:
    python -m backend.utils.migrate_day15c_telemetry_v3
"""
import sqlite3
import os

DB_PATH = os.path.join("database", "sqlite", "acip.db")

NEW_COLUMNS = {
    "aux_battery_voltage": "REAL",
    "washer_fluid_level_pct": "REAL",
    "cabin_temp": "REAL",
    "ac_setpoint_temp": "REAL",
    "headlamp_status": "INTEGER",
    "dcdc_converter_temp": "REAL",
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
    print("  ACIP-X1 — Day 15c Telemetry Migration (v3)")
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