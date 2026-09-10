"""Add columns missing from databases created before Alembic management.

Legacy rows deliberately remain unassigned. Ownership must be migrated with an
explicit administrator decision instead of silently exposing data to a default
account.
"""

from alembic import op

revision = "20260910_02"
down_revision = "20260910_01"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(254)")
    op.execute("ALTER TABLE schedules ADD COLUMN IF NOT EXISTS end_date DATE")
    op.execute(
        "ALTER TABLE schedules ADD COLUMN IF NOT EXISTS user_id BIGINT "
        "REFERENCES users(id) ON DELETE CASCADE"
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS users_email_key ON users(email) WHERE email IS NOT NULL")
    op.execute("CREATE INDEX IF NOT EXISTS idx_courses_schedule_id ON courses(schedule_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_schedules_user_id ON schedules(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_schedules_user_id_term ON schedules(user_id, term)")


def downgrade():
    # Do not remove compatibility columns: they may contain data written by the
    # current application after this migration was applied.
    pass
