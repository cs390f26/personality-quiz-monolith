from unittest.mock import Mock

import mysql.connector
import pytest

from personality_quiz import db


@pytest.fixture
def database_connection(monkeypatch):
    """Provide a mocked MySQL connection and cursor for each test."""
    connection = Mock()
    cursor = connection.cursor.return_value
    monkeypatch.setattr(db, "get_connection", lambda: connection)
    return connection, cursor


def test_get_connection_uses_required_settings(monkeypatch):
    settings = {
        "DB_HOST": "db.example.test",
        "DB_PORT": "3307",
        "DB_NAME": "quiz_test",
        "DB_USER": "quiz_user",
        "DB_PASSWORD": "secret",
    }
    monkeypatch.setattr(db, "ensure_settings", lambda: settings)
    connect = Mock()
    monkeypatch.setattr(db.mysql.connector, "connect", connect)

    db.get_connection()

    connect.assert_called_once_with(
        host="db.example.test",
        port=3307,
        user="quiz_user",
        password="secret",
        database="quiz_test",
    )


def test_ping_succeeds_and_closes_connection(database_connection):
    connection, _ = database_connection

    assert db.ping() is None

    connection.ping.assert_called_once_with(
        reconnect=True,
        attempts=3,
        delay=5,
    )
    connection.close.assert_called_once_with()


def test_ping_raises_database_unavailable_when_mysql_ping_fails(
    database_connection,
):
    connection, _ = database_connection
    connection.ping.side_effect = mysql.connector.Error("connection lost")

    with pytest.raises(db.DatabaseUnavailableError, match="Cannot reach"):
        db.ping()

    connection.close.assert_called_once_with()


def test_get_questions_returns_all_rows_and_closes_resources(
    database_connection,
):
    connection, cursor = database_connection
    questions = [
        {"question_ID": 1, "question_text": "Which activity sounds most appealing?"},
        {"question_ID": 2, "question_text": "How do you approach a new problem?"},
    ]
    cursor.fetchall.return_value = questions

    result = db.get_questions()

    assert result == questions
    query = cursor.execute.call_args.args[0].lower()
    assert "select" in query
    assert "questions" in query
    cursor.close.assert_called_once_with()
    connection.close.assert_called_once_with()


def test_get_answers_returns_choices_for_requested_question(
    database_connection,
):
    connection, cursor = database_connection
    answers = [
        {
            "answer_ID": 1,
            "question_ID": 1,
            "answer_text": "Trying something exciting and spontaneous",
            "personality_ID": 1,
        },
        {
            "answer_ID": 2,
            "question_ID": 1,
            "answer_text": "Planning and completing an organized project",
            "personality_ID": 2,
        },
    ]
    cursor.fetchall.return_value = answers

    result = db.get_answers(1)

    assert result == answers
    query, parameters = cursor.execute.call_args.args
    assert "answers" in query.lower()
    assert "question_id" in query.lower()
    assert parameters == (1,)
    cursor.close.assert_called_once_with()
    connection.close.assert_called_once_with()


def test_get_answers_returns_empty_list_when_question_has_no_choices(
    database_connection,
):
    _, cursor = database_connection
    cursor.fetchall.return_value = []

    assert db.get_answers(999) == []


def test_save_result_inserts_name_and_personality_and_commits(
    database_connection,
):
    connection, cursor = database_connection

    db.save_result("Ada", 3)

    query, parameters = cursor.execute.call_args.args
    assert "insert into quiz_results" in query.lower()
    assert parameters == (3, "Ada")
    connection.commit.assert_called_once_with()
    cursor.close.assert_called_once_with()
    connection.close.assert_called_once_with()


def test_save_result_stores_selected_answers_in_the_same_transaction(
    database_connection,
):
    connection, cursor = database_connection

    db.save_result("Ada", 3, selected_answers=[(1, 4), (2, 7)])

    assert cursor.execute.call_count == 3
    query, parameters = cursor.execute.call_args_list[-1].args
    assert "insert into quiz_result_answers" in query.lower()
    assert parameters == (cursor.lastrowid, 2, 7)
    connection.commit.assert_called_once_with()


def test_get_result_answers_returns_selected_question_and_answer_text(
    database_connection,
):
    connection, cursor = database_connection
    answers = [
        {
            "question_ID": 1,
            "question_text": "Choose an activity",
            "answer_ID": 4,
            "answer_text": "Spend time with friends",
        }
    ]
    cursor.fetchall.return_value = answers

    assert db.get_result_answers(12) == answers

    query, parameters = cursor.execute.call_args.args
    assert "quiz_result_answers" in query
    assert parameters == (12,)
    cursor.close.assert_called_once_with()
    connection.close.assert_called_once_with()


def test_get_result_answers_returns_none_for_unknown_attempt(database_connection):
    _, cursor = database_connection
    cursor.fetchall.return_value = []

    assert db.get_result_answers(999) is None


def test_get_statistics_returns_aggregate_rows(database_connection):
    connection, cursor = database_connection
    statistics = [
        {"personality_type": "Orange", "result_count": 1},
        {"personality_type": "Green", "result_count": 2},
    ]
    cursor.fetchall.return_value = statistics

    assert db.get_statistics() == statistics

    query = cursor.execute.call_args.args[0].lower()
    assert "quiz_results" in query
    assert "personality_types" in query
    cursor.close.assert_called_once_with()
    connection.close.assert_called_once_with()