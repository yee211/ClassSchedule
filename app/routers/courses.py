import json
from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..db import connect, row_dict
from ..schemas import CourseIn

router = APIRouter(prefix="/api/courses", tags=["courses"])


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


@router.put("/{course_id}")
def update_course(course_id: int, course: CourseIn, user=Depends(get_current_user)):
    """更新指定课程信息。"""
    if course.end_section < course.start_section:
        raise HTTPException(400, "结束节次不能早于开始节次")
    with connect() as db:
        if not db.execute(
            "SELECT 1 FROM schedules WHERE id=%s AND user_id=%s",
            (course.schedule_id, user["id"]),
        ).fetchone():
            raise HTTPException(404, "课表不存在")
        row = db.execute(
            """UPDATE courses SET schedule_id=%s,name=%s,teacher=%s,room=%s,
            weekday=%s,start_section=%s,end_section=%s,weeks=%s::jsonb,color=%s
            WHERE id=%s AND schedule_id IN (SELECT id FROM schedules WHERE user_id=%s) RETURNING *""",
            (*course_row_values(course), course_id, user["id"]),
        ).fetchone()
        if not row:
            raise HTTPException(404, "课程不存在")
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
