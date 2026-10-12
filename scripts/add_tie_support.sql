-- Add tied-result storage to an existing quiz database without deleting data.
-- Fresh databases already receive this table from create_tables.py.
CREATE TABLE IF NOT EXISTS quiz_result_ties (
    results_ID INT NOT NULL,
    personality_ID TINYINT NOT NULL,
    PRIMARY KEY (results_ID, personality_ID),
    CONSTRAINT fk_ties_result
        FOREIGN KEY (results_ID)
        REFERENCES quiz_results(results_ID) ON DELETE CASCADE,
    CONSTRAINT fk_ties_personality
        FOREIGN KEY (personality_ID)
        REFERENCES personality_types(personality_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Preserve only additional winners from the legacy link table, if it exists.
SET @legacy_links_exist = (
    SELECT COUNT(*)
    FROM information_schema.tables
    WHERE table_schema = DATABASE()
      AND table_name = 'quiz_result_personalities'
);

SET @migrate_legacy_ties_sql = IF(
    @legacy_links_exist > 0,
    'INSERT IGNORE INTO quiz_result_ties (results_ID, personality_ID) SELECT legacy.results_ID, legacy.personality_ID FROM quiz_result_personalities AS legacy JOIN quiz_results AS saved ON saved.results_ID = legacy.results_ID WHERE legacy.personality_ID <> saved.personality_ID',
    'SELECT 1'
);

PREPARE migrate_legacy_ties_stmt FROM @migrate_legacy_ties_sql;
EXECUTE migrate_legacy_ties_stmt;
DEALLOCATE PREPARE migrate_legacy_ties_stmt;
