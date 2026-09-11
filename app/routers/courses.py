import json

from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..db import connect, row_dict
from ..schemas import CourseAdjustmentIn, CourseIn

router = APIRouter(prefix="/api/courses", tags=["courses"])


def adjustment_conflicts(db, course_id: int, week: int, weekday: int, start_section: int, end_section: int) -> bool:
    owner = db.execute("SELECT schedule_id FROM courses WHERE id=%s", (course_id,)).fetchone()
    if not owner:
        return False
    rows = db.execute(
        """SELECT c.*, a.week AS adjusted_week, a.weekday AS adjusted_weekday,
                  a.start_section AS adjusted_start, a.end_section AS adjusted_end
           FROM courses c LEFT JOIN course_adjustments a
             ON a.course_id=c.id AND a.week=%s
           WHERE c.schedule_id=%s AND c.id<>%s""",
        (week, owner["schedule_id"], course_id),
    ).fetchall()
    for row in rows:
        if row["weeks"] and week not in row["weeks"]:
            continue
        other_day = row["adjusted_weekday"] if row["adjusted_week"] is not None else row["weekday"]
        other_start = row["adjusted_start"] if row["adjusted_week"] is not None else row["start_section"]
        other_end = row["adjusted_end"] if row["adjusted_week"] is not None else row["end_section"]
        if other_day == weekday and start_section <= other_end and end_section >= other_start:
            return True
    return False


def course_row_values(course: CourseIn):
    data = course.model_dump()
    return (
        data["schedule_id"],
        data["name"],
        data["teacher"],
        data["room"],
        data["weekday"],
        data["start_section"],
        data["end_section"],
        json.dumps(data["weeks"]),
        data["color"],
    )


@router.post("", status_code=201)
def add_course(course: CourseIn, user=Depends(get_current_user)):
    """添加单门课程安排。"""
    if course.end_section < course.start_section:
        raise HTTPException(400, "结束节次不能早于开始节次")
    with connect() as db:
        if not db.execute(
            "SELECT 1 FROM schedules WHERE id=%s AND user_id=%s",
            (course.schedule_id, user["id"]),
        ).fetchone():
            raise HTTPException(404, "课表不存在")
        row = db.execute(
            """INSERT INTO courses
            (schedule_id,name,teacher,room,weekday,start_section,end_section,weeks,color)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s) RETURNING *""",
            course_row_values(course),
        ).fetchone()
        return row_dict(row)


DAYS_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


@router.put("/{course_id}")
def update_course(course_id: int, course: CourseIn, source: str = "manual", user=Depends(get_current_user)):
    """更新指定课程信息。"""
    if course.end_section < course.start_section:
        raise HTTPException(400, "结束节次不能早于开始节次")
    with connect() as db:
        if not db.execute(
            "SELECT 1 FROM schedules WHERE id=%s AND user_id=%s",
            (course.schedule_id, user["id"]),
        ).fetchone():
            raise HTTPException(404, "课表不存在")
        old_course = db.execute(
            "SELECT * FROM courses WHERE id=%s AND schedule_id IN (SELECT id FROM schedules WHERE user_id=%s)",
            (course_id, user["id"]),
        ).fetchone()
        if not old_course:
            raise HTTPException(404, "课程不存在")

        row = db.execute(
            """UPDATE courses SET schedule_id=%s,name=%s,teacher=%s,room=%s,
            weekday=%s,start_section=%s,end_section=%s,weeks=%s::jsonb,color=%s
            WHERE id=%s AND schedule_id IN (SELECT id FROM schedules WHERE user_id=%s) RETURNING *""",
            (*course_row_values(course), course_id, user["id"]),
        ).fetchone()
        if not row:
            raise HTTPException(404, "课程不存在")

        diffs = []
        if (old_course["weekday"] != course.weekday or
            old_course["start_section"] != course.start_section or
            old_course["end_section"] != course.end_section):
            diffs.append({
                "field": "time",
                "label": "上课时间",
                "old": f"{DAYS_NAMES[old_course['weekday']-1]} 第{old_course['start_section']}-{old_course['end_section']}节",
                "new": f"{DAYS_NAMES[course.weekday-1]} 第{course.start_section}-{course.end_section}节",
            })
        if (old_course["room"] or "") != (course.room or ""):
            diffs.append({
                "field": "room",
                "label": "教室地点",
                "old": old_course["room"] or "未设置",
                "new": course.room or "未设置",
            })
        if (old_course["teacher"] or "") != (course.teacher or ""):
            diffs.append({
                "field": "teacher",
                "label": "授课教师",
                "old": old_course["teacher"] or "未设置",
                "new": course.teacher or "未设置",
            })
        if old_course["name"] != course.name:
            diffs.append({
                "field": "name",
                "label": "课程名称",
                "old": old_course["name"],
                "new": course.name,
            })

        if diffs:
            if source == "drag":
                action_type = "drag_move"
                title = "位置移动（修改时间）"
                description = f"拖拽将《{course.name}》移动至 {DAYS_NAMES[course.weekday-1]} 第{course.start_section}-{course.end_section}节（所有周次）"
            else:
                action_type = "manual_edit"
                title = "主动编辑课程"
                description = f"修改了《{course.name}》的" + "、".join(d["label"] for d in diffs)
            db.execute(
                """INSERT INTO course_change_logs(schedule_id, course_id, action_type, title, description, details)
                   VALUES(%s, %s, %s, %s, %s, %s::jsonb)""",
                (
                    course.schedule_id,
                    course_id,
                    action_type,
                    title,
                    description,
                    json.dumps(diffs, ensure_ascii=False),
                ),
            )

        return row_dict(row)


