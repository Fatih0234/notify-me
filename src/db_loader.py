import os
import sqlite3


class DatabaseValidationError(Exception):
    pass


def load_db(path):
    """Validate SQLite file and return a connection."""
    if not os.path.exists(path):
        raise DatabaseValidationError(f"File not found: {path}")
    if os.path.getsize(path) == 0:
        raise DatabaseValidationError(f"File is empty: {path}")

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check")
    result = cursor.fetchone()
    if result[0] != "ok":
        conn.close()
        raise DatabaseValidationError(f"Integrity check failed for {path}: {result[0]}")

    return conn
