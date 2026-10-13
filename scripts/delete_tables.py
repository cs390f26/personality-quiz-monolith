import sys

import mysql.connector
from mysql.connector import Error

from personality_quiz.settings import ensure_settings
from scripts.create_tables import _tables_exist

REQUIRED_TABLES = (
    "questions",
    "personality_types",
    "answers",
    "quiz_results",
    "quiz_result_ties",
    "quiz_result_answers",
)

DELETE_TABLES_SQL = """
DROP TABLE IF EXISTS quiz_result_answers;
DROP TABLE IF EXISTS quiz_result_ties;
DROP TABLE IF EXISTS quiz_results;
DROP TABLE IF EXISTS answers;
DROP TABLE IF EXISTS personality_types;
DROP TABLE IF EXISTS questions;
"""


def main() -> None:
    """Delete the quiz tables if they exist."""
    try:
        settings = ensure_settings()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)

    connection = mysql.connector.connect(
        host=settings["DB_HOST"],
        port=int(settings["DB_PORT"]),
        user=settings["DB_USER"],
        password=settings["DB_PASSWORD"],
        database=settings["DB_NAME"],
        autocommit=True,
    )

    try:
        with connection.cursor() as cursor:
            if not _tables_exist(cursor):
                print(
                    "No quiz tables exist to delete.",
                    file=sys.stderr,
                )
                sys.exit(1)

            for statement in DELETE_TABLES_SQL.split(";"):
                if statement.strip():
                    cursor.execute(statement)

        print("MySQL tables deleted successfully.")
    except Error as exc:
        print(f"Failed to delete MySQL tables: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
