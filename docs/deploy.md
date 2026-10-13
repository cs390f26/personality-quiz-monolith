# Deploy on EC2

This document explains how to run the monolithic personality quiz app on an EC2 instance.

## One-Time Setup

The repository URL in `deploy/userdata.sh` is set to `https://github.com/cs390f26/personality-quiz-monolith.git`. If you deploy from a fork, change the URL to your repository and push the change before deploying.

## Deploy Process

The `deploy/userdata.sh` file is a script that performs initial setup. The steps it executes are as follows:

* Install Git and Python 3.12
* Clone the repository
* Set up the `.venv` and install the Python packages
* Configure `.env` with the MySQL connection settings
* Start MySQL, create the tables, and load the sample data
* Install and launch the `personality_quiz` systemd service

As you launch the EC2 instance:

* Title it `Personality Quiz App` (optional), leave the default Amazon Linux kernel and t3.micro Instance type selected.
* Under key pair, select `vockey`
* Enable HTTP and SSH in the security group.
* Paste the completed `deploy/userdata.sh` into **Advanced details → User data**.

## Other Useful Commands on the EC2 Instance

* `sudo systemctl status personality_quiz` — see the app service status
* `sudo systemctl status mysql` — see the MySQL service status
* `curl -i http://localhost/health` — check the app and its MySQL connection
* `sudo systemctl restart personality_quiz` — restart the app service
* `sudo journalctl -u personality_quiz -f` — follow the app logs
* `sudo journalctl -u mysql -f` — follow the MySQL logs
