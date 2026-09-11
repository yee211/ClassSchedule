"""Parse course-adjustment notice images with an OpenAI-compatible vision model."""
import base64
import json
import logging
import os
import re
from pathlib import Path

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

logger = logging.getLogger("classschedule")
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
VISION_BASE_URL = os.getenv("VISION_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1").rstrip("/")
VISION_API_KEY = os.getenv("VISION_API_KEY", "").strip().strip('"').strip("'")
VISION_MODEL = os.getenv("VISION_MODEL", "qwen3.7-flash")
VISION_TIMEOUT = min(60.0, max(5.0, float(os.getenv("VISION_TIMEOUT_SECONDS", "20"))))
VISION_MAX_OUTPUT_TOKENS = min(8000, max(500, int(os.getenv("VISION_MAX_OUTPUT_TOKENS", "2000"))))
VISION_ENABLE_THINKING = os.getenv("VISION_ENABLE_THINKING", "false").lower() == "true"

PROMPT = """你是高校调课通知结构化提取器。阅读用户提供的图片或自然语言，将每一条“调整前”与对应的“调整后”配对。
只输出 JSON，不要解释，不要 Markdown。格式：
{"adjustments":[{"course_name":"课程全名","teacher":"教师","week":2,
"old_weekday":1,"old_start_section":1,"old_end_section":2,"old_room":"北201",
"new_weekday":1,"new_start_section":1,"new_end_section":2,"new_room":"南204"}]}
规则：weekday 取 1至7，星期一为1；节次和周次必须是整数；一条调整前记录对应一条调整后记录；
通知中同一课程涉及多个周次或时段时逐条展开；保持教室原文；无法可靠配对的条目不要猜测。"""


class VisionAdjustment(BaseModel):
    course_name: str = Field(min_length=1, max_length=120)
    teacher: str = Field(default="", max_length=40)
    week: int = Field(ge=1, le=30)
    old_weekday: int = Field(ge=1, le=7)
    old_start_section: int = Field(ge=1, le=12)
    old_end_section: int = Field(ge=1, le=12)
    old_room: str = Field(default="", max_length=40)
    new_weekday: int = Field(ge=1, le=7)
    new_start_section: int = Field(ge=1, le=12)
    new_end_section: int = Field(ge=1, le=12)
    new_room: str = Field(default="", max_length=40)

    @field_validator("course_name", "teacher", "old_room", "new_room")
    @classmethod
    def clean_text(cls, value):
        return re.sub(r"\s+", " ", str(value or "")).strip()

    @model_validator(mode="after")
    def validate_sections(self):
        if self.old_end_section < self.old_start_section or self.new_end_section < self.new_start_section:
            raise ValueError("节次范围倒序")
        return self


def _extract_json(text: str) -> str:
    text = (text or "").strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    return text[start:end + 1] if start != -1 and end > start else text


def _request_adjustments(user_content) -> list[dict]:
    if not VISION_API_KEY:
        raise RuntimeError("视觉模型尚未配置 VISION_API_KEY")
    try:
        response = httpx.post(
            f"{VISION_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {VISION_API_KEY}"},
            timeout=VISION_TIMEOUT,
            json={
                "model": VISION_MODEL,
                "temperature": 0,
                "max_tokens": VISION_MAX_OUTPUT_TOKENS,
                "enable_thinking": VISION_ENABLE_THINKING,
                "response_format": {"type": "json_object"},
                "messages": [{"role": "user", "content": user_content}],
            },
        )
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"]
        payload = json.loads(_extract_json(raw))
    except httpx.TimeoutException as error:
        raise RuntimeError("视觉模型响应超时，请重试") from error
    except httpx.HTTPStatusError as error:
        logger.warning("视觉模型 HTTP 错误: %s", error.response.status_code)
        raise RuntimeError(f"视觉模型调用失败（HTTP {error.response.status_code}）") from error
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as error:
        logger.warning("视觉模型响应无效: %s", error.__class__.__name__)
        raise RuntimeError("视觉模型返回了无法解析的数据") from error
    rows = []
    for item in payload.get("adjustments", []) if isinstance(payload, dict) else []:
        try:
            rows.append(VisionAdjustment.model_validate(item).model_dump())
        except ValidationError:
            continue
    if not rows:
        raise RuntimeError("没有从通知中识别到有效调课记录")
    return rows


def parse_adjustment_image(content: bytes, mime_type: str) -> list[dict]:
    image_url = f"data:{mime_type};base64,{base64.b64encode(content).decode('ascii')}"
    return _request_adjustments([
        {"type": "text", "text": PROMPT},
        {"type": "image_url", "image_url": {"url": image_url}},
    ])


def parse_adjustment_text(description: str) -> list[dict]:
    return _request_adjustments(f"{PROMPT}\n\n用户的调课描述：\n{description}")
