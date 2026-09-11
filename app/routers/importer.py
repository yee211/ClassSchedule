import json
import logging
import time
import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ..ai import parse_with_ai
from ..auth import get_current_user
from ..db import DATA, connect
from ..excel import validate_excel_container
from ..parser import parse_excel_schedule
from ..settings import settings

router = APIRouter(prefix="/api", tags=["import"])

UPLOADS = DATA / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger("classschedule")


def parse_schedule_date(value: str, label: str):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise HTTPException(400, f"{label}格式应为 YYYY-MM-DD") from error


@router.post("/import")
def import_file(
    file: UploadFile = File(...),
    start_date: str = Form(""),
    end_date: str = Form(""),
    user=Depends(get_current_user),
):
    """上传 Excel 课表文件（.xlsx / .xlsm / .xls），优先由 AI 提取，失败时自动回退本地解析。"""
    schedule_start = parse_schedule_date(start_date, "学期开始日期")
    schedule_end = parse_schedule_date(end_date, "学期结束日期")
    if schedule_start and schedule_end and schedule_end < schedule_start:
        raise HTTPException(400, "学期结束日期不能早于开始日期")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".xlsx", ".xlsm", ".xls"}:
        raise HTTPException(400, "仅支持 Excel 课表（.xlsx / .xlsm / .xls）")
    target = UPLOADS / f"{uuid.uuid4().hex}{suffix}"
    started = time.perf_counter()
    try:
        with target.open("wb") as out:
            total = 0
            while chunk := file.file.read(1024 * 1024):
                total += len(chunk)
                if total > settings.max_upload_bytes:
                    raise HTTPException(413, f"文件不能超过 {settings.max_upload_bytes // 1024 // 1024} MB")
                out.write(chunk)
        try:
            validate_excel_container(target, suffix)
        except ValueError as error:
            raise HTTPException(400, str(error)) from error
        parsed, engine = parse_with_ai(target)
        if not parsed:
            # AI 未配置、超时或识别失败时静默回退到确定性解析，保证导入功能不中断
            try:
                parsed = parse_excel_schedule(target)
            except Exception as error:
                logger.warning("本地 Excel 解析失败: %s", error.__class__.__name__)
                parsed = None
            engine = f"excel-fallback({engine})"
        if not parsed:
            # 带上引擎标记，便于用户与运维分辨到底是 AI 未配置还是文件本身无法识别
            raise HTTPException(422, f"AI 与本地解析均未能从该 Excel 中识别出课程（{engine}），请确认文件包含课程明细")

        with connect() as db:
            db.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (f"{user['id']}|{parsed['term']}",))
            schedule = db.execute(
                """SELECT * FROM schedules WHERE user_id=%s AND term=%s
                   AND variant_type IN ('original','draft') ORDER BY id DESC LIMIT 1 FOR UPDATE""",
                (user["id"], parsed["term"]),
            ).fetchone()
            replaced = schedule is not None
            if schedule:
                schedule = db.execute(
                    """UPDATE schedules SET name=%s,start_date=%s,end_date=%s,variant_type='original'
                    WHERE id=%s RETURNING *""",
                    (parsed["name"], schedule_start, schedule_end, schedule["id"]),
                ).fetchone()
                db.execute("DELETE FROM courses WHERE schedule_id=%s", (schedule["id"],))
            else:
                schedule = db.execute(
                    """INSERT INTO schedules(user_id,name,term,start_date,end_date,variant_type)
                       VALUES(%s,%s,%s,%s,%s,'original') RETURNING *""",
                    (user["id"], parsed["name"], parsed["term"], schedule_start, schedule_end),
                ).fetchone()
            rows = [(
                schedule["id"], course["name"], course["teacher"], course["room"], course["weekday"],
                course["start_section"], course["end_section"], json.dumps(course["weeks"]), course["color"],
            ) for course in parsed["courses"]]
            with db.cursor() as cursor:
                cursor.executemany("""INSERT INTO courses
                    (schedule_id,name,teacher,room,weekday,start_section,end_section,weeks,color)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)""", rows)
        duration_ms = round((time.perf_counter() - started) * 1000)
        logger.info(json.dumps({
            "event": "schedule_import",
            "user_id": user["id"],
            "engine": engine,
            "imported": len(rows),
            "replaced": replaced,
            "file_bytes": total,
            "duration_ms": duration_ms,
        }, ensure_ascii=False))
        return {"engine": engine, "imported": len(rows), "schedule_id": schedule["id"], "replaced": replaced, "duration_ms": duration_ms}
    finally:
        # 上传文件仅用于本次解析，用完即删，避免 data/uploads 无限堆积
        target.unlink(missing_ok=True)
