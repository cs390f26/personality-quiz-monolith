import mysql.connector

from personality_quiz.settings import ensure_settings


class DatabaseUnavailableError(Exception):
    """Raised when the MySQL database cannot be reached."""


def get_connection():
    """Create and return a connection to the MySQL database."""
    settings = ensure_settings()
    return mysql.connector.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME
    )


def ping() -> None:
    """Check that MySQL can be reached."""
    connection = get_connection()
    try:
        connection.ping(reconnect=True, attempts=3, delay=5)
    except mysql.connector.Error:
        raise DatabaseUnavailableError("Cannot reach the MySQL database.")
    finally:
        connection.close()


def get_questions():
    """Return all quiz questions."""
    pass


def get_answers(question_id):
    """Return the answer choices for one question."""
    pass


def save_result(person_id, personality_type_id):
    """Store a completed quiz result."""
    pass


def get_statistics():
    """Return aggregate personality quiz statistics."""
    pass