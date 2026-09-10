import json
import logging
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/app", tags=["App Update"])
logger = logging.getLogger("classschedule")

ROOT = Path(__file__).resolve().parent.parent.parent
VERSION_FILE = ROOT / "data" / "app_version.json"

DEFAULT_VERSION_INFO = {
    "versionCode": 1,
    "versionName": "2.0.0",
    "minVersionCode": 1,
    "title": "发现新版本",
    "changelog": [
        "性能与稳定性优化"
    ],
    "downloadUrl": "https://api.tanzeng.xyz/downloads/ClassSchedule.apk",
    "forceUpdate": False
}


class AppVersionResponse(BaseModel):
    versionCode: int
    versionName: str
    minVersionCode: int = 1
    title: str = "发现新版本"
    changelog: list[str] = Field(default_factory=list)
    downloadUrl: str
    backupDownloadUrl: str | None = None
    forceUpdate: bool = False


@router.get("/version", response_model=AppVersionResponse)
def get_app_version() -> AppVersionResponse:
    """获取移动端最新版本信息与下载链接"""
    if VERSION_FILE.is_file():
        try:
            with open(VERSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AppVersionResponse(**data)
        except (OSError, ValueError, TypeError) as error:
            logger.error("读取版本元数据失败: %s", error.__class__.__name__)
    return AppVersionResponse(**DEFAULT_VERSION_INFO)
