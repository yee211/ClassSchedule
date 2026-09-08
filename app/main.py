import json
import shutil
import uuid
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from .db import DATA, connect, init_db, row_dict
from .ocr import extract_text, parse_structured_schedule, parse_xlsx_schedule, suggest_courses

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIST = ROOT / "frontend" / "dist"
UPLOADS = DATA / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="简课", version="2.0.0", lifespan=lifespan)


class CourseIn(BaseModel):
    schedule_id: int
    name: str = Field(min_length=1, max_length=80)
    teacher: str = Field(default="", max_length=40)
    room: str = Field(default="", max_length=40)
    weekday: int = Field(ge=1, le=7)
    start_section: int = Field(ge=1, le=12)
    end_section: int = Field(ge=1, le=12)
    weeks: list[int] = Field(default_factory=list)
    color: str = "#5B8DEF"

    @field_validator("weeks")
    @classmethod
    def valid_weeks(cls, value):
        if any(week < 1 or week > 30 for week in value):
            raise ValueError("周次必须在 1 到 30 之间")
        return sorted(set(value))


@app.get("/api/health")
def health():
    with connect() as db:
        db.execute("SELECT 1")
    return {"ok": True}


@app.get("/api/schedules")
def schedules():
    with connect() as db:
        rows = db.execute("SELECT * FROM schedules ORDER BY id DESC").fetchall()
        result = []
        for row in rows:
            item = row_dict(row)
            courses = db.execute("SELECT * FROM courses WHERE schedule_id=%s ORDER BY weekday,start_section", (row["id"],)).fetchall()
            item["courses"] = [row_dict(course) for course in courses]
            result.append(item)
        return result


def values(course):
    data = course.model_dump()
    return (data["schedule_id"],data["name"],data["teacher"],data["room"],data["weekday"],
            data["start_section"],data["end_section"],json.dumps(data["weeks"]),data["color"])


@app.post("/api/courses", status_code=201)
def add_course(course: CourseIn):
    if course.end_section < course.start_section:
        raise HTTPException(400, "结束节次不能早于开始节次")
    with connect() as db:
        if not db.execute("SELECT 1 FROM schedules WHERE id=%s", (course.schedule_id,)).fetchone():
            raise HTTPException(404, "课表不存在")
        row = db.execute("""INSERT INTO courses
            (schedule_id,name,teacher,room,weekday,start_section,end_section,weeks,color)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s) RETURNING *""", values(course)).fetchone()
        return row_dict(row)


@app.put("/api/courses/{course_id}")
def update_course(course_id: int, course: CourseIn):
    if course.end_section < course.start_section:
        raise HTTPException(400, "结束节次不能早于开始节次")
    with connect() as db:
        row = db.execute("""UPDATE courses SET schedule_id=%s,name=%s,teacher=%s,room=%s,
            weekday=%s,start_section=%s,end_section=%s,weeks=%s::jsonb,color=%s
            WHERE id=%s RETURNING *""", (*values(course), course_id)).fetchone()
        if not row:
            raise HTTPException(404, "课程不存在")
        return row_dict(row)


@app.delete("/api/courses/{course_id}", status_code=204)
def delete_course(course_id: int):
    with connect() as db:
        if not db.execute("DELETE FROM courses WHERE id=%s RETURNING id", (course_id,)).fetchone():
            raise HTTPException(404, "课程不存在")


def parse_schedule_date(value: str, label: str):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise HTTPException(400, f"{label}格式应为 YYYY-MM-DD") from error


@app.post("/api/import")
def import_file(
    file: UploadFile = File(...),
    start_date: str = Form(""),
    end_date: str = Form(""),
):
    schedule_start = parse_schedule_date(start_date, "学期开始日期")
    schedule_end = parse_schedule_date(end_date, "学期结束日期")
    if schedule_start and schedule_end and schedule_end < schedule_start:
        raise HTTPException(400, "学期结束日期不能早于开始日期")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".xlsx", ".xlsm", ".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(400, "仅支持 PDF、XLSX、XLSM、PNG、JPG、WEBP")
    target = UPLOADS / f"{uuid.uuid4().hex}{suffix}"
    with target.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    parsed = parse_xlsx_schedule(target) or parse_structured_schedule(target)
    if suffix in {".xlsx", ".xlsm"} and not parsed:
        raise HTTPException(422, "未找到‘课程明细速查表’或可识别的课程明细")
    if parsed:
        with connect() as db:
            schedule = db.execute(
                "INSERT INTO schedules(name,term,start_date,end_date) VALUES(%s,%s,%s,%s) RETURNING *",
                (parsed["name"], parsed["term"], schedule_start, schedule_end),
            ).fetchone()
            rows = [(
                schedule["id"], course["name"], course["teacher"], course["room"], course["weekday"],
                course["start_section"], course["end_section"], json.dumps(course["weeks"]), course["color"],
            ) for course in parsed["courses"]]
            with db.cursor() as cursor:
                cursor.executemany("""INSERT INTO courses
                    (schedule_id,name,teacher,room,weekday,start_section,end_section,weeks,color)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)""", rows)
        engine = "xlsx-table" if suffix in {".xlsx", ".xlsm"} else "pdf-table"
        return {"engine": engine, "imported": len(rows), "schedule_id": schedule["id"], "suggestions": []}
    text, engine = extract_text(target)
    return {"engine": engine, "text": text, "suggestions": suggest_courses(text)}


if FRONTEND_DIST.exists():
    if (FRONTEND_DIST / "assets").exists():
        app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    def frontend(path: str):
        candidate = FRONTEND_DIST / path
        return FileResponse(candidate if candidate.is_file() else FRONTEND_DIST / "index.html")
