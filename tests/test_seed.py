import runpy
from unittest.mock import Mock

import mysql.connector
import pytest

from scripts import seed


def _connection_with_tables():
    connection = Mock()
    cursor = connection.cursor.return_value
    cursor.fetchall.return_value = [(table,) for table in seed.REQUIRED_TABLES]
    return connection, cursor


def test_seed_sample_data_executes_sql_and_commits():
    connection, cursor = _connection_with_tables()

    seed.seed_sample_data(connection)

    statements = [call.args[0] for call in cursor.execute.call_args_list]
    assert statements[0] == "SHOW TABLES"
    inserts = [statement for statement in statements[1:] if "INSERT IGNORE" in statement]
    assert len(inserts) == 3
    personality_insert = next(
        statement
        for statement in statements[1:]
        if "INSERT INTO personality_types" in statement
    )
    assert (
        "ON DUPLICATE KEY UPDATE description = VALUES(description)"
        in personality_insert
    )
    connection.commit.assert_called_once_with()
    connection.rollback.assert_not_called()
    cursor.close.assert_called_once_with()


def test_seed_sample_data_rejects_missing_tables():
    connection = Mock()
    cursor = connection.cursor.return_value
    cursor.fetchall.return_value = [("questions",)]

    with pytest.raises(RuntimeError, match="Required quiz tables are missing"):
        seed.seed_sample_data(connection)

    assert cursor.execute.call_count == 1
    connection.rollback.assert_called_once_with()
    connection.commit.assert_not_called()
    cursor.close.assert_called_once_with()


def test_seed_sample_data_lists_all_missing_tables_in_sorted_order():
    connection = Mock()
    cursor = connection.cursor.return_value
    cursor.fetchall.return_value = []

    with pytest.raises(RuntimeError) as error:
        seed.seed_sample_data(connection)

    assert "answers, personality_types, questions, quiz_results" in str(error.value)
    connection.rollback.assert_called_once_with()
    connection.commit.assert_not_called()
    cursor.close.assert_called_once_with()


def test_seed_sample_data_skips_empty_sql_statements(monkeypatch, tmp_path):
    connection, cursor = _connection_with_tables()
    sql_file = tmp_path / "sample.sql"
    sql_file.write_text(" ;\nINSERT INTO questions VALUES (1); \n ;", encoding="utf-8")
    monkeypatch.setattr(seed, "SAMPLE_DATA_PATH", sql_file)

    seed.seed_sample_data(connection)

    assert [call.args[0] for call in cursor.execute.call_args_list] == [
        "SHOW TABLES",
        "\nINSERT INTO questions VALUES (1)",
    ]
    connection.commit.assert_called_once_with()
    connection.rollback.assert_not_called()
    cursor.close.assert_called_once_with()


def test_seed_sample_data_rolls_back_and_closes_cursor_when_query_fails():
    connection = Mock()
    cursor = connection.cursor.return_value
    cursor.execute.side_effect = mysql.connector.Error("query failed")

    with pytest.raises(mysql.connector.Error, match="query failed"):
        seed.seed_sample_data(connection)

    connection.rollback.assert_called_once_with()
    connection.commit.assert_not_called()
    cursor.close.assert_called_once_with()


def test_seed_sample_data_rolls_back_when_an_insert_fails():
    connection, cursor = _connection_with_tables()
    cursor.execute.side_effect = [
        None,
        None,
        mysql.connector.Error("insert failed"),
    ]

    with pytest.raises(mysql.connector.Error, match="insert failed"):
        seed.seed_sample_data(connection)

    assert cursor.execute.call_count == 3
    connection.rollback.assert_called_once_with()
    connection.commit.assert_not_called()
    cursor.close.assert_called_once_with()


def test_seed_sample_data_rolls_back_when_commit_fails():
    connection, cursor = _connection_with_tables()
    connection.commit.side_effect = mysql.connector.Error("commit failed")

    with pytest.raises(mysql.connector.Error, match="commit failed"):
        seed.seed_sample_data(connection)

    connection.commit.assert_called_once_with()
    connection.rollback.assert_called_once_with()
    cursor.close.assert_called_once_with()


def test_seed_sample_data_rolls_back_and_closes_cursor_when_sql_cannot_be_read(
    monkeypatch,
):
    connection, cursor = _connection_with_tables()
    monkeypatch.setattr(
        seed,
        "SAMPLE_DATA_PATH",
        Mock(read_text=Mock(side_effect=OSError("file unavailable"))),
    )

    with pytest.raises(OSError, match="file unavailable"):
        seed.seed_sample_data(connection)

    connection.rollback.assert_called_once_with()
    connection.commit.assert_not_called()
    cursor.close.assert_called_once_with()


