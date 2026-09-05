"""
Centralized database connection handling.

Defaults to SQLite (zero setup, ships with Python) so the app runs
out of the box. Swap get_connection() for psycopg2 / mysql-connector
if you want Postgres or MySQL instead — every page and query file
only ever imports from here, so that's the only place to change.
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / os.getenv("DB_PATH", "data/cricbuzz_livestats.db")


def get_connection():
    """Return a raw sqlite3 connection with foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_cursor():
    """Context manager: yields a cursor, commits on success, closes always."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    finally:
        conn.close()


def run_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Run a SELECT and return a DataFrame. Used by the SQL Analytics page."""
    conn = get_connection()
    try:
        df = pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()
    return df


def execute_write(sql: str, params: tuple = ()) -> int:
    """Run an INSERT/UPDATE/DELETE. Returns affected row count."""
    with db_cursor() as cur:
        cur.execute(sql, params)
        return cur.rowcount


def init_schema():
    """Create tables if they don't exist yet, from data/schema.sql."""
    schema_path = BASE_DIR / "data" / "schema.sql"
    with open(schema_path, "r") as f:
        schema = f.read()
    conn = get_connection()
    try:
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_schema()
    print(f"Schema applied to {DB_PATH}")
