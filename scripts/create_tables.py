"""Create any missing MySQL tables used by the personality quiz application."""

import sys

import mysql.connector
from mysql.connector import Error

from personality_quiz.settings import ensure_settings


REQUIRED_TABLES = (
    "questions",
    "personality_types",
    "answers",
    "quiz_results",
    "quiz_result_ties",
    "quiz_result_answers",
)

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS questions (
    question_ID TINYINT PRIMARY KEY,
    question_text VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS personality_types (
    personality_ID TINYINT PRIMARY KEY,
    personality_type VARCHAR(100) NOT NULL,
    description VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS answers (
    answer_ID TINYINT PRIMARY KEY,
    question_ID TINYINT NOT NULL,
    answer_text VARCHAR(255) NOT NULL,
    personality_ID TINYINT NOT NULL,
    CONSTRAINT fk_answers_question
        FOREIGN KEY (question_ID)
        REFERENCES questions(question_ID),
    CONSTRAINT fk_answers_personality
        FOREIGN KEY (personality_ID)
        REFERENCES personality_types(personality_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS quiz_results (
    results_ID INT AUTO_INCREMENT PRIMARY KEY,
    personality_ID TINYINT NOT NULL,
    person_name VARCHAR(100) NOT NULL,
    completed_date DATE NOT NULL,
    CONSTRAINT fk_quiz_results_personality
        FOREIGN KEY (personality_ID)
        REFERENCES personality_types(personality_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS quiz_result_ties (
    results_ID INT NOT NULL,
    personality_ID TINYINT NOT NULL,
    PRIMARY KEY (results_ID, personality_ID),
    CONSTRAINT fk_ties_result
        FOREIGN KEY (results_ID)
        REFERENCES quiz_results(results_ID) ON DELETE CASCADE,
    CONSTRAINT fk_ties_personality
        FOREIGN KEY (personality_ID)
        REFERENCES personality_types(personality_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS quiz_result_answers (
    results_ID INT NOT NULL,
    question_ID TINYINT NOT NULL,
    answer_ID TINYINT NOT NULL,
    PRIMARY KEY (results_ID, question_ID),
    CONSTRAINT fk_result_answers_result
        FOREIGN KEY (results_ID)
        REFERENCES quiz_results(results_ID) ON DELETE CASCADE,
    CONSTRAINT fk_result_answers_question
        FOREIGN KEY (question_ID)
        REFERENCES questions(question_ID),
    CONSTRAINT fk_result_answers_answer
        FOREIGN KEY (answer_ID)
        REFERENCES answers(answer_ID)
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
            for statement in CREATE_TABLES_SQL.split(";"):
                if statement.strip():
                    cursor.execute(statement)

        print("MySQL tables are ready.")
    except Error as exc:
        print(f"Failed to create MySQL tables: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
