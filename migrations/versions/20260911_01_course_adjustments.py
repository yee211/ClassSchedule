"""Add per-week course adjustments."""
from alembic import op

revision = "20260911_01"
down_revision = "20260910_02"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE IF NOT EXISTS course_adjustments (
        id BIGSERIAL PRIMARY KEY,
        course_id BIGINT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        week SMALLINT NOT NULL CHECK (week BETWEEN 1 AND 30),
        weekday SMALLINT NOT NULL CHECK (weekday BETWEEN 1 AND 7),
        start_section SMALLINT NOT NULL CHECK (start_section BETWEEN 1 AND 12),
        end_section SMALLINT NOT NULL CHECK (end_section BETWEEN 1 AND 12),
        room VARCHAR(40) NOT NULL DEFAULT '',
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (course_id, week),
        CHECK (end_section >= start_section))""")
    op.execute("CREATE INDEX IF NOT EXISTS idx_course_adjustments_course_id ON course_adjustments(course_id)")


def downgrade():
    op.execute("DROP TABLE IF EXISTS course_adjustments")
