from datetime import date
from unittest.mock import Mock

import mysql.connector
import pytest

from personality_quiz import db
from personality_quiz import app as app_module
from personality_quiz.app import create_app


def test_submit_quiz_saves_selected_answers_for_the_attempt(monkeypatch):
    app = create_app()
    app.config.update(TESTING=True)
    saved_result = {
        "results_ID": 42,
        "person_name": "Ada",
        "completed_date": date(2026, 10, 12),
        "personalities": [
            {
                "personality_ID": 1,
                "personality_type": "Orange",
                "description": "Energetic and spontaneous",
            }
        ],
    }
    monkeypatch.setattr(
        db,
        "get_questions",
        lambda: [{"question_ID": 1}, {"question_ID": 2}],
    )
    monkeypatch.setattr(
        db,
        "get_answers",
        lambda question_id: [
            {
                "answer_ID": question_id,
                "personality_ID": 1,
            }
        ],
    )
    save_result = Mock(return_value=42)
    monkeypatch.setattr(db, "save_result", save_result)
    monkeypatch.setattr(db, "get_result", lambda result_id: saved_result)

    response = app.test_client().post(
        "/quiz-results",
        json={
            "personName": "Ada",
            "selectedAnswers": [
                {"questionId": 1, "answerId": 1},
                {"questionId": 2, "answerId": 2},
            ],
        },
    )

    assert response.status_code == 201
    assert response.json["resultId"] == 42
    save_result.assert_called_once_with(
        "Ada",
        1,
        tied_personality_ids=[],
        selected_answers=[(1, 1), (2, 2)],
    )


def test_get_quiz_result_answers_returns_attempt_breakdown(monkeypatch):
    app = create_app()
    app.config.update(TESTING=True)
    monkeypatch.setattr(
        db,
        "get_result_answers",
        lambda result_id: [
            {
                "question_ID": 1,
                "question_text": "Choose an activity",
                "answer_ID": 4,
                "answer_text": "Spend time with friends",
            }
        ],
    )

    response = app.test_client().get("/quiz-results/42/answers")

    assert response.status_code == 200
    assert response.json == {
        "resultId": 42,
        "answers": [
            {
                "questionId": 1,
                "questionText": "Choose an activity",
                "answerId": 4,
                "answerText": "Spend time with friends",
            }
        ],
    }


def test_get_quiz_result_answers_returns_404_for_unknown_attempt(monkeypatch):
    app = create_app()
    app.config.update(TESTING=True)
    monkeypatch.setattr(db, "get_result_answers", lambda result_id: None)

    response = app.test_client().get("/quiz-results/999/answers")

    assert response.status_code == 404
    assert response.json["error"]["code"] == "NOT_FOUND"


def test_list_quiz_results_returns_attempts_with_all_winning_categories(monkeypatch):
    app = create_app()
    app.config.update(TESTING=True)
    monkeypatch.setattr(
        db,
        "get_result_history",
        lambda: [
            {
                "results_ID": 42,
                "person_name": "Ada",
                "completed_date": date(2026, 10, 12),
                "personality_type": "Blue",
            },
            {
                "results_ID": 42,
                "person_name": "Ada",
                "completed_date": date(2026, 10, 12),
                "personality_type": "Green",
            },
        ],
    )

    response = app.test_client().get("/quiz-results")

    assert response.status_code == 200
    assert response.json == {
        "results": [
            {
                "resultId": 42,
                "personName": "Ada",
                "completedDate": "2026-10-12",
                "personalities": ["Blue", "Green"],
            }
        ]
    }


def test_list_quiz_results_returns_empty_list_when_no_attempts_exist(monkeypatch):
    app = create_app()
    app.config.update(TESTING=True)
    monkeypatch.setattr(db, "get_result_history", lambda: [])

    response = app.test_client().get("/quiz-results")

    assert response.status_code == 200
    assert response.json == {"results": []}


@pytest.mark.parametrize("path", ["/", "/quiz", "/results", "/statistics-page"])
def test_page_routes_render_templates(path):
    app = create_app()
    app.config.update(TESTING=True)

    response = app.test_client().get(path)

    assert response.status_code == 200
    assert response.mimetype == "text/html"


def test_health_route_reports_database_availability(monkeypatch):
    app = create_app()
    app.config.update(TESTING=True)
    monkeypatch.setattr(db, "ping", lambda: None)

    response = app.test_client().get("/health")

    assert response.status_code == 200
    assert response.json == {"status": "ok"}


@pytest.mark.parametrize(
    "error",
    [
        db.DatabaseUnavailableError("database offline"),
        mysql.connector.Error("connection lost"),
    ],
)
def test_database_errors_return_service_unavailable(monkeypatch, error):
    app = create_app()
    app.config.update(TESTING=True)
    monkeypatch.setattr(db, "ping", Mock(side_effect=error))

    response = app.test_client().get("/health")

    assert response.status_code == 503
    assert response.json == {"status": "unavailable"}


