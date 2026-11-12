
import sqlite3
import os

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "careertrack.db"
)


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            company TEXT NOT NULL,
            position TEXT NOT NULL,
            status TEXT DEFAULT 'Applied',
            applied_date TEXT,
            notes TEXT,
            follow_up_date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Add new columns to an existing applications table
    cursor.execute("PRAGMA table_info(applications)")
    columns = [row["name"] for row in cursor.fetchall()]

    if "notes" not in columns:
        cursor.execute(
            "ALTER TABLE applications ADD COLUMN notes TEXT"
        )

    if "follow_up_date" not in columns:
        cursor.execute(
            "ALTER TABLE applications ADD COLUMN follow_up_date TEXT"
        )

    conn.commit()
    conn.close()


create_tables()
print("CareerTrack database ready!")
