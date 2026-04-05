"""DocFlow FastAPI 백엔드 - 프론트엔드 직접 서빙"""

import os
import sys

# 프로젝트 루트
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# .env 로드
from dotenv import load_dotenv
load_dotenv(os.path.join(_ROOT, ".env"))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from api.routes import form, ai, batch, extract, periodic, stamp, merge, excel, auth, payment, preset, mapping, gallery, achievements, usage

app = FastAPI(title="Eazy HWPX API")


# 임시 파일 자동 정리 (30분마다)
@app.on_event("startup")
async def start_cleanup_scheduler():
    import asyncio
    from api.services.file_manager import file_manager

    async def _cleanup_loop():
        while True:
            await asyncio.sleep(1800)  # 30분
            file_manager.cleanup_expired()

    asyncio.create_task(_cleanup_loop())

_allowed_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Rate limit (AI API 분당 2회)
from api.services.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

# API 라우터
app.include_router(form.router, prefix="/api/form", tags=["form"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(batch.router, prefix="/api/batch", tags=["batch"])
app.include_router(extract.router, prefix="/api/extract", tags=["extract"])
app.include_router(periodic.router, prefix="/api/periodic", tags=["periodic"])
app.include_router(stamp.router, prefix="/api/stamp", tags=["stamp"])
app.include_router(merge.router, prefix="/api/merge", tags=["merge"])
app.include_router(excel.router, prefix="/api/excel", tags=["excel"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(payment.router, prefix="/api/payment", tags=["payment"])
app.include_router(preset.router, prefix="/api/preset", tags=["preset"])
app.include_router(mapping.router, prefix="/api/mapping", tags=["mapping"])
app.include_router(gallery.router, prefix="/api/gallery", tags=["gallery"])
app.include_router(achievements.router, prefix="/api/achievements", tags=["achievements"])
app.include_router(usage.router, prefix="/api/usage", tags=["usage"])


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/stats")
def conversion_stats():
    """변환 성공률 통계"""
    from api.services.metrics import get_stats
    return get_stats()


# 프론트엔드 정적 파일 서빙 (Next.js export 결과)
_FRONTEND_DIR = os.path.join(_ROOT, "frontend", "out")
if os.path.isdir(_FRONTEND_DIR):
    # /_next 등 정적 자산
    app.mount("/_next", StaticFiles(directory=os.path.join(_FRONTEND_DIR, "_next")), name="next-static")

    # 프론트엔드 명시적 라우트
    @app.get("/tool")
    async def serve_tool():
        html = os.path.join(_FRONTEND_DIR, "tool.html")
        return FileResponse(html if os.path.isfile(html) else os.path.join(_FRONTEND_DIR, "index.html"))

    @app.get("/pricing")
    async def serve_pricing():
        html = os.path.join(_FRONTEND_DIR, "pricing.html")
        return FileResponse(html if os.path.isfile(html) else os.path.join(_FRONTEND_DIR, "index.html"))

    @app.get("/mypage")
    async def serve_mypage():
        html = os.path.join(_FRONTEND_DIR, "mypage.html")
        return FileResponse(html if os.path.isfile(html) else os.path.join(_FRONTEND_DIR, "index.html"))

    @app.get("/auth/callback")
    async def serve_auth_callback():
        html = os.path.join(_FRONTEND_DIR, "auth", "callback.html")
        return FileResponse(html if os.path.isfile(html) else os.path.join(_FRONTEND_DIR, "index.html"))

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(_FRONTEND_DIR, "index.html"))

    # 404 폴백: API 외 경로는 SPA로
    @app.exception_handler(404)
    async def spa_fallback(request: Request, exc):
        path = request.url.path
        if path.startswith("/api/"):
            return JSONResponse({"detail": "Not found"}, status_code=404)
        # 정적 파일 확인
        file_path = os.path.join(_FRONTEND_DIR, path.lstrip("/"))
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        html_path = os.path.join(_FRONTEND_DIR, f"{path.lstrip('/')}.html")
        if os.path.isfile(html_path):
            return FileResponse(html_path)
        return FileResponse(os.path.join(_FRONTEND_DIR, "index.html"))
