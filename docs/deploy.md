# Deploy on EC2

This document explains how to run the monolithic personality quiz app on an EC2 instance.

## One-Time Setup

The repository URL in `deploy/userdata.sh` is set to `https://github.com/cs390f26/personality-quiz-monolith.git`. If you deploy from a fork, change the URL to your repository and push the change before deploying.

## Deploy Process

The deployment steps are:

* Install Git and Python 3.12
* Clone the repository
* Set up the `.venv` and install the Python packages
* Configure `.env` with the MySQL connection settings
* Start MySQL, create the tables, and load the sample data
* Install and launch the `personality_quiz` systemd service

The `deploy/userdata.sh` script is intended to perform the initial setup. The service file also needs its `Type` and Gunicorn application target corrected before it can run.

In the EC2 launch dialog:

* Select an Amazon Linux instance with Python 3.12 available.
* Enable HTTP and SSH in the security group. Restrict SSH to trusted addresses.
* Paste the completed `deploy/userdata.sh` into **Advanced details → User data**.

## Debugging

Cloud-init writes user-data output to `/var/log/cloud-init-output.log`. SSH to the instance and inspect this file if setup fails:

```bash
sudo tail -n 200 /var/log/cloud-init-output.log
```

## Other Useful Commands on the EC2 Instance

* `sudo systemctl status personality_quiz` — see the app service status
* `sudo systemctl status mysql` — see the MySQL service status
* `curl -i http://localhost/health` — check the app and its MySQL connection
* `sudo systemctl restart personality_quiz` — restart the app service
* `sudo journalctl -u personality_quiz -f` — follow the app logs
* `sudo journalctl -u mysql -f` — follow the MySQL logs
