"""Apply schema.sql to the configured database. Run: python -m app.db.migrate"""
from __future__ import annotations

from pathlib import Path

from app.db.connection import close_pool, get_connection

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def run_migration() -> None:
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_connection() as conn:
        conn.execute(sql)
        conn.commit()
    print(f"Migration applied from {SCHEMA_PATH}")


if __name__ == "__main__":
    run_migration()
    close_pool()
