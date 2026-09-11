from pydantic import BaseModel, Field, field_validator


def normalize_email(value: str) -> str:
    """邮箱清洗与格式基本校验。"""
    value = (value or "").strip().lower()
    if "@" not in value or "." not in value.split("@")[-1]:
        raise ValueError("邮箱格式不正确")
    return value


class RegisterIn(BaseModel):
    email: str = Field(max_length=254)
    username: str = Field(min_length=2, max_length=40)
    password: str = Field(min_length=6, max_length=72)

    @field_validator("email")
    @classmethod
    def check_email(cls, value):
        return normalize_email(value)


class LoginIn(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=6, max_length=72)

    @field_validator("email")
    @classmethod
    def check_email(cls, value):
        return normalize_email(value)


class CourseIn(BaseModel):
    schedule_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=80)
    teacher: str = Field(default="", max_length=40)
    room: str = Field(default="", max_length=40)
    weekday: int = Field(ge=1, le=7)
    start_section: int = Field(ge=1, le=12)
    end_section: int = Field(ge=1, le=12)
    weeks: list[int] = Field(default_factory=list)
    color: str = Field(default="#5B8DEF", pattern=r"^#[0-9A-Fa-f]{6}$")

    @field_validator("name", "teacher", "room")
    @classmethod
    def clean_text(cls, value, info):
        value = value.strip()
        if info.field_name == "name" and not value:
            raise ValueError("课程名称不能为空")
        return value

    @field_validator("weeks")
    @classmethod
    def valid_weeks(cls, value):
        if any(week < 1 or week > 30 for week in value):
            raise ValueError("周次必须在 1 到 30 之间")
        return sorted(set(value))


class CourseAdjustmentIn(BaseModel):
    week: int = Field(ge=1, le=30)
    weekday: int = Field(ge=1, le=7)
    start_section: int = Field(ge=1, le=12)
    end_section: int = Field(ge=1, le=12)
    room: str = Field(default="", max_length=40)

    @field_validator("room")
    @classmethod
    def clean_room(cls, value):
        return value.strip()
