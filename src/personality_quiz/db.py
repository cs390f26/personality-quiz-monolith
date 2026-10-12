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


def save_result(person_name, personality_type_id, *, tied_personality_ids=()):
    """Save one completed attempt and its additional tied winners atomically.

    The original personality_ID column keeps the first winner so existing
    single-category results and sample data remain valid.
    """
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO quiz_results (personality_ID, person_name, completed_date) "
            "VALUES (%s, %s, CURDATE())",
            (personality_type_id, person_name),
        )
        result_id = cursor.lastrowid
        for tied_id in tied_personality_ids:
            cursor.execute(
                "INSERT INTO quiz_result_ties (results_ID, personality_ID) "
                "VALUES (%s, %s)",
                (result_id, tied_id),
            )
        connection.commit()
        return result_id
    except mysql.connector.Error:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def get_result(result_id):
    """Return a saved attempt with all its winning categories, or None."""
    connection = get_connection()
    cursor = connection.cursor(dictionary=True, buffered=True)
    try:
        cursor.execute(
            "SELECT results_ID, personality_ID, person_name, completed_date "
            "FROM quiz_results WHERE results_ID = %s",
            (result_id,),
        )
        result = cursor.fetchone()
        if result is None:
            return None
        cursor.execute(
            "SELECT personality_ID, personality_type, description "
            "FROM personality_types WHERE personality_ID = %s "
            "OR personality_ID IN ("
            "SELECT personality_ID FROM quiz_result_ties WHERE results_ID = %s) "
            "ORDER BY personality_ID",
            (result["personality_ID"], result_id),
        )
        result["personalities"] = cursor.fetchall()
        return result
    finally:
        cursor.close()
        connection.close()


def get_statistics():
    """Count attempts once overall and once for each winning category.

    Return totals and category counts in the same query so they describe the
    same snapshot, including categories that have no completed results.
    """
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT pt.personality_ID, pt.personality_type, "
            "COUNT(winners.results_ID) AS result_count, "
            "(SELECT COUNT(*) FROM quiz_results) AS total_completed "
            "FROM personality_types pt LEFT JOIN ("
            "SELECT results_ID, personality_ID FROM quiz_results UNION "
            "SELECT results_ID, personality_ID FROM quiz_result_ties"
            ") winners ON pt.personality_ID = winners.personality_ID "
            "GROUP BY pt.personality_ID, pt.personality_type "
            "ORDER BY pt.personality_ID"
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()
