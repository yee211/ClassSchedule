from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .db import close_pool, connect, init_pool
from .observability import configure_logging, request_metrics_middleware
from .settings import settings
from .routers import app_update, auth, courses, importer, schedules

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIST = ROOT / "frontend" / "dist"
DOWNLOADS_DIR = ROOT / "static" / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.validate()
    configure_logging()
    init_pool()
    yield
    close_pool()


app = FastAPI(title="序时", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.middleware("http")(request_metrics_middleware)

# 挂载静态下载目录（供移动端 APK 直接下载更新）
app.mount("/downloads", StaticFiles(directory=DOWNLOADS_DIR), name="downloads")

# 注册业务子路由模块
app.include_router(auth.router)
app.include_router(schedules.router)
app.include_router(courses.router)
app.include_router(importer.router)
app.include_router(app_update.router)


@app.get("/api/health")
def health():
    """就绪探针：同时检查数据库连接。"""
    with connect() as db:
        db.execute("SELECT 1")
    return {"ok": True}


@app.get("/api/live")
def live():
    """存活探针：仅确认应用进程能够响应。"""
    return {"ok": True}


# 托管前端单页应用静态资源
if FRONTEND_DIST.exists():
    if (FRONTEND_DIST / "assets").exists():
        app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    def frontend(path: str):
        candidate = FRONTEND_DIST / path
        return FileResponse(candidate if candidate.is_file() else FRONTEND_DIST / "index.html")
