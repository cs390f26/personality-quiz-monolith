from datetime import date
from unittest.mock import Mock

from personality_quiz import db
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
