#!/bin/bash
#Paste the contents of this file into the user data field
#under 'Advanced Details' while launching an EC2 instance.

#install git
sudo yum install -y git python3.12

#clone and cd into the repo
git clone https://github.com/cs390f26/personality-quiz-monolith.git
cd /home/ec2-user/personality-quiz-monolith

#create a virtual environment, upgrade + install the necesary packages
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt 
pip install -e .

#configure the .env
cp config/example.env .env

#add database configuration


systemctl daemon-reload
systemctl enable --now personality_quiz.service