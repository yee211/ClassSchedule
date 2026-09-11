"""Preserve imported schedules and add one editable adjusted variant."""
from alembic import op

revision = "20260911_03"
down_revision = "20260911_02"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE schedules ADD COLUMN IF NOT EXISTS variant_type VARCHAR(16) NOT NULL DEFAULT 'draft'")
    op.execute(
        "ALTER TABLE schedules ADD COLUMN IF NOT EXISTS source_schedule_id BIGINT REFERENCES schedules(id) ON DELETE CASCADE"
    )
    op.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS source_course_id BIGINT REFERENCES courses(id) ON DELETE SET NULL")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_schedules_adjusted_source "
        "ON schedules(source_schedule_id) WHERE variant_type='adjusted'"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_courses_source_course_id ON courses(source_course_id)")


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_courses_source_course_id")
    op.execute("DROP INDEX IF EXISTS uq_schedules_adjusted_source")
    op.execute("ALTER TABLE courses DROP COLUMN IF EXISTS source_course_id")
    op.execute("ALTER TABLE schedules DROP COLUMN IF EXISTS source_schedule_id")
    op.execute("ALTER TABLE schedules DROP COLUMN IF EXISTS variant_type")
