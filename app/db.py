import json
import os
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from psycopg import connect as pg_connect
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .auth import hash_password

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
load_dotenv(ROOT / ".env")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres@127.0.0.1:5432/class_schedule")

_pool: ConnectionPool | None = None


def init_pool(min_size: int = 2, max_size: int = 10):
    """初始化数据库连接池，在 FastAPI lifespan 中启动。"""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=DATABASE_URL,
            min_size=min_size,
            max_size=max_size,
            kwargs={"row_factory": dict_row},
            open=True,
        )
    return _pool


def close_pool():
    """优雅关闭数据库连接池。"""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


@contextmanager
def connect():
    """获取数据库连接上下文。优先从连接池借用，未初始化连接池时自动降级为单次独立连接。"""
    if _pool is not None:
        with _pool.connection() as db:
            yield db
    else:
        with pg_connect(DATABASE_URL, row_factory=dict_row) as db:
            yield db



def _ensure_default_user(db):
    """确保存在默认账号，用于接管升级前无主的课表数据。登录凭证为邮箱。"""
    username = os.getenv("DEFAULT_USERNAME", "demo")
    email = os.getenv("DEFAULT_EMAIL", "demo@example.com").strip().lower()
    password = os.getenv("DEFAULT_PASSWORD", "demo1234")
    row = db.execute("SELECT id,email FROM users WHERE username=%s", (username,)).fetchone()
    if row:
        # 将升级迁移回填的占位邮箱规整为配置的默认邮箱（仅当该邮箱未被占用）
        if row["email"] != email:
            db.execute("""UPDATE users SET email=%s WHERE id=%s
                AND NOT EXISTS (SELECT 1 FROM users u WHERE u.email=%s)""", (email, row["id"], email))
        return row["id"]
    return db.execute(
        "INSERT INTO users(email,username,password_hash) VALUES(%s,%s,%s) RETURNING id",
        (email, username, hash_password(password)),
    ).fetchone()["id"]


def init_db():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS users (
            id BIGSERIAL PRIMARY KEY,
            email VARCHAR(254) NOT NULL UNIQUE,
            username VARCHAR(40) NOT NULL UNIQUE,
            password_hash VARCHAR(200) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        # 兼容升级：为已存在的 users 表补充 email 列，并按 username 回填占位邮箱
        db.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(254)")
        db.execute("UPDATE users SET email = lower(username) || '@legacy.local' WHERE email IS NULL")
        db.execute("ALTER TABLE users ALTER COLUMN email SET NOT NULL")
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS users_email_key ON users(email)")
        db.execute("""CREATE TABLE IF NOT EXISTS schedules (
            id BIGSERIAL PRIMARY KEY, name VARCHAR(80) NOT NULL,
            term VARCHAR(80) NOT NULL DEFAULT '', start_date DATE, end_date DATE,
            background TEXT NOT NULL DEFAULT '', created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        db.execute("ALTER TABLE schedules ADD COLUMN IF NOT EXISTS end_date DATE")
        db.execute("ALTER TABLE schedules ADD COLUMN IF NOT EXISTS user_id BIGINT REFERENCES users(id) ON DELETE CASCADE")
        db.execute("""CREATE TABLE IF NOT EXISTS courses (
            id BIGSERIAL PRIMARY KEY,
            schedule_id BIGINT NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
            name VARCHAR(80) NOT NULL, teacher VARCHAR(40) NOT NULL DEFAULT '',
            room VARCHAR(40) NOT NULL DEFAULT '', weekday SMALLINT NOT NULL CHECK (weekday BETWEEN 1 AND 7),
            start_section SMALLINT NOT NULL CHECK (start_section BETWEEN 1 AND 12),
            end_section SMALLINT NOT NULL CHECK (end_section BETWEEN 1 AND 12),
            weeks JSONB NOT NULL DEFAULT '[]'::jsonb, color VARCHAR(16) NOT NULL DEFAULT '#5B8DEF',
            CHECK (end_section >= start_section))""")
        # 将升级前无主的课表归属到默认账号，随后强制 user_id 非空
        default_user_id = _ensure_default_user(db)
        db.execute("UPDATE schedules SET user_id=%s WHERE user_id IS NULL", (default_user_id,))
        db.execute("ALTER TABLE schedules ALTER COLUMN user_id SET NOT NULL")
        # 索引优化：外键关联与高频查询加速
        db.execute("CREATE INDEX IF NOT EXISTS idx_courses_schedule_id ON courses(schedule_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_schedules_user_id ON schedules(user_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_schedules_user_id_term ON schedules(user_id, term)")

        if not db.execute("SELECT 1 FROM schedules LIMIT 1").fetchone():
            sid = db.execute(
                "INSERT INTO schedules(user_id,name,term,start_date) VALUES(%s,%s,%s,%s) RETURNING id",
                (default_user_id, "我的课表", "2026-2027-1学期", "2026-09-07"),
            ).fetchone()["id"]
            weeks = json.dumps(list(range(1, 9)))
            demo = [
                (sid,"数据采集与预处理","李老师","南313",2,1,2,weeks,"#EF4770"),
                (sid,"计算机组成原理","李老师","南407",3,1,2,weeks,"#F1763F"),
                (sid,"开源软件开发","张老师","南508",4,1,2,weeks,"#8D68D7"),
                (sid,"应用程序设计","付老师","南405",3,3,4,weeks,"#63B75A"),
                (sid,"计算机网络","龙老师","南312",4,3,4,weeks,"#3D9DDB"),
            ]
            with db.cursor() as cursor:
                cursor.executemany("""INSERT INTO courses
                    (schedule_id,name,teacher,room,weekday,start_section,end_section,weeks,color)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)""", demo)


def row_dict(row):
    result = dict(row)
    for key in ("start_date", "end_date", "created_at"):
        if result.get(key):
            result[key] = result[key].isoformat()
    return result
