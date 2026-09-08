import json
import os
from contextlib import contextmanager
from pathlib import Path

from psycopg import connect as pg_connect
from psycopg.rows import dict_row
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
load_dotenv(ROOT / ".env")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres@127.0.0.1:5432/class_schedule")


@contextmanager
def connect():
    with pg_connect(DATABASE_URL, row_factory=dict_row) as db:
        yield db


def init_db():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS schedules (
            id BIGSERIAL PRIMARY KEY, name VARCHAR(80) NOT NULL,
            term VARCHAR(80) NOT NULL DEFAULT '', start_date DATE, end_date DATE,
            background TEXT NOT NULL DEFAULT '', created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        db.execute("ALTER TABLE schedules ADD COLUMN IF NOT EXISTS end_date DATE")
        db.execute("""CREATE TABLE IF NOT EXISTS courses (
            id BIGSERIAL PRIMARY KEY,
            schedule_id BIGINT NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
            name VARCHAR(80) NOT NULL, teacher VARCHAR(40) NOT NULL DEFAULT '',
            room VARCHAR(40) NOT NULL DEFAULT '', weekday SMALLINT NOT NULL CHECK (weekday BETWEEN 1 AND 7),
            start_section SMALLINT NOT NULL CHECK (start_section BETWEEN 1 AND 12),
            end_section SMALLINT NOT NULL CHECK (end_section BETWEEN 1 AND 12),
            weeks JSONB NOT NULL DEFAULT '[]'::jsonb, color VARCHAR(16) NOT NULL DEFAULT '#5B8DEF',
            CHECK (end_section >= start_section))""")
        if not db.execute("SELECT 1 FROM schedules LIMIT 1").fetchone():
            sid = db.execute(
                "INSERT INTO schedules(name,term,start_date) VALUES(%s,%s,%s) RETURNING id",
                ("我的课表", "2026-2027-1学期", "2026-09-07"),
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
