"""Load data/sample-data.sql into the existing quiz tables."""

import sys
from pathlib import Path

import mysql.connector
from mysql.connector import Error

from personality_quiz.settings import ensure_settings


ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DATA_PATH = ROOT / "data" / "sample-data.sql"
REQUIRED_TABLES = (
    "personality_types",
    "questions",
    "answers",
    "quiz_results",
)


def seed_sample_data(connection) -> None:
    """Execute the sample SQL after confirming its target tables exist."""
    cursor = connection.cursor()
    try:
        cursor.execute("SHOW TABLES")
        existing_tables = {row[0] for row in cursor.fetchall()}
        missing_tables = sorted(set(REQUIRED_TABLES) - existing_tables)
        if missing_tables:
            raise RuntimeError(
                "Required quiz tables are missing: "
                + ", ".join(missing_tables)
                + ". Create them first: "
                "PYTHONPATH=src python scripts/create_tables.py"
            )

        sql = SAMPLE_DATA_PATH.read_text(encoding="utf-8")
        for statement in sql.split(";"):
            if statement.strip():
                cursor.execute(statement)
        connection.commit()
    except (Error, OSError, RuntimeError):
        connection.rollback()
        raise
    finally:
        cursor.close()


def main() -> None:
    """Load sample quiz content into the configured MySQL database."""
    try:
        settings = ensure_settings()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)

    try:
        connection = mysql.connector.connect(
            host=settings["DB_HOST"],
            port=int(settings["DB_PORT"]),
            user=settings["DB_USER"],
            password=settings["DB_PASSWORD"],
            database=settings["DB_NAME"],
        )
    except (Error, ValueError) as exc:
        print(f"Cannot connect to the MySQL database: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        seed_sample_data(connection)
        print(f"Sample data loaded from {SAMPLE_DATA_PATH}.")
    except (Error, OSError, RuntimeError) as exc:
        print(f"Failed to load sample data: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        connection.close()


if __name__ == "__main__":
    main()

