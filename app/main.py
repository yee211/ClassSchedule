from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .db import close_pool, connect, init_db, init_pool
from .routers import auth, courses, importer, schedules

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIST = ROOT / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_pool()
    init_db()
    yield
    close_pool()


app = FastAPI(title="简课", version="2.0.0", lifespan=lifespan)

# 注册业务子路由模块
app.include_router(auth.router)
app.include_router(schedules.router)
app.include_router(courses.router)
app.include_router(importer.router)


@app.get("/api/health")
def health():
    """基础存活探针。"""
    with connect() as db:
        db.execute("SELECT 1")
    return {"ok": True}


# 托管前端单页应用静态资源
if FRONTEND_DIST.exists():
    if (FRONTEND_DIST / "assets").exists():
        app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    def frontend(path: str):
        candidate = FRONTEND_DIST / path
        return FileResponse(candidate if candidate.is_file() else FRONTEND_DIST / "index.html")
