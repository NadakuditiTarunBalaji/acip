"""
Migration: add base_price column to vehicles table
(Day 21 / C9 — Resale Value Maximizer + Health Certificate).

Run once:
    python -m backend.utils.migrate_day21_resale
"""
import sqlite3
import os


def migrate():
    db_path = os.path.join("database", "sqlite", "acip.db")
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cols = [c[1] for c in conn.execute("PRAGMA table_info(vehicles)").fetchall()]

    if "base_price" in cols:
        print("⏭️  base_price already exists — nothing to do")
    else:
        conn.execute("ALTER TABLE vehicles ADD COLUMN base_price INTEGER")
        conn.commit()
        print("✅ Added column: base_price")

    conn.close()


if __name__ == "__main__":
    migrate()