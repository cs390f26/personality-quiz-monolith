"""Flask routes for the personality quiz API and existing page templates."""

import sys
from collections import Counter

import mysql.connector
from flask import Flask, jsonify, render_template, request

from personality_quiz import db


class ValidationError(ValueError):
    """The submitted quiz does not satisfy the API contract."""


def _error(code, message, status):
    return jsonify({"error": {"code": code, "message": message}}), status


def _score_submission(body):
    """Validate the whole submission before saving anything; return its winners."""
    if not isinstance(body, dict):
        raise ValidationError("JSON body required")

    name = body.get("personName")
    if not isinstance(name, str) or not name.strip():
        raise ValidationError("personName is required")
    if len(name) > 100:
        raise ValidationError("personName must be at most 100 characters")

    selections = body.get("selectedAnswers")
    if not isinstance(selections, list) or not selections:
        raise ValidationError("selectedAnswers must be a non-empty list")

    selected_ids = {}
    for selection in selections:
        if not isinstance(selection, dict):
            raise ValidationError("Each selection must contain questionId and answerId")
        question_id = selection.get("questionId")
        answer_id = selection.get("answerId")
        # bool is a subclass of int in Python, but is not a valid JSON ID.
        if type(question_id) is not int or question_id < 1:
            raise ValidationError("questionId must be a positive integer")
        if type(answer_id) is not int or answer_id < 1:
            raise ValidationError("answerId must be a positive integer")
        if question_id in selected_ids:
            raise ValidationError("Only one answer may be submitted for each question")
        selected_ids[question_id] = answer_id

    question_ids = {question["question_ID"] for question in db.get_questions()}
    if not question_ids or set(selected_ids) != question_ids:
        raise ValidationError("One answer must be submitted for every quiz question")

    scores = Counter()
    for question_id, answer_id in selected_ids.items():
        answers = {answer["answer_ID"]: answer for answer in db.get_answers(question_id)}
        if answer_id not in answers:
            raise ValidationError(
                "The selected answer is not valid for the specified question"
            )
        scores[answers[answer_id]["personality_ID"]] += 1

    highest = max(scores.values())
    winners = sorted(
        personality_id for personality_id, score in scores.items() if score == highest
    )
    return name, winners


def _result_json(result):
    personalities = [
        {
            "personalityId": personality["personality_ID"],
            "personalityType": personality["personality_type"],
            "description": personality["description"],
        }
        for personality in result["personalities"]
    ]
    body = {
        "resultId": result["results_ID"],
        "personName": result["person_name"],
        "completedDate": result["completed_date"].isoformat(),
    }
    if len(personalities) == 1:
        body["personality"] = personalities[0]
    else:
        body["isTie"] = True
        body["personalities"] = personalities
    return body


def create_app() -> Flask:
    """Create an app without opening a database connection at import time."""
    app = Flask(__name__)

    @app.errorhandler(db.DatabaseUnavailableError)
    @app.errorhandler(mysql.connector.Error)
    def database_unavailable(error):
        app.logger.warning("Database request failed: %s", error)
        return jsonify({"status": "unavailable"}), 503

    @app.get("/")
    def index_page():
        return render_template("index.html")

    @app.get("/quiz")
    def quiz_page():
        return render_template("quiz.html")

    @app.get("/results")
    def results_page():
        return render_template("results.html")

    @app.get("/statistics-page")
    def statistics_page():
        return render_template("statistics.html")

    @app.get("/health")
    def health():
        db.ping()
        return jsonify({"status": "ok"})

    @app.get("/questions")
    def list_questions():
        questions = [
            {
                "questionId": question["question_ID"],
                "questionText": question["question_text"],
                "answers": [
                    {
                        "answerId": answer["answer_ID"],
                        "answerText": answer["answer_text"],
                    }
                    for answer in db.get_answers(question["question_ID"])
                ],
            }
            for question in db.get_questions()
        ]
        return jsonify({"questions": questions})

    @app.post("/quiz-results")
    def submit_quiz():
        body = request.get_json(silent=True)
        try:
            name, winners = _score_submission(body)
        except ValidationError as error:
            return _error("BAD_REQUEST", str(error), 400)

        selected_answers = [
            (selection["questionId"], selection["answerId"])
            for selection in body["selectedAnswers"]
        ]
        result_id = db.save_result(
            name,
            winners[0],
            tied_personality_ids=winners[1:],
            selected_answers=selected_answers,
        )
        return jsonify(_result_json(db.get_result(result_id))), 201

    @app.get("/quiz-results")
    def list_quiz_results():
        results_by_id = {}
        for row in db.get_result_history():
            result_id = row["results_ID"]
            if result_id not in results_by_id:
                results_by_id[result_id] = {
                    "resultId": result_id,
                    "personName": row["person_name"],
                    "completedDate": row["completed_date"].isoformat(),
                    "personalities": [],
                }
            results_by_id[result_id]["personalities"].append(row["personality_type"])
        return jsonify({"results": list(results_by_id.values())})

    @app.get("/quiz-results/<int:result_id>/answers")
    def get_quiz_result_answers(result_id):
        answers = db.get_result_answers(result_id)
        if answers is None:
            return _error("NOT_FOUND", "Requested resource not found", 404)
        return jsonify(
            {
                "resultId": result_id,
                "answers": [
                    {
                        "questionId": answer["question_ID"],
                        "questionText": answer["question_text"],
                        "answerId": answer["answer_ID"],
                        "answerText": answer["answer_text"],
                    }
                    for answer in answers
                ],
            }
        )

    @app.get("/quiz-results/<int:result_id>")
    def get_quiz_result(result_id):
        result = db.get_result(result_id)
        if result is None:
            return _error("NOT_FOUND", "Requested resource not found", 404)
        return jsonify(_result_json(result))

    @app.get("/statistics")
    def statistics():
        rows = db.get_statistics()
        total = rows[0]["total_completed"] if rows else 0
        return jsonify(
            {
                "totalCompleted": total,
                "personalityTypes": [
                    {
                        "personalityId": row["personality_ID"],
                        "personalityType": row["personality_type"],
                        "count": row["result_count"],
                        "percentage": (
                            round(row["result_count"] / total * 100, 2)
                            if total
                            else 0.0
                        ),
                    }
                    for row in rows
                ],
            }
        )

    return app


def launch() -> Flask:
    """Check configured MySQL connectivity before launching the web server."""
    db.ping()
    return create_app()


def main():
    try:
        app = launch()
    except (db.DatabaseUnavailableError, RuntimeError) as error:
        print(f"Cannot start the personality quiz: {error}", file=sys.stderr)
        sys.exit(1)
    app.run(host="127.0.0.1", port=5000)


if __name__ == "__main__":
    main()