def test_main_exits_when_required_settings_are_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        seed, "ensure_settings", Mock(side_effect=RuntimeError("DB_HOST is required"))
    )
    connect = Mock()
    monkeypatch.setattr(seed.mysql.connector, "connect", connect)

    with pytest.raises(SystemExit) as exit_info:
        seed.main()

    assert exit_info.value.code == 1
    assert "DB_HOST is required" in capsys.readouterr().err
    connect.assert_not_called()


@pytest.mark.parametrize(
    ("port", "error", "connect_called"),
    [
        ("3307", mysql.connector.Error("connection refused"), True),
        ("not-a-port", None, False),
    ],
)
def test_main_exits_when_database_connection_fails(
    monkeypatch, capsys, port, error, connect_called
):
    settings = {
        "DB_HOST": "db.example.test",
        "DB_PORT": port,
        "DB_NAME": "quiz_test",
        "DB_USER": "quiz_user",
        "DB_PASSWORD": "secret",
    }
    monkeypatch.setattr(seed, "ensure_settings", lambda: settings)
    connect = Mock(side_effect=error)
    monkeypatch.setattr(seed.mysql.connector, "connect", connect)

    with pytest.raises(SystemExit) as exit_info:
        seed.main()

    assert exit_info.value.code == 1
    assert "Cannot connect to the MySQL database:" in capsys.readouterr().err
    if connect_called:
        connect.assert_called_once_with(
            host="db.example.test",
            port=3307,
            user="quiz_user",
            password="secret",
            database="quiz_test",
        )
    else:
        connect.assert_not_called()


def test_main_seeds_and_closes_database_connection(monkeypatch, capsys):
    settings = {
        "DB_HOST": "db.example.test",
        "DB_PORT": "3307",
        "DB_NAME": "quiz_test",
        "DB_USER": "quiz_user",
        "DB_PASSWORD": "secret",
    }
    connection = Mock()
    monkeypatch.setattr(seed, "ensure_settings", lambda: settings)
    connect = Mock(return_value=connection)
    monkeypatch.setattr(seed.mysql.connector, "connect", connect)
    seed_data = Mock()
    monkeypatch.setattr(seed, "seed_sample_data", seed_data)

    seed.main()

    connect.assert_called_once_with(
        host="db.example.test",
        port=3307,
        user="quiz_user",
        password="secret",
        database="quiz_test",
    )
    seed_data.assert_called_once_with(connection)
    connection.close.assert_called_once_with()
    assert "Sample data loaded from" in capsys.readouterr().out


@pytest.mark.parametrize(
    "error",
    [
        mysql.connector.Error("insert failed"),
        OSError("sample file unavailable"),
        RuntimeError("required table missing"),
    ],
)
def test_main_reports_seed_failure_and_closes_connection(monkeypatch, capsys, error):
    connection = Mock()
    monkeypatch.setattr(
        seed,
        "ensure_settings",
        lambda: {
            "DB_HOST": "db.example.test",
            "DB_PORT": "3307",
            "DB_NAME": "quiz_test",
            "DB_USER": "quiz_user",
            "DB_PASSWORD": "secret",
        },
    )
    monkeypatch.setattr(seed.mysql.connector, "connect", Mock(return_value=connection))
    monkeypatch.setattr(seed, "seed_sample_data", Mock(side_effect=error))

    with pytest.raises(SystemExit) as exit_info:
        seed.main()

    assert exit_info.value.code == 1
    assert "Failed to load sample data:" in capsys.readouterr().err
    connection.close.assert_called_once_with()


def test_script_entrypoint_runs_main_with_configured_database(monkeypatch, capsys):
    for key, value in {
        "DB_HOST": "db.example.test",
        "DB_PORT": "3307",
        "DB_NAME": "quiz_test",
        "DB_USER": "quiz_user",
        "DB_PASSWORD": "secret",
    }.items():
        monkeypatch.setenv(key, value)

    connection, cursor = _connection_with_tables()
    monkeypatch.setattr(seed.mysql.connector, "connect", Mock(return_value=connection))

    runpy.run_path(seed.__file__, run_name="__main__")

    connection.commit.assert_called_once_with()
    connection.close.assert_called_once_with()
    cursor.close.assert_called_once_with()
    assert "Sample data loaded from" in capsys.readouterr().out
