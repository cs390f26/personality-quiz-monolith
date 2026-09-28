CREATE DATABASE IF NOT EXISTS personality_quiz;

CREATE USER IF NOT EXISTS 'quiz_app'@'localhost'
IDENTIFIED BY 'quiz_password';

GRANT ALL PRIVILEGES
ON personality_quiz.*
TO 'quiz_app'@'localhost';

FLUSH PRIVILEGES;