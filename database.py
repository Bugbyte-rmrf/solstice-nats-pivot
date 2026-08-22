import sqlite3
from pathlib import Path

DATABASE_PATH = Path("data/solstice.db")

def get_connection():
    DATABASE_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DATABASE_PATH)

def initialize_database():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS attendees (
            attendee_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            current_job_id TEXT,
            completed_job_id TEXT
        )
        """
    )

    attendees = [
        ("A001", "Alice Johnson"),
        ("A002", "Brian Smith"),
        ("A003", "Carla Davis"),
    ]

    for attendee_id, name in attendees:
        connection.execute(
            """
            INSERT OR IGNORE INTO attendees
            (
                attendee_id,
                name,
                status
            )
            VALUES (?, ?, 'NOT_CHECKED_IN')
            """,
            (attendee_id, name)
        )

    connection.commit()
    connection.close()
