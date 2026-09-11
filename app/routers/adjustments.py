import json
import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from ..adjustment_ai import parse_adjustment_image
from ..auth import get_current_user
from ..db import connect, row_dict
from ..settings import settings
from .courses import adjustment_conflicts

router = APIRouter(prefix="/api/adjustments", tags=["adjustments"])
IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def valid_image_signature(content: bytes, mime_type: str) -> bool:
    if mime_type == "image/jpeg":
        return content.startswith(b"\xff\xd8\xff")
    if mime_type == "image/png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if mime_type == "image/webp":
        return len(content) >= 12 and content.startswith(b"RIFF") and content[8:12] == b"WEBP"
    return False


def normalized(value: str) -> str:
    return re.sub(r"[\s（）()\-—_·]", "", str(value or "")).lower()


def match_course(courses, item):
    candidates = []
    notice_name = normalized(item["course_name"])
    notice_teacher = normalized(item["teacher"])
    for course in courses:
        if course["weekday"] != item["old_weekday"]:
            continue
        if course["start_section"] != item["old_start_section"] or course["end_section"] != item["old_end_section"]:
            continue
        weeks = course["weeks"] or []
        if weeks and item["week"] not in weeks:
            continue
        course_name = normalized(course["name"])
        course_teacher = normalized(course["teacher"])
        name_match = course_name == notice_name or course_name in notice_name or notice_name in course_name
        teacher_match = not notice_teacher or course_teacher == notice_teacher
        if name_match and teacher_match:
            candidates.append(course)
    return candidates[0] if len(candidates) == 1 else None, len(candidates)


class ApplyItem(BaseModel):
    course_id: int
    week: int = Field(ge=1, le=30)
    weekday: int = Field(ge=1, le=7)
    start_section: int = Field(ge=1, le=12)
    end_section: int = Field(ge=1, le=12)
    room: str = Field(default="", max_length=40)


class ApplyRequest(BaseModel):
    schedule_id: int
    items: list[ApplyItem] = Field(min_length=1, max_length=100)


def match_extracted(schedule_id: int, user_id: int, extracted: list[dict]):
    with connect() as db:
        if not db.execute("SELECT 1 FROM schedules WHERE id=%s AND user_id=%s", (schedule_id, user_id)).fetchone():
            raise HTTPException(404, "课表不存在")
        courses = db.execute("SELECT * FROM courses WHERE schedule_id=%s", (schedule_id,)).fetchall()
    results = []
    for item in extracted:
        course, count = match_course(courses, item)
        status = "matched" if course else ("ambiguous" if count > 1 else "unmatched")
        results.append({**item, "status": status, "course_id": course["id"] if course else None,
                        "matched_course_name": course["name"] if course else "", "selected": bool(course)})
    return {"items": results, "matched": sum(row["status"] == "matched" for row in results), "total": len(results)}


@router.post("/parse")
def parse_notice(file: UploadFile = File(...), schedule_id: int = Form(...), user=Depends(get_current_user)):
    if file.content_type not in IMAGE_TYPES:
        raise HTTPException(400, "仅支持 JPG、PNG 或 WebP 图片")
    content = file.file.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(413, f"图片不能超过 {settings.max_upload_bytes // 1024 // 1024} MB")
    if not content:
        raise HTTPException(400, "图片内容为空")
    if not valid_image_signature(content, file.content_type):
        raise HTTPException(400, "图片内容与文件格式不匹配")
    try:
        extracted = parse_adjustment_image(content, file.content_type)
    except RuntimeError as error:
        raise HTTPException(422, str(error)) from error
    return match_extracted(schedule_id, user["id"], extracted)


@router.post("/apply")
def apply_notice(payload: ApplyRequest, user=Depends(get_current_user)):
    with connect() as db:
        if not db.execute("SELECT 1 FROM schedules WHERE id=%s AND user_id=%s", (payload.schedule_id, user["id"])).fetchone():
            raise HTTPException(404, "课表不存在")
        seen = set()
        details = []
        for item in payload.items:
            key = (item.course_id, item.week)
            if key in seen:
                raise HTTPException(400, "同一课程同一周存在重复调课记录")
            seen.add(key)
            course = db.execute("SELECT * FROM courses WHERE id=%s AND schedule_id=%s", (item.course_id, payload.schedule_id)).fetchone()
            if not course or (course["weeks"] and item.week not in course["weeks"]):
                raise HTTPException(400, "调课记录与当前课表不匹配")
            if item.end_section < item.start_section:
                raise HTTPException(400, "结束节次不能早于开始节次")
            if adjustment_conflicts(db, item.course_id, item.week, item.weekday, item.start_section, item.end_section):
                raise HTTPException(409, f"第 {item.week} 周的目标时段与现有课程冲突")
            db.execute("""INSERT INTO course_adjustments(course_id,week,weekday,start_section,end_section,room)
                VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(course_id,week) DO UPDATE SET
                weekday=EXCLUDED.weekday,start_section=EXCLUDED.start_section,
                end_section=EXCLUDED.end_section,room=EXCLUDED.room""",
                (item.course_id, item.week, item.weekday, item.start_section, item.end_section, item.room))
            details.append({
                "course_id": item.course_id,
                "course_name": course["name"],
                "week": item.week,
                "old_weekday": course["weekday"],
                "old_start_section": course["start_section"],
                "old_end_section": course["end_section"],
                "old_room": course["room"] or "",
                "new_weekday": item.weekday,
                "new_start_section": item.start_section,
                "new_end_section": item.end_section,
                "new_room": item.room or "",
            })

        if details:
            db.execute(
                """INSERT INTO course_change_logs(schedule_id, action_type, title, description, details)
                   VALUES(%s, %s, %s, %s, %s::jsonb)""",
                (
                    payload.schedule_id,
                    "batch_import",
                    "图片识别调课",
                    f"一次性调整了 {len(details)} 门次课程",
                    json.dumps(details, ensure_ascii=False),
                ),
            )
    return {"applied": len(payload.items)}


@router.get("/records")
def list_records(schedule_id: int, user=Depends(get_current_user)):
    """获取指定课表的调课与课程修改历史记录。"""
    with connect() as db:
        if not db.execute("SELECT 1 FROM schedules WHERE id=%s AND user_id=%s", (schedule_id, user["id"])).fetchone():
            raise HTTPException(404, "课表不存在")
        rows = db.execute(
            """SELECT * FROM course_change_logs
               WHERE schedule_id=%s
               ORDER BY id DESC LIMIT 100""",
            (schedule_id,),
        ).fetchall()
        active_adjustments = db.execute(
            """SELECT ca.course_id, ca.week
               FROM course_adjustments ca
               JOIN courses c ON c.id=ca.course_id
               WHERE c.schedule_id=%s""",
            (schedule_id,),
        ).fetchall()
        active_keys = {(a["course_id"], a["week"]) for a in active_adjustments}

        results = []
        for row in rows:
            item = row_dict(row)
            details = item.get("details") or []
            if isinstance(details, list):
                for sub in details:
                    if isinstance(sub, dict) and "course_id" in sub and "week" in sub:
                        sub["can_revoke"] = (sub["course_id"], sub["week"]) in active_keys
            item["details"] = details
            item["can_revoke"] = any(isinstance(sub, dict) and sub.get("can_revoke") for sub in details)
            results.append(item)
        return results
