# Local development setup

How to set up this project on your laptop: Python environment, tests, lint, MySQL, and the web app.

## Prerequisites

- **Python 3.12 or newer**
- **MySQL Server and the `mysql` command-line client**
- **Homebrew**, if using the macOS installation commands below

Confirm Python with `python3 --version`. After installing MySQL, confirm its client with `mysql --version`.

## 1. Create a virtual environment

From the root of the project:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Use a Python executable that reports version 3.12 or newer. Activate the environment again whenever you open a new terminal to run project commands.

## 2. Install libraries

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

The editable install (`-e .`) makes the `personality_quiz` package importable while you edit source under `src/personality_quiz/`.

Verify the package is importable:

```bash
python -c "import personality_quiz; print('Package import successful')"
```

## 3. Run tests

With the virtual environment active:

```bash
python -m pytest tests
```

The tests in `tests/test_db.py` mock the MySQL connection and cursor. The HTTP tests in `tests/test_api.py` use a fresh in-memory database with the project schema and sample data, plus five test questions to exercise a ten-question quiz. Neither suite requires a running MySQL server or changes your local database. These tests cover validation, scoring, saved results, ties, statistics, and database failures; they do not verify MySQL-specific behavior.


## 4. Configure `.env`

For a fresh checkout, copy the example file:

```bash
cp config/example.env .env
```

If `.env` already exists, edit it instead of overwriting your settings. Keep it out of Git; it is listed in `.gitignore`.

For the local database created by `scripts/setup_db.sql`, use:

```dotenv
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=personality_quiz
DB_USER=quiz_app
DB_PASSWORD=quiz_password
```

| Setting | Purpose |
| --- | --- |
| `DB_HOST` | Host running MySQL; `127.0.0.1` is your laptop. |
| `DB_PORT` | MySQL's TCP port; the default is `3306`. |
| `DB_NAME` | Database containing the quiz tables. |
| `DB_USER` | MySQL account used by the application and table-creation script. |
| `DB_PASSWORD` | Password for that MySQL account. |

All five values are required. The example file uses `CHANGE_ME`, but the bootstrap SQL creates the local account with `quiz_password`. Replace `CHANGE_ME` to match that account. This is a local development example password; use a separate password for deployment. If the account already exists, the bootstrap's `CREATE USER IF NOT EXISTS` does not change its password.

Python code loads `.env` through `settings.py`. The `mysql` client does **not** read this file: the commands below explicitly use the example host, port, user, and database. Adjust those arguments if you choose different settings. The `-p` option prompts for a password.

## 5. Install MySQL

If MySQL Server and its client are already installed, skip installation. On macOS with Homebrew:

```bash
brew install mysql
```

