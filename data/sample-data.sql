-- -----------------------------------------------------
-- personality_types
-- -----------------------------------------------------

INSERT INTO personality_types
    (personality_ID, personality_type, description)
VALUES
    (1, 'Orange', 'Orange personalities are action-oriented and spontaneous, driven by a strong need for freedom, variety, excitement, and momentum. They thrive in fast-paced environments, enjoy taking initiative, and are often happiest when they can adapt quickly, explore new opportunities, and make things happen without being restricted by rigid plans or routine.'),
    (2, 'Gold', 'Gold personalities are organized, dependable, and deeply value structure, stability, and clear expectations. They are dutiful, punctual, and goal-oriented, often preferring plans, routines, and traditional systems that help them follow through consistently. In both work and life, they tend to prepare ahead, respect authority, and prioritize responsibility over spontaneity. While this makes them reliable and effective in roles like project management, operations, accounting, administration, and law, they can become rigid or overly controlling when faced with sudden change or uncertainty.'),
    (3, 'Green', 'Green personalities are analytical, logical, and driven by a deep need for competence, independence, and intellectual freedom. They are curious, innovative, and often perfectionistic, seeking to understand the underlying systems behind complex problems and question assumptions before accepting them. These individuals value the ability to think deeply and solve challenges on their own, which makes them especially effective in engineering, technology, scientific research, medicine, and data analysis. However, under stress they may become detached, overly critical, or so focused on analysis that they struggle to act decisively.'),
    (4, 'Blue', 'Blue personalities are relationship-oriented, empathetic, and deeply motivated by meaningful connections, harmony, and authentic human interaction. They are warm, compassionate, creative, and cooperative, often reading the room instinctively and caring deeply about how decisions affect the people around them. They thrive in environments where they can support others, build trust, and contribute to a shared purpose, making them well suited for teaching, counseling, human resources, nursing, and mission-driven nonprofit work. Under stress, however, they can become conflict-avoidant, overly sensitive, or take criticism too personally when they feel disconnected from others.')
ON DUPLICATE KEY UPDATE description = VALUES(description);


-- -----------------------------------------------------
-- questions
-- -----------------------------------------------------

INSERT IGNORE INTO questions
    (question_ID, question_text)
VALUES
    (1, 'Which activity sounds most appealing?'),
    (2, 'How do you usually approach a new problem?'),
    (3, 'What do you value most when working in a group?'),
    (4, 'Which environment do you prefer?'),
    (5, 'What best describes how you make decisions?'),
    (6, 'I am more…'),
    (7, 'In the workplace I am…'),
    (8, 'I am…'),
    (9, 'I tend to…'),
    (10, 'Others are drawn to me because I am…');


-- -----------------------------------------------------
-- answers
-- -----------------------------------------------------

INSERT IGNORE INTO answers
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
    (20, 5, 'I consider how the decision affects people', 4),

    (21, 6, 'Mostly Organized', 2),
    (22, 6, 'Mostly Flexible', 1),
    (23, 6, 'Flexible', 1),
    (24, 6, 'Organized', 2),

    (25, 7, 'Hardworking and organized', 2),
    (26, 7, 'Friendly and flexible', 1),
    (27, 7, 'Kind and quiet', 4),
    (28, 7, 'Creative and full of ideas', 3),

    (29, 8, 'Mostly Realistic', 2),
    (30, 8, 'Mostly Optimistic', 1),
    (31, 8, 'Optimistic', 1),
    (32, 8, 'Realistic', 2),

    (33, 9, 'Mostly Look for affirmation from others', 4),
    (34, 9, 'Mostly Do whatever I think is best', 3),
    (35, 9, 'Always Do whatever I think is best', 3),
    (36, 9, 'Always Look for affirmation from others', 4),

    (37, 10, 'Dependable', 2),
    (38, 10, 'Fun', 1),
    (39, 10, 'A good listener', 4),
    (40, 10, 'Insightful', 3);


-- -----------------------------------------------------
-- quiz_results
-- -----------------------------------------------------

INSERT IGNORE INTO quiz_results
    (results_ID, personality_ID, person_name, completed_date)
VALUES
    (1, 3, 'Jenny', '2026-09-14'),
    (2, 2, 'Nora', '2026-09-15'),
    (3, 4, 'Ronnie', '2026-09-16'),
    (4, 1, 'Coleman', '2026-09-17'),
    (5, 3, 'Jeff', '2026-09-18');
