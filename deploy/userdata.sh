#!/bin/bash
#Paste the contents of this file into the user data field
#under 'Advanced Details' while launching an EC2 instance.

# Exit on error, undefined variable, or failure in a pipeline.
set -euo pipefail

# User data runs as root. This fixed credential is only for a disposable test
# instance; replace it with a private password before any persistent deployment.
APP_DIR=/home/ec2-user/personality-quiz-monolith

# Install Git, Python, and the local MySQL-compatible database server.
yum install -y git python3.12 mariadb105-server
systemctl enable --now mariadb

# Wait up to one minute for MariaDB to accept local connections.
for attempt in {1..30}; do
    if mysqladmin --protocol=socket ping --silent; then
        break
    fi
    sleep 2
done
mysqladmin --protocol=socket ping --silent

#clone and cd into the repo
runuser -u ec2-user -- git clone \
    https://github.com/cs390f26/personality-quiz-monolith.git \
    "$APP_DIR"

#create a virtual environment, upgrade + install the necesary packages
runuser -u ec2-user -- bash -e -c '
    cd /home/ec2-user/personality-quiz-monolith
    python3.12 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
    .venv/bin/pip install -e .
'

#configure the MySQL database environment variables
cat > "$APP_DIR/.env" <<'EOF'
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=personality_quiz
DB_USER=quiz_app
DB_PASSWORD=quiz_password
EOF
chown ec2-user:ec2-user "$APP_DIR/.env"
chmod 600 "$APP_DIR/.env"

# Create the database and app account from the repository's SQL setup.
mysql --protocol=socket --user=root < "$APP_DIR/scripts/setup_db.sql"

# Create the tables and populate them with sample quiz data.
runuser -u ec2-user -- bash -e -c '
    cd /home/ec2-user/personality-quiz-monolith
    .venv/bin/python scripts/create_tables.py
    .venv/bin/python scripts/seed.py
'

# Install and enable the systemd service for the application.
install -o root -g root -m 0644 \
    "$APP_DIR/deploy/personality_quiz.service" \
    /etc/systemd/system/personality_quiz.service
systemctl daemon-reload
systemctl enable --now personality_quiz.service