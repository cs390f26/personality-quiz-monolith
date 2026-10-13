# Local development setup

How to set up this project on your laptop: Python environment, tests, lint, MySQL, and the web app.

## Prerequisites

- **Python 3.12 or newer**
- **MySQL Server and the `mysql` command-line client**
- **Homebrew**, if using the macOS installation commands below

Confirm Python with `python3 --version`. Confirm the MySQL client with `mysql --version`.

## 1. Create and activate a virtual environment

In the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2. Install necessary libraries

Run the following while the virtual environment is active:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

Confirm the package is importable by recieving the output of the print statement when this command is run:

```bash
python -c "import personality_quiz; print('Package import successful')"
```

## 3. Run tests

With the virtual environment still active, run:

```bash
python -m pytest tests
```

This command executes all test functions and files in the `tests` directory and generates a coverage percentage report in the terminal. The goal is 90% coverage.


## 4. Configure `.env`

Copy the example file:

```bash
cp config/example.env .env
```

Alter the `DB_PASSWORD` field of the `.env` to `quiz_password` for the local database created by `scripts/setup_db.sql`. This is a local development example password; we will use a separate password for deployment.  The file should now resemble the following:

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

Python code loads `.env` through `settings.py`. The `mysql` client does **not** read this file: the commands below explicitly use the example host, port, user, and database. Adjust those arguments if you choose different settings. The `-p` option prompts for a password.

## 5. Install MySQL

If MySQL Server and its client are already installed, skip this step.

On macOS with Homebrew:

```bash
brew install mysql
```

See the [Homebrew MySQL formula](https://formulae.brew.sh/formula/mysql) for further installation and service details. On other operating systems, install MySQL Server and its command-line client using the appropriate installer or package manager before continuing.

## 6. Start MySQL and create the database

Run the following two commands. The second should show the mysql status as `started`:

```bash
brew services start mysql
brew services list
```

MySQL runs as a background service on port **3306**. If you installed it another way, use that installation's service controls.

Create the database and application account using a **MySQL administrator**. When prompted for a password, enter your MySQL administration password instead of the application password. For a fresh local installation with no root password, press Enter at the prompt. Use the administrator account configured for your installation if it is not `root`:

```bash
mysql -u root -p < scripts/setup_db.sql
```

The `setup_db.sql` script creates the `personality_quiz` database and `quiz_app` for `localhost` if absent, and grants that account privileges on `personality_quiz.*`.

Check that the application account can connect over TCP. This time, when prompted, enter the application password:

```bash
mysql -h 127.0.0.1 -P 3306 -u quiz_app -p personality_quiz -e "SELECT 1;"
```

Verify the Python connection using `.env`:

```bash
PYTHONPATH=src python -c "from personality_quiz.db import ping; ping(); print('MySQL connection successful')"
```

MySQL stores data on disk in its own data directory. Stopping it does not erase your tables or results. For this Homebrew installation, stop it with `brew services stop mysql`; start it again with `brew services start mysql`.

## 7. Create the quiz tables

With the virtual environment active, MySQL running, and `.env` configured, execute this command to create the tables that make up our database schema:

```bash
PYTHONPATH=src python scripts/create_tables.py
```
It should confirm success with `MySQL tables are ready.`

This uses the application account and creates any missing quiz tables: `questions`, `personality_types`, `answers`, `quiz_results`, `quiz_result_ties`, and `quiz_result_answers`. Foreign keys connect answers to questions and personality types, results to personality types, and each saved answer to its result attempt. Each completed attempt has one row in `quiz_results`; additional winning categories for a tie and the selected question answers are stored in related tables and saved in the same transaction. Existing tables and results are left in place.

The script is safe to rerun and can fill in tables missing from a partially initialized database, including `quiz_result_answers` for answer breakdowns. It does not alter the columns of existing tables. If the legacy `quiz_result_personalities` table exists, it also copies additional winners into `quiz_result_ties` without deleting existing data; single-category results keep their original format. Tied API results return `personalities` and `isTie: true`. Statistics credit each winning category and count the attempt once in `totalCompleted`, so category percentages can sum above 100% when ties exist.

### Initialize or repair quiz content

For a fresh or partially initialized database, create the tables and load the sample rows:

```bash
PYTHONPATH=src python scripts/create_tables.py
PYTHONPATH=src python scripts/seed.py
```

This keeps existing quiz results and migrates any legacy result-personality links during table setup; no separate legacy upgrade script is needed.

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
PYTHONPATH=src python scripts/seed.py
```

The script reads the database settings from `.env` (or the environment) and loads `data/sample-data.sql`, which inserts four personality types, five questions, twenty answer choices, and five example completed results. Quiz questions, answers, and personality types are required for a usable quiz. Example completed results are optional in principle, but this file inserts them together with the quiz content. Before loading, the script checks that the `personality_types`, `questions`, `answers`, and `quiz_results` tables exist. If a table is missing, it reports the missing tables and directs you to run `PYTHONPATH=src python scripts/create_tables.py`.

This import can be rerun safely. It uses `INSERT IGNORE` with fixed IDs, which inserts missing sample rows and leaves existing rows unchanged. Changes are committed after all SQL statements execute; if loading fails, the transaction is rolled back and the script exits with an error.

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

The API serves `/questions`, `POST /quiz-results`, `GET /quiz-results`, `/quiz-results/{resultId}`, `/statistics`, and `/health`. The `/quiz` page loads questions from `/questions`, submits completed attempts to `/quiz-results`, and the `/results` page loads the saved result. The home page displays completed-attempt totals, and the statistics page loads category counts and percentages plus links to previous attempts. Category percentages can sum above 100% when attempts have tied results, since each winning category receives credit. The API validates against all questions stored in the database; the development seed contains five of the planned ten questions. A `503` from `/questions` means the app cannot reach the configured MySQL database; check the database service and the `.env` settings in the setup steps above.

## 10. Run acceptance tests (pending implementation)
