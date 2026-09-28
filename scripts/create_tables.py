"""Create the MySQL tables used by the personality quiz application.

Fails if any of the required tables already exist. To reset, remove the
existing tables or recreate the database first.
"""

import sys

import mysql.connector
from mysql.connector import Error

from personality_quiz.settings import ensure_settings


REQUIRED_TABLES = ("questions", "personality_types", "answers", "quiz_results")

CREATE_TABLES_SQL = """
CREATE TABLE questions (
    question_ID TINYINT PRIMARY KEY,
    question_text VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE personality_types (
    personality_ID TINYINT PRIMARY KEY,
    personality_type VARCHAR(100) NOT NULL,
    description VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE answers (
    answer_ID TINYINT PRIMARY KEY,
    question_ID INT NOT NULL,
    answer_text VARCHAR(255) NOT NULL,
    personality_ID TINYINT NOT NULL,
    CONSTRAINT fk_answers_question
        FOREIGN KEY (question_ID)
        REFERENCES questions(question_ID),
    CONSTRAINT fk_answers_personality
        FOREIGN KEY (personality_ID)
        REFERENCES personality_types(personality_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE quiz_results (
    results_ID TINYINT PRIMARY KEY,
    personality_ID TINYINT NOT NULL,
    person_name VARCHAR(100) NOT NULL,
    completed_date DATE NOT NULL,
    CONSTRAINT fk_quiz_results_personality
        FOREIGN KEY (personality_ID)
        REFERENCES personality_types(personality_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def _tables_exist(cursor) -> bool:
    """Return whether any required quiz tables already exist."""
    cursor.execute("SHOW TABLES")
    existing_tables = {row[0] for row in cursor.fetchall()}
    return any(table_name in existing_tables for table_name in REQUIRED_TABLES)


def main() -> None:
    """Create the quiz schema if it does not already exist."""
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
            if _tables_exist(cursor):
                print(
                    "One or more quiz tables already exist. "
                    "Delete or recreate the database before running this script again.",
                    file=sys.stderr,
                )
                sys.exit(1)

            cursor.execute(CREATE_TABLES_SQL)

        print("MySQL tables created successfully.")
    except Error as exc:
        print(f"Failed to create MySQL tables: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
