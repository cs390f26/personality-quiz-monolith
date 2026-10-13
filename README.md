# Personality Quiz

This is the monolithic implementation of the Personality Quiz application. It provides a Flask web interface and HTTP API backed by MySQL.

The quiz lets a participant answer questions, see their personality result (including ties), and view saved attempts and aggregate statistics.

## Documentation

| Guide | Contents |
| --- | --- |
| [Development setup](docs/development.md) | Python environment, MySQL setup, test commands, sample data, and running the app |
| [Deploy on EC2](docs/deploy.md) | Deployment guide |

## Quick start

Prerequisites: Python 3.12 or newer and a running MySQL server.

* Create a virtual environment and install dependencies
* Configure .env from config/example.env
* Start MySQL Local and create the quiz tables
* Run python -m personality_quiz.app and open http://127.0.0.1:5000/

See development.md for further details.
