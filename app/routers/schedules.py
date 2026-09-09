from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..db import connect, row_dict

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


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


@router.delete("/{schedule_id}", status_code=204)
def delete_schedule(schedule_id: int, user=Depends(get_current_user)):
    """删除指定的课表，级联删除下属所有课程。"""
    with connect() as db:
        if not db.execute(
            "DELETE FROM schedules WHERE id=%s AND user_id=%s RETURNING id",
            (schedule_id, user["id"]),
        ).fetchone():
            raise HTTPException(404, "课表不存在")
