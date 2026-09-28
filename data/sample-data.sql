-- -----------------------------------------------------
-- personality_types
-- -----------------------------------------------------

INSERT INTO personality_types
    (personality_ID, personality_type, description)
VALUES
    (1, 'Orange', 'Energetic, spontaneous, and action-oriented'),
    (2, 'Gold', 'Organized, dependable, and structured'),
    (3, 'Green', 'Analytical, curious, and independent'),
    (4, 'Blue', 'Compassionate, cooperative, and relationship-focused');


-- -----------------------------------------------------
-- questions
-- -----------------------------------------------------

INSERT INTO questions
    (question_ID, question_text)
VALUES
    (1, 'Which activity sounds most appealing?'),
    (2, 'How do you usually approach a new problem?'),
    (3, 'What do you value most when working in a group?'),
    (4, 'Which environment do you prefer?'),
    (5, 'What best describes how you make decisions?');


-- -----------------------------------------------------
-- answers
-- -----------------------------------------------------

INSERT INTO answers
    (answer_ID, question_ID, answer_text, personality_ID)
VALUES
    (1, 1, 'Trying something exciting and spontaneous', 1),
    (2, 1, 'Planning and completing an organized project', 2),
    (3, 1, 'Learning how something complex works', 3),
    (4, 1, 'Spending meaningful time with other people', 4),

    (5, 2, 'Jump in and adjust as I go', 1),
    (6, 2, 'Make a clear step-by-step plan', 2),
    (7, 2, 'Analyze the problem before acting', 3),
    (8, 2, 'Talk it through with others', 4),

    (9, 3, 'Energy and flexibility', 1),
    (10, 3, 'Organization and responsibility', 2),
    (11, 3, 'Logic and strong ideas', 3),
    (12, 3, 'Cooperation and understanding', 4),

    (13, 4, 'A fast-paced environment with variety', 1),
    (14, 4, 'A predictable environment with clear expectations', 2),
    (15, 4, 'A quiet environment where I can focus', 3),
    (16, 4, 'A friendly environment with lots of interaction', 4),

    (17, 5, 'I decide quickly and trust my instincts', 1),
    (18, 5, 'I follow rules and proven methods', 2),
    (19, 5, 'I compare facts and possibilities', 3),
    (20, 5, 'I consider how the decision affects people', 4);


-- -----------------------------------------------------
-- quiz_results
-- -----------------------------------------------------

INSERT INTO quiz_results
    (results_ID, personality_ID, person_name, completed_date)
VALUES
    (1, 3, 'Jenny', '2026-09-14'),
    (2, 2, 'Nora', '2026-09-15'),
    (3, 4, 'Ronnie', '2026-09-16'),
    (4, 1, 'Coleman', '2026-09-17'),
    (5, 3, 'Jeff', '2026-09-18');
