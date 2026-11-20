-- Apply to databases created before course lecturer ownership was added.
ALTER TABLE courses
    ADD COLUMN IF NOT EXISTS lecturer_id INTEGER;

ALTER TABLE courses
    ADD CONSTRAINT courses_lecturer_id_fkey
    FOREIGN KEY (lecturer_id) REFERENCES users(id)
    ON DELETE RESTRICT;

CREATE INDEX IF NOT EXISTS ix_courses_lecturer_id
    ON courses (lecturer_id);

-- Backfill existing courses here before making lecturer_id NOT NULL in production.
-- Example:
-- UPDATE courses SET lecturer_id = <approved_lecturer_id> WHERE lecturer_id IS NULL;
-- ALTER TABLE courses ALTER COLUMN lecturer_id SET NOT NULL;
