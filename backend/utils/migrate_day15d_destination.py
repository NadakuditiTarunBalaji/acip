"""
ACIP-X1 — Day 15d Migration (Navigation)
Creates the new 'vehicle_destinations' table used by the
destination/navigation feature.

SAFE TO RE-RUN — uses CREATE TABLE IF NOT EXISTS.
Does NOT touch any existing tables or data.

Usage:
    python -m backend.utils.migrate_day15d_destination
"""
import sqlite3
import os

DB_PATH = os.path.join("database", "sqlite", "acip.db")

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS vehicle_destinations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id VARCHAR UNIQUE,
    dest_name VARCHAR,
    dest_lat REAL,
    dest_lon REAL,
    status VARCHAR DEFAULT 'active',
    set_at DATETIME
)
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS ix_vehicle_destinations_vehicle_id
ON vehicle_destinations (vehicle_id)
"""


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}. Run init_db first.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 50)
    print("  ACIP-X1 — Day 15d Migration (Navigation)")
    print("=" * 50)

    cursor.execute(CREATE_SQL)
    cursor.execute(CREATE_INDEX_SQL)
    conn.commit()
    conn.close()

    print("✅ Table 'vehicle_destinations' ready.")
    print("=" * 50)


if __name__ == "__main__":
    migrate()