See the [Homebrew MySQL formula](https://formulae.brew.sh/formula/mysql) for installation and service details. On other operating systems, install MySQL Server and its command-line client using the appropriate installer or package manager before continuing.

## 6. Start MySQL and create the database

For the Homebrew installation above:

```bash
brew services start mysql
brew services list
```

MySQL runs as a background service on port **3306**. If you installed it another way, use that installation's service controls.

Create the database and application account using a **MySQL administrator**:

```bash
mysql -u root -p < scripts/setup_db.sql
```

Enter your MySQL administrator password, not the application password. For a fresh local installation with no root password, press Enter at the prompt. Use the administrator account configured for your installation if it is not `root`.

The script creates the `personality_quiz` database, creates `quiz_app` for `localhost` if absent, and grants that account privileges on `personality_quiz.*`.

Check that the application account can connect over TCP:

```bash
mysql -h 127.0.0.1 -P 3306 -u quiz_app -p personality_quiz -e "SELECT 1;"
```

Enter the application password from step 5. Then check the Python connection using `.env`:

```bash
python -c "from personality_quiz.db import ping; ping(); print('MySQL connection successful')"
```

This checks connectivity, not whether the tables or quiz content exist.

MySQL stores data on disk in its own data directory. Stopping it does not erase your tables or results. For this Homebrew installation, stop it with `brew services stop mysql`; start it again with `brew services start mysql`.

## 7. Create the quiz tables

With the virtual environment active, MySQL running, and `.env` configured:

```bash
PYTHONPATH=src python scripts/create_tables.py
```

This uses the application account and creates any missing quiz tables: `questions`, `personality_types`, `answers`, `quiz_results`, and `quiz_result_ties`. Foreign keys connect answers to questions and personality types, and results to personality types. Each completed attempt has one row in `quiz_results`; additional winning categories for a tie are stored in `quiz_result_ties` and saved in the same transaction. Existing tables and results are left in place.

The script is safe to rerun and can fill in tables missing from a partially initialized database. It does not alter the columns of existing tables.

### Add tie support to an existing database

If you already created the original four tables, add the new table without deleting questions or saved results:

```bash
mysql -h 127.0.0.1 -P 3306 -u quiz_app -p personality_quiz < scripts/add_tie_support.sql
```

This migration can be run again safely. Fresh databases created with the updated table script already include it. If the legacy `quiz_result_personalities` table exists, the script copies only additional winners into the new table. Single-category results keep their original format; tied API results return `personalities` and `isTie: true`. Statistics credit each winning category and count the attempt once in `totalCompleted`, so category percentages can sum above 100% when ties exist.

### Initialize or repair quiz content

For a fresh or partially initialized database, run the same table and seed steps above and below. The seed file uses `INSERT IGNORE`, so existing rows with the same IDs are preserved and missing development questions and answers are added:

```bash
PYTHONPATH=src python scripts/create_tables.py
mysql -h 127.0.0.1 -P 3306 -u quiz_app -p personality_quiz < data/sample-data.sql
```

This keeps existing quiz results and legacy result-personality links; no separate legacy upgrade script is needed.

### Reset the local quiz tables when needed

**This deletes all quiz questions, answer choices, personality types, and saved results in the selected database.** Use it only for a local development database whose data you intend to discard.

From the project root, with the virtual environment active and `.env` configured for the local development database, run:

```bash
PYTHONPATH=src python scripts/delete_tables.py
```

Recreate the tables with `PYTHONPATH=src python scripts/create_tables.py`, then load the sample data in step 8.

## 8. Load quiz content and sample results

With MySQL running and the tables created:

```bash
mysql -h 127.0.0.1 -P 3306 -u quiz_app -p personality_quiz < data/sample-data.sql
```

The file inserts four personality types, five questions, twenty answer choices, and five example completed results. Quiz questions, answers, and personality types are required for a usable quiz. Example completed results are optional in principle, but this file inserts them together with the quiz content.

This import can be rerun safely. It uses `INSERT IGNORE` with fixed IDs, which inserts missing sample rows and leaves existing rows unchanged.

Verify the row counts:

```bash
mysql -h 127.0.0.1 -P 3306 -u quiz_app -p personality_quiz -e "SELECT 'personality_types' AS table_name, COUNT(*) AS row_count FROM personality_types UNION ALL SELECT 'questions', COUNT(*) FROM questions UNION ALL SELECT 'answers', COUNT(*) FROM answers UNION ALL SELECT 'quiz_results', COUNT(*) FROM quiz_results;"
```

Expected counts after a fresh import are **4, 5, 20, and 5**, respectively.

## 9. Launch the web app

With the virtual environment active, MySQL running, the tables created or migrated, and quiz content loaded:

```bash
PYTHONPATH=src python -m personality_quiz.app
```

The entry point checks the configured MySQL connection, then listens on port **5000**. Open [http://127.0.0.1:5000/](http://127.0.0.1:5000/).

The API serves `/questions`, `POST /quiz-results`, `/quiz-results/{resultId}`, `/statistics`, and `/health`. The `/quiz` page loads questions from `/questions`, submits completed attempts to `/quiz-results`, and the `/results` page loads the saved result. The home and statistics pages are still static. The API validates against all questions stored in the database; the development seed contains five of the planned ten questions. A `503` from `/questions` means the app cannot reach the configured MySQL database; check the database service and the `.env` settings in the setup steps above.

## 10. Run acceptance tests (pending implementation)

The repository does not yet contain `tests_ui/` or Playwright dependencies. There is no browser acceptance-test command available today; HTTP API tests run with the command in step 3.

When browser tests are added, document their dependencies, browser installation, app startup, and database setup here. Tests that reset data should use a dedicated test database. The quiz app now has `/health`, but the voting project's fixtures still do not apply to this MySQL application.
