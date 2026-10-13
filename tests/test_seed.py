from unittest.mock import Mock

import pytest

from scripts import seed


def test_seed_sample_data_executes_sql_and_commits():
    connection = Mock()
    cursor = connection.cursor.return_value
    cursor.fetchall.return_value = [
        ("personality_types",),
        ("questions",),
        ("answers",),
        ("quiz_results",),
    ]

    seed.seed_sample_data(connection)

    statements = [call.args[0] for call in cursor.execute.call_args_list]
    assert statements[0] == "SHOW TABLES"
    inserts = [statement for statement in statements[1:] if "INSERT IGNORE" in statement]
    assert len(inserts) == 4
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