def test_list_questions_returns_questions_with_answers(monkeypatch):
    app = create_app()
    app.config.update(TESTING=True)
    monkeypatch.setattr(
        db,
        "get_questions",
        lambda: [
            {"question_ID": 1, "question_text": "Choose an activity"},
            {"question_ID": 2, "question_text": "Pick a setting"},
        ],
    )
    monkeypatch.setattr(
        db,
        "get_answers",
        lambda question_id: [
            {
                "answer_ID": question_id + 10,
                "answer_text": f"Choice for question {question_id}",
            }
        ],
    )

    response = app.test_client().get("/questions")

    assert response.status_code == 200
    assert response.json == {
        "questions": [
            {
                "questionId": 1,
                "questionText": "Choose an activity",
                "answers": [
                    {"answerId": 11, "answerText": "Choice for question 1"}
                ],
            },
            {
                "questionId": 2,
                "questionText": "Pick a setting",
                "answers": [
                    {"answerId": 12, "answerText": "Choice for question 2"}
                ],
            },
        ]
    }


@pytest.mark.parametrize(
    ("body", "question_ids", "answers", "expected_message"),
    [
        (["not", "an", "object"], [1], {}, "JSON body required"),
        (
            {"selectedAnswers": [{"questionId": 1, "answerId": 1}]},
            [1],
            {},
            "personName is required",
        ),
        (
            {
                "personName": "A" * 101,
                "selectedAnswers": [{"questionId": 1, "answerId": 1}],
            },
            [1],
            {},
            "personName must be at most 100 characters",
        ),
        (
            {"personName": "Ada"},
            [1],
            {},
            "selectedAnswers must be a non-empty list",
        ),
        (
            {"personName": "Ada", "selectedAnswers": []},
            [1],
            {},
            "selectedAnswers must be a non-empty list",
        ),
        (
            {"personName": "Ada", "selectedAnswers": ["not an object"]},
            [1],
            {},
            "Each selection must contain questionId and answerId",
        ),
        (
            {
                "personName": "Ada",
                "selectedAnswers": [{"questionId": True, "answerId": 1}],
            },
            [1],
            {},
            "questionId must be a positive integer",
        ),
        (
            {
                "personName": "Ada",
                "selectedAnswers": [{"questionId": 1, "answerId": 0}],
            },
            [1],
            {},
            "answerId must be a positive integer",
        ),
        (
            {
                "personName": "Ada",
                "selectedAnswers": [
                    {"questionId": 1, "answerId": 1},
                    {"questionId": 1, "answerId": 1},
                ],
            },
            [1],
            {},
            "Only one answer may be submitted for each question",
        ),
        (
            {
                "personName": "Ada",
                "selectedAnswers": [{"questionId": 1, "answerId": 1}],
            },
            [1, 2],
            {},
            "One answer must be submitted for every quiz question",
        ),
        (
            {
                "personName": "Ada",
                "selectedAnswers": [{"questionId": 1, "answerId": 99}],
            },
            [1],
            {1: [{"answer_ID": 1, "personality_ID": 1}]},
            "The selected answer is not valid for the specified question",
        ),
    ],
)
def test_submit_quiz_rejects_invalid_submissions(
    monkeypatch, body, question_ids, answers, expected_message
):
    app = create_app()
    app.config.update(TESTING=True)
    monkeypatch.setattr(
        db,
        "get_questions",
        lambda: [{"question_ID": question_id} for question_id in question_ids],
    )
    monkeypatch.setattr(db, "get_answers", lambda question_id: answers.get(question_id, []))
    save_result = Mock()
    monkeypatch.setattr(db, "save_result", save_result)

    response = app.test_client().post("/quiz-results", json=body)

    assert response.status_code == 400
    assert response.json["error"]["code"] == "BAD_REQUEST"
    assert response.json["error"]["message"] == expected_message
    save_result.assert_not_called()


def test_submit_quiz_rejects_submission_when_quiz_has_no_questions(monkeypatch):
    app = create_app()
    app.config.update(TESTING=True)
    monkeypatch.setattr(db, "get_questions", lambda: [])
    save_result = Mock()
    monkeypatch.setattr(db, "save_result", save_result)

    response = app.test_client().post(
        "/quiz-results",
        json={
            "personName": "Ada",
            "selectedAnswers": [{"questionId": 1, "answerId": 1}],
        },
    )

    assert response.status_code == 400
    assert response.json["error"]["message"] == (
        "One answer must be submitted for every quiz question"
    )
    save_result.assert_not_called()


