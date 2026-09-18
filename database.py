import sqlite3
from pathlib import Path

DATABASE = Path(__file__).resolve().parent / "lost_found.db"


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    db = get_db()

    # Main reports table
    db.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_type TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            category TEXT NOT NULL,
            report_date TEXT NOT NULL,
            contact TEXT,
            photo TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add latitude/longitude to an existing database
    columns = [
        row["name"]
        for row in db.execute("PRAGMA table_info(reports)").fetchall()
    ]

    if "latitude" not in columns:
        db.execute("ALTER TABLE reports ADD COLUMN latitude REAL")

    if "longitude" not in columns:
        db.execute("ALTER TABLE reports ADD COLUMN longitude REAL")

    # Match status table
    db.execute("""
        CREATE TABLE IF NOT EXISTS match_status (
            match_id TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'potential'
        )
    """)

    db.commit()
    db.close()


if __name__ == "__main__":
    init_db()
    print("Database created successfully!")