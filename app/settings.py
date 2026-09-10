import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

INSECURE_SECRETS = {"", "dev-insecure-secret-change-me", "please-change-this-to-a-long-random-string"}


@dataclass(frozen=True)
class Settings:
    environment: str = os.getenv("APP_ENV", "development").strip().lower()
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-insecure-secret-change-me")
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
    auth_rate_limit: int = int(os.getenv("AUTH_RATE_LIMIT", "10"))
    auth_rate_window_seconds: int = int(os.getenv("AUTH_RATE_WINDOW_SECONDS", "300"))
    trust_proxy_headers: bool = os.getenv("TRUST_PROXY_HEADERS", "false").lower() == "true"
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "https://localhost,http://localhost,capacitor://localhost").split(",")
        if origin.strip()
    )

    def validate(self) -> None:
        if self.environment not in {"development", "test", "production"}:
            raise RuntimeError("APP_ENV 只能是 development、test 或 production")
        if self.max_upload_bytes < 1024 or self.max_upload_bytes > 50 * 1024 * 1024:
            raise RuntimeError("MAX_UPLOAD_BYTES 必须在 1KB 到 50MB 之间")
        if self.environment == "production":
            if self.jwt_secret in INSECURE_SECRETS or len(self.jwt_secret) < 32:
                raise RuntimeError("生产环境必须配置至少 32 字符的随机 JWT_SECRET")
            if os.getenv("DEFAULT_PASSWORD", "demo1234") == "demo1234":
                raise RuntimeError("生产环境禁止使用默认演示账号密码")


settings = Settings()