def test_submit_quiz_returns_all_personalities_when_scores_are_tied(monkeypatch):
    app = create_app()
    app.config.update(TESTING=True)
    monkeypatch.setattr(
        db,
        "get_questions",
        lambda: [{"question_ID": 1}, {"question_ID": 2}],
    )
    monkeypatch.setattr(
        db,
        "get_answers",
        lambda question_id: [
            {"answer_ID": question_id, "personality_ID": question_id}
        ],
    )
    saved_result = {
        "results_ID": 43,
        "person_name": "Ada",
        "completed_date": date(2026, 10, 13),
        "personalities": [
            {
                "personality_ID": 1,
                "personality_type": "Blue",
                "description": "Thoughtful and empathetic",
            },
            {
                "personality_ID": 2,
                "personality_type": "Green",
                "description": "Analytical and curious",
            },
        ],
    }
    save_result = Mock(return_value=43)
    monkeypatch.setattr(db, "save_result", save_result)
    monkeypatch.setattr(db, "get_result", lambda result_id: saved_result)

    response = app.test_client().post(
        "/quiz-results",
        json={
            "personName": "Ada",
            "selectedAnswers": [
                {"questionId": 1, "answerId": 1},
                {"questionId": 2, "answerId": 2},
            ],
        },
    )

    assert response.status_code == 201
    assert response.json == {
        "resultId": 43,
        "personName": "Ada",
        "completedDate": "2026-10-13",
        "isTie": True,
        "personalities": [
            {
                "personalityId": 1,
                "personalityType": "Blue",
                "description": "Thoughtful and empathetic",
            },
            {
                "personalityId": 2,
                "personalityType": "Green",
                "description": "Analytical and curious",
            },
        ],
    }
    save_result.assert_called_once_with(
        "Ada",
        1,
        tied_personality_ids=[2],
        selected_answers=[(1, 1), (2, 2)],
    )


def test_get_quiz_result_returns_a_tied_result(monkeypatch):
    app = create_app()
    app.config.update(TESTING=True)
    monkeypatch.setattr(
        db,
        "get_result",
        lambda result_id: {
            "results_ID": result_id,
            "person_name": "Ada",
            "completed_date": date(2026, 10, 13),
            "personalities": [
                {
                    "personality_ID": 1,
                    "personality_type": "Blue",
                    "description": "Thoughtful and empathetic",
                },
                {
                    "personality_ID": 2,
                    "personality_type": "Green",
                    "description": "Analytical and curious",
                },
            ],
        },
    )

    response = app.test_client().get("/quiz-results/43")

    assert response.status_code == 200
    assert response.json["resultId"] == 43
    assert response.json["isTie"] is True
    assert [item["personalityType"] for item in response.json["personalities"]] == [
        "Blue",
        "Green",
    ]


def test_get_quiz_result_returns_404_for_unknown_attempt(monkeypatch):
    app = create_app()
    app.config.update(TESTING=True)
    monkeypatch.setattr(db, "get_result", lambda result_id: None)

    response = app.test_client().get("/quiz-results/999")

    assert response.status_code == 404
    assert response.json == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Requested resource not found",
        }
    }


@pytest.mark.parametrize(
    ("rows", "expected"),
    [
        (
            [
                {
                    "personality_ID": 1,
                    "personality_type": "Orange",
                    "result_count": 1,
                    "total_completed": 4,
                },
                {
                    "personality_ID": 2,
                    "personality_type": "Blue",
                    "result_count": 3,
                    "total_completed": 4,
                },
            ],
            {
                "totalCompleted": 4,
                "personalityTypes": [
                    {
                        "personalityId": 1,
                        "personalityType": "Orange",
                        "count": 1,
                        "percentage": 25.0,
                    },
                    {
                        "personalityId": 2,
                        "personalityType": "Blue",
                        "count": 3,
                        "percentage": 75.0,
                    },
                ],
            },
        ),
        (
            [
                {
                    "personality_ID": 1,
                    "personality_type": "Orange",
                    "result_count": 0,
                    "total_completed": 0,
                }
            ],
            {
                "totalCompleted": 0,
                "personalityTypes": [
                    {
                        "personalityId": 1,
                        "personalityType": "Orange",
                        "count": 0,
                        "percentage": 0.0,
                    }
                ],
            },
        ),
        ([], {"totalCompleted": 0, "personalityTypes": []}),
    ],
)
def test_statistics_returns_aggregates_and_handles_zero_totals(monkeypatch, rows, expected):
    app = create_app()
    app.config.update(TESTING=True)
    monkeypatch.setattr(db, "get_statistics", lambda: rows)

    response = app.test_client().get("/statistics")

    assert response.status_code == 200
    assert response.json == expected


def test_launch_checks_database_before_creating_app(monkeypatch):
    flask_app = create_app()
    ping = Mock()
    create = Mock(return_value=flask_app)
    monkeypatch.setattr(db, "ping", ping)
    monkeypatch.setattr(app_module, "create_app", create)

    assert app_module.launch() is flask_app

    ping.assert_called_once_with()
    create.assert_called_once_with()


@pytest.mark.parametrize(
    "error",
    [
        db.DatabaseUnavailableError("database offline"),
        RuntimeError("missing configuration"),
    ],
)
def test_main_exits_with_message_when_launch_fails(monkeypatch, capsys, error):
    monkeypatch.setattr(app_module, "launch", Mock(side_effect=error))

    with pytest.raises(SystemExit) as exit_info:
        app_module.main()

    assert exit_info.value.code == 1
    assert "Cannot start the personality quiz:" in capsys.readouterr().err


def test_main_runs_app_on_local_interface(monkeypatch):
    flask_app = Mock()
    monkeypatch.setattr(app_module, "launch", Mock(return_value=flask_app))

    app_module.main()

    flask_app.run.assert_called_once_with(host="127.0.0.1", port=5000)
