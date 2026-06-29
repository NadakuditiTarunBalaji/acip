"""
Migration: add sms_results_json column to accident_events table
(Day 18 / C4 — real SMS via Twilio).

Run once:
    python -m backend.utils.migrate_day18_sms
"""
import sqlite3
import os


def migrate():
    db_path = os.path.join("database", "sqlite", "acip.db")
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cols = [c[1] for c in conn.execute("PRAGMA table_info(accident_events)").fetchall()]

    if "sms_results_json" in cols:
        print("⏭️  sms_results_json already exists — nothing to do")
    else:
        conn.execute("ALTER TABLE accident_events ADD COLUMN sms_results_json TEXT")
        conn.commit()
        print("✅ Added column: sms_results_json")

    conn.close()


if __name__ == "__main__":
    migrate()