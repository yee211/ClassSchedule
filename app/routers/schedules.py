from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import get_current_user
from ..db import connect, row_dict

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


class ScheduleUpdate(BaseModel):
    name: str | None = None
    term: str | None = None
    start_date: str | None = None
    end_date: str | None = None


def parse_schedule_date(value: str | None, label: str):
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise HTTPException(400, f"{label}格式应为 YYYY-MM-DD") from error


@router.get("")
def list_schedules(user=Depends(get_current_user)):
    """获取当前用户的所有课表及其课程列表。通过批量查询消除 N+1 性能瓶颈。"""
    with connect() as db:
        rows = db.execute(
            "SELECT * FROM schedules WHERE user_id=%s ORDER BY id DESC",
            (user["id"],),
        ).fetchall()
        if not rows:
            return []

        schedule_ids = [row["id"] for row in rows]
        # 一次性批量获取当前用户全部课表中的课程
        courses_rows = db.execute(
            "SELECT * FROM courses WHERE schedule_id = ANY(%s) ORDER BY weekday, start_section",
            (schedule_ids,),
        ).fetchall()

        courses_by_schedule: dict[int, list[dict]] = {sid: [] for sid in schedule_ids}
        for course in courses_rows:
            courses_by_schedule[course["schedule_id"]].append(row_dict(course))

        result = []
        for row in rows:
            item = row_dict(row)
            item["courses"] = courses_by_schedule.get(row["id"], [])
            result.append(item)
        return result


@router.put("/{schedule_id}")
def update_schedule(schedule_id: int, payload: ScheduleUpdate, user=Depends(get_current_user)):
    """更新课表的基础信息（名称、学期、开学日期、结束日期）。"""
    with connect() as db:
        schedule = db.execute(
            "SELECT * FROM schedules WHERE id=%s AND user_id=%s",
            (schedule_id, user["id"]),
        ).fetchone()
        if not schedule:
            raise HTTPException(404, "课表不存在")

        new_name = payload.name.strip() if payload.name is not None else schedule["name"]
        new_term = payload.term.strip() if payload.term is not None else schedule["term"]
        new_start = parse_schedule_date(payload.start_date, "开学日期") if payload.start_date is not None else schedule["start_date"]
        new_end = parse_schedule_date(payload.end_date, "结束日期") if payload.end_date is not None else schedule["end_date"]

        if new_start and new_end and new_end < new_start:
            raise HTTPException(400, "结束日期不能早于开学日期")

        updated = db.execute(
            """UPDATE schedules SET name=%s, term=%s, start_date=%s, end_date=%s
               WHERE id=%s AND user_id=%s RETURNING *""",
            (new_name, new_term, new_start, new_end, schedule_id, user["id"]),
        ).fetchone()

        courses_rows = db.execute(
            "SELECT * FROM courses WHERE schedule_id=%s ORDER BY weekday, start_section",
            (schedule_id,),
        ).fetchall()

        result = row_dict(updated)
        result["courses"] = [row_dict(c) for c in courses_rows]
        return result


@router.delete("/{schedule_id}", status_code=204)
def delete_schedule(schedule_id: int, user=Depends(get_current_user)):
    """删除指定的课表，级联删除下属所有课程。"""
    with connect() as db:
        if not db.execute(
            "DELETE FROM schedules WHERE id=%s AND user_id=%s RETURNING id",
            (schedule_id, user["id"]),
        ).fetchone():
            raise HTTPException(404, "课表不存在")

