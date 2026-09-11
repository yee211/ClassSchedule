import pytest
from pydantic import ValidationError

from app.schemas import CourseAdjustmentIn


def test_course_adjustment_schema():
    payload = CourseAdjustmentIn(
        week=6,
        weekday=4,
        start_section=3,
        end_section=4,
        room="南 312",
    )
    assert payload.week == 6
    assert payload.weekday == 4
    assert payload.room == "南 312"


@pytest.mark.parametrize(
    ("field", "value"),
    [("week", 31), ("weekday", 0), ("start_section", 13), ("end_section", 0)],
)
def test_course_adjustment_rejects_out_of_range(field, value):
    data = {"week": 6, "weekday": 4, "start_section": 3, "end_section": 4}
    data[field] = value
    with pytest.raises(ValidationError):
        CourseAdjustmentIn(**data)
