import sqlite3
from pathlib import Path

DATABASE_PATH = Path("data/infrastructure.db")
SCHEMA_PATH = Path("app/db/schema.sql")


def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database() -> None:
    connection = get_connection()

    try:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        connection.executescript(schema)
        connection.commit()
    finally:
        connection.close()
