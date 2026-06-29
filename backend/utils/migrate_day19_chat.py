"""
Migration: add conversation_json column to breakdown_events table
(Day 19 / C5 — real AI chat via Gemini).

Run once:
    python -m backend.utils.migrate_day19_chat
"""
import sqlite3
import os


def migrate():
    db_path = os.path.join("database", "sqlite", "acip.db")
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cols = [c[1] for c in conn.execute("PRAGMA table_info(breakdown_events)").fetchall()]

    if "conversation_json" in cols:
        print("⏭️  conversation_json already exists — nothing to do")
    else:
        conn.execute("ALTER TABLE breakdown_events ADD COLUMN conversation_json TEXT")
        conn.commit()
        print("✅ Added column: conversation_json")

    conn.close()


if __name__ == "__main__":
    migrate()