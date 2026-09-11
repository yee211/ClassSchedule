"""Add course change logs table for tracking batch adjustments, position moves, and manual edits."""
from alembic import op

revision = "20260911_02"
down_revision = "20260911_01"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE IF NOT EXISTS course_change_logs (
        id BIGSERIAL PRIMARY KEY,
        schedule_id BIGINT NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
        course_id BIGINT REFERENCES courses(id) ON DELETE SET NULL,
        action_type VARCHAR(32) NOT NULL,
        title VARCHAR(120) NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        details JSONB NOT NULL DEFAULT '[]'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    op.execute("CREATE INDEX IF NOT EXISTS idx_course_change_logs_schedule_id ON course_change_logs(schedule_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_course_change_logs_created_at ON course_change_logs(created_at DESC)")


def downgrade():
    op.execute("DROP TABLE IF EXISTS course_change_logs")
