# Local development setup

How to run this project on your laptop: Python environment, tests, MySQL, and the web app.


## Prerequisites

- **Python 3.12 or newer**
- **MySQL Server and the `mysql` command-line client**

Confirm with `python3 --version` and `mysql --version`.


## 1. Create a virtual environment

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
```


## 2. Install libraries

```bash
pip install -r requirements.txt
pip install -e .
```

Confirm the package is importable:

```bash
python -c "import personality_quiz; print('Package import successful')"
```


## 3. Run tests

With the virtual environment active:

```bash
pytest
```

The test configuration reports coverage and requires at least 90%.


## 4. Configure `.env`

Copy the example file:

```bash
cp config/example.env .env
```

Set `DB_PASSWORD=quiz_password` to match the local MySQL account created in the next step. The remaining database settings are documented in `config/example.env`. Keep `.env` out of git; it is listed in `.gitignore`.


## 5. Install and start MySQL

Install MySQL Server and its command-line client if they are not already installed. On macOS with Homebrew:

```bash
brew install mysql
brew services start mysql
```

MySQL uses port **3306** by default. Start it using the service controls for your installation if you are not using Homebrew.

Create the local database and application account using a MySQL administrator:

```bash
mysql -u root -p < scripts/setup_db.sql
```

The script creates the `personality_quiz` database and the `quiz_app` account with the local development password `quiz_password`.

Confirm 
```bash
PYTHONPATH=src python -c "from personality_quiz.db import ping; ping(); print('MySQL connection successful')"
```


## 6. Create the quiz tables and load sample data

With the virtual environment active, MySQL running, and `.env` configured:

```bash
PYTHONPATH=src python scripts/create_tables.py
PYTHONPATH=src python scripts/seed.py
```

The seed script loads sample quiz content and results from `data/sample-data.sql`.


## 7. Launch the web app

With MySQL running and the tables created:

```bash
PYTHONPATH=src python -m personality_quiz.app
```

Open [http://127.0.0.1:5000/](http://127.0.0.1:5000/).
