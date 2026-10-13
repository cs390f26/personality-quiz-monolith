# Design

This document describes the design of the Flask server and how data moves through its layers. The web API and database are *delivery mechanisms* for the core application, and there is one layer for each:

1. **API** — handles HTTP: parse requests, call the application, and return responses.
2. **Application** — handles quiz workflows: load questions, validate and score answers, and prepare results and statistics.
3. **DB** — interacts with MySQL: turn application requests into SQL operations and turn query results into data the application can use.

The API and application logic are implemented in `src/personality_quiz/app.py`; database operations are implemented in `src/personality_quiz/db.py`.

## Data representations

The data for this application is a collection of quiz content and completed attempts. This section describes how this data is stored in the database and the forms used to pass data around within the Flask server.

The database layer retrieves rows from the tables involved in a request. The application layer validates or combines that information as needed. The API layer translates it into an HTTP response.

### Database Representation

Quiz content is stored across the `questions`, `answers`, and `personality_types` tables. A completed attempt is stored in `quiz_results`; additional winning personalities for a tie are stored in `quiz_result_ties`, and the participant's selected answers are stored in `quiz_result_answers`.

For example, a completed attempt for the Green personality might be represented by these rows:

```text
quiz_results
results_ID | personality_ID | person_name | completed_date
6          | 3              | Alex        | 2026-10-13

quiz_result_answers
results_ID | question_ID | answer_ID
6          | 1           | 3
6          | 2           | 7
6          | 3           | 11
6          | 4           | 15
6          | 5           | 19
```

The `personality_ID` value `3` identifies Green. If multiple personalities tie, the additional winners are stored with the same `results_ID` in `quiz_result_ties`.

### Raw Query Result

The database layer returns query results as Python dictionaries whose keys match the MySQL column names. For example, `get_result` combines a completed attempt with its winning personalities:

```python
{
    "results_ID": 6,
    "personality_ID": 3,
    "person_name": "Alex",
    "completed_date": date(2026, 10, 13),
    "personalities": [
        {
            "personality_ID": 3,
            "personality_type": "Green",
            "description": "Analytical, curious, and independent",
        },
    ],
}
```

### Quiz Result

When a participant completes the quiz, the API returns their name, the result ID, completion date, and personality. The response uses camelCase field names:

```json
{
  "resultId": 6,
  "personName": "Alex",
  "completedDate": "2026-10-13",
  "personality": {
    "personalityId": 3,
    "personalityType": "Green",
    "description": "Analytical, curious, and independent"
  }
}
```

If multiple personalities tie, the response contains `isTie: true` and a `personalities` list instead of a single `personality`.

### Quiz Statistics

When a user views statistics, they see the total number of completed attempts and the count and percentage for each personality type. The API returns this information in the following shape:

```json
{
  "totalCompleted": 5,
  "personalityTypes": [
    {
      "personalityId": 1,
      "personalityType": "Orange",
      "count": 1,
      "percentage": 20.0
    },
    {
      "personalityId": 2,
      "personalityType": "Gold",
      "count": 1,
      "percentage": 20.0
    },
    {
      "personalityId": 3,
      "personalityType": "Green",
      "count": 2,
      "percentage": 40.0
    },
    {
      "personalityId": 4,
      "personalityType": "Blue",
      "count": 1,
      "percentage": 20.0
    }
  ]
}
```

Each tied attempt is counted once in `totalCompleted` and toward every winning personality's count, so personality percentages can add up to more than 100%.