@router.delete("/{course_id}", status_code=204)
def delete_course(course_id: int, user=Depends(get_current_user)):
    """删除指定课程。"""
    with connect() as db:
        deleted = db.execute(
            """DELETE FROM courses WHERE id=%s
            AND schedule_id IN (SELECT id FROM schedules WHERE user_id=%s) RETURNING id""",
            (course_id, user["id"]),
        ).fetchone()
        if not deleted:
            raise HTTPException(404, "课程不存在")


@router.put("/{course_id}/adjustments/{week}")
def upsert_adjustment(
    course_id: int,
    week: int,
    payload: CourseAdjustmentIn,
    source: str = "drag",
    user=Depends(get_current_user),
):
    """新增或更新某门课程在指定周的临时调课安排。"""
    if week != payload.week:
        raise HTTPException(400, "路径周次与调课周次不一致")
    if payload.end_section < payload.start_section:
        raise HTTPException(400, "结束节次不能早于开始节次")
    with connect() as db:
        course = db.execute(
            """SELECT c.* FROM courses c JOIN schedules s ON s.id=c.schedule_id
               WHERE c.id=%s AND s.user_id=%s""",
            (course_id, user["id"]),
        ).fetchone()
        if not course:
            raise HTTPException(404, "课程不存在")
        if adjustment_conflicts(db, course_id, week, payload.weekday, payload.start_section, payload.end_section):
            raise HTTPException(409, "目标时段与现有课程冲突")
        row = db.execute(
            """INSERT INTO course_adjustments
               (course_id,week,weekday,start_section,end_section,room)
               VALUES(%s,%s,%s,%s,%s,%s)
               ON CONFLICT(course_id,week) DO UPDATE SET
                 weekday=EXCLUDED.weekday,start_section=EXCLUDED.start_section,
                 end_section=EXCLUDED.end_section,room=EXCLUDED.room
               RETURNING *""",
            (course_id, week, payload.weekday, payload.start_section, payload.end_section, payload.room),
        ).fetchone()

        diffs = [
            {
                "course_id": course_id,
                "course_name": course["name"],
                "week": week,
                "old_weekday": course["weekday"],
                "old_start_section": course["start_section"],
                "old_end_section": course["end_section"],
                "old_room": course["room"] or "",
                "new_weekday": payload.weekday,
                "new_start_section": payload.start_section,
                "new_end_section": payload.end_section,
                "new_room": payload.room or "",
            }
        ]
        action_type = "drag_move" if source == "drag" else "manual_edit"
        title = "位置移动（修改时间）" if source == "drag" else "临时调课"
        old_time = f"{DAYS_NAMES[course['weekday']-1]} 第{course['start_section']}-{course['end_section']}节"
        new_time = f"{DAYS_NAMES[payload.weekday-1]} 第{payload.start_section}-{payload.end_section}节"
        desc = f"第 {week} 周将《{course['name']}》从 {old_time} 调整至 {new_time}"
        if payload.room and payload.room != course["room"]:
            desc += f"（教室：{payload.room}）"

        db.execute(
            """INSERT INTO course_change_logs(schedule_id, course_id, action_type, title, description, details)
               VALUES(%s, %s, %s, %s, %s, %s::jsonb)""",
            (
                course["schedule_id"],
                course_id,
                action_type,
                title,
                desc,
                json.dumps(diffs, ensure_ascii=False),
            ),
        )

        return row_dict(row)


@router.delete("/{course_id}/adjustments/{week}", status_code=204)
def delete_adjustment(course_id: int, week: int, user=Depends(get_current_user)):
    """撤销指定周的调课，恢复课程原安排。"""
    with connect() as db:
        deleted = db.execute(
            """DELETE FROM course_adjustments a USING courses c, schedules s
               WHERE a.course_id=%s AND a.week=%s AND c.id=a.course_id
                 AND s.id=c.schedule_id AND s.user_id=%s RETURNING a.id""",
            (course_id, week, user["id"]),
        ).fetchone()
        if not deleted:
            raise HTTPException(404, "调课记录不存在")
