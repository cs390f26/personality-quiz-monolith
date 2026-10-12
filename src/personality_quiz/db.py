import mysql.connector

from personality_quiz.settings import ensure_settings


class DatabaseUnavailableError(Exception):
    """Raised when the MySQL database cannot be reached."""


def get_connection():
    """Create and return a connection to the MySQL database."""
    settings = ensure_settings()
    return mysql.connector.connect(
        host=settings["DB_HOST"],
        port=int(settings["DB_PORT"]),
        user=settings["DB_USER"],
        password=settings["DB_PASSWORD"],
        database=settings["DB_NAME"],
    )


def ping() -> None:
    """Check that MySQL can be reached."""
    connection = None
    try:
        connection = get_connection()
        connection.ping(reconnect=True, attempts=3, delay=5)
    except mysql.connector.Error as exc:
        raise DatabaseUnavailableError("Cannot reach the MySQL database.") from exc
    finally:
        if connection is not None:
            connection.close()


def get_questions():
    """Return all quiz questions."""
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT question_ID, question_text FROM questions ORDER BY question_ID"
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def get_answers(question_id):
    """Return the answer choices for one question."""
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT answer_ID, question_ID, answer_text, personality_ID "
            "FROM answers WHERE question_ID = %s ORDER BY answer_ID",
            (question_id,),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def save_result(person_id, personality_type_id):
    """Store a completed quiz result."""
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO quiz_results (personality_ID, person_name, completed_date) "
            "VALUES (%s, %s, CURDATE())",
            (personality_type_id, person_id),
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def get_statistics():
    """Return aggregate personality quiz statistics."""
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT pt.personality_type, COUNT(*) AS result_count "
            "FROM quiz_results qr "
            "JOIN personality_types pt ON pt.personality_ID = qr.personality_ID "
            "GROUP BY pt.personality_ID, pt.personality_type "
            "ORDER BY pt.personality_ID"
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()
