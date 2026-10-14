# Deploy on EC2

This document explains how to run the monolithic personality quiz app on an EC2 instance.

## One-Time Setup

The repository URL in `deploy/userdata.sh` is set to `https://github.com/cs390f26/personality-quiz-monolith.git`. If you deploy from a fork, change the URL to your repository and push the change before deploying.

## Deploy Process

The `deploy/userdata.sh` file is a script that performs initial setup. The steps it executes are as follows:

* Install Git, Python 3.12, and the local MariaDB (MySQL-compatible) server
* Clone the repository
* Set up the `.venv` and install the Python packages
* Start MariaDB and wait for it to accept connections
* Create the database and account, then write `.env`
* Create the tables and load the sample data
* Install and launch the `personality_quiz` systemd service

As you launch the EC2 instance:

* Title it `Personality Quiz App` (optional), leave the default Amazon Linux kernel and t3.micro Instance type selected.
* Under key pair, select `vockey`
* Enable HTTP and SSH in the security group.
The `deploy/userdata.sh` script performs this setup on an Amazon Linux 2023 instance. It uses the example `quiz_password` credential from `scripts/setup_db.sql`; this is only appropriate for a disposable test instance with no sensitive data. For a persistent deployment, replace it with a private password in both `scripts/setup_db.sql` and `deploy/userdata.sh` before launch. The app's `.env` file is readable only by `ec2-user`. MySQL-compatible database traffic stays local; do not open port 3306 in the instance's security group.

In the EC2 launch dialog:

* Select an Amazon Linux 2023 instance.
* Enable HTTP and SSH in the security group. Restrict SSH to trusted addresses.
* Paste the completed `deploy/userdata.sh` into **Advanced details → User data**.

## Other Useful Commands on the EC2 Instance

* `sudo systemctl status personality_quiz` — see the app service status
* `sudo systemctl status mariadb` — see the local database service status
* `curl -i http://localhost/health` — check the app and its MySQL connection
* `sudo systemctl restart personality_quiz` — restart the app service
* `sudo journalctl -u personality_quiz -f` — follow the app logs
* `sudo journalctl -u mariadb -f` — follow the database logs
