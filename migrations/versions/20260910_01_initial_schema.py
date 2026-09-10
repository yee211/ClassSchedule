"""Establish the managed ClassSchedule schema."""
from alembic import op

revision = "20260910_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE IF NOT EXISTS users (
        id BIGSERIAL PRIMARY KEY,
        email VARCHAR(254) NOT NULL UNIQUE,
        username VARCHAR(40) NOT NULL UNIQUE,
        password_hash VARCHAR(200) NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
    op.execute("""CREATE TABLE IF NOT EXISTS schedules (
        id BIGSERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name VARCHAR(80) NOT NULL,
        term VARCHAR(80) NOT NULL DEFAULT '',
        start_date DATE,
        end_date DATE,
        background TEXT NOT NULL DEFAULT '',
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
    op.execute("""CREATE TABLE IF NOT EXISTS courses (
        id BIGSERIAL PRIMARY KEY,
        schedule_id BIGINT NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
        name VARCHAR(80) NOT NULL,
        teacher VARCHAR(40) NOT NULL DEFAULT '',
        room VARCHAR(40) NOT NULL DEFAULT '',
        weekday SMALLINT NOT NULL CHECK (weekday BETWEEN 1 AND 7),
        start_section SMALLINT NOT NULL CHECK (start_section BETWEEN 1 AND 12),
        end_section SMALLINT NOT NULL CHECK (end_section BETWEEN 1 AND 12),
        weeks JSONB NOT NULL DEFAULT '[]'::jsonb,
        color VARCHAR(16) NOT NULL DEFAULT '#5B8DEF',
        CHECK (end_section >= start_section))""")
    # A pre-Alembic installation may already have these tables. Add the
    # compatibility columns before creating indexes that reference them.
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(254)")
    op.execute("ALTER TABLE schedules ADD COLUMN IF NOT EXISTS user_id BIGINT REFERENCES users(id) ON DELETE CASCADE")
    op.execute("ALTER TABLE schedules ADD COLUMN IF NOT EXISTS end_date DATE")
    op.execute("CREATE INDEX IF NOT EXISTS idx_courses_schedule_id ON courses(schedule_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_schedules_user_id ON schedules(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_schedules_user_id_term ON schedules(user_id, term)")


def downgrade():
    op.execute("DROP TABLE IF EXISTS courses")
    op.execute("DROP TABLE IF EXISTS schedules")
    op.execute("DROP TABLE IF EXISTS users")
