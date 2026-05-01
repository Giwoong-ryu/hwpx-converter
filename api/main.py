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

from api.routes import form, ai, batch, extract, periodic, stamp, merge, excel, auth, payment, preset, mapping, gallery, achievements, usage, coupon, admin

app = FastAPI(title="Eazy HWPX API")


# 미처리 예외도 CORS 미들웨어를 통과하도록 전역 핸들러 등록
# (ServerErrorMiddleware가 CORS 바깥에서 잡기 전에 ExceptionMiddleware가 먼저 처리)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


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


# 서버 시작 시 잔류 Gemini 캐시 정리 (비정상 종료 시 남은 캐시 방지)
@app.on_event("startup")
async def cleanup_stale_gemini_caches():
    try:
        from ai_mapper import _get_api_key
        from google import genai
        api_key = _get_api_key()
        if api_key:
            client = genai.Client(api_key=api_key)
            for c in client.caches.list():
                try:
                    client.caches.delete(name=c.name)
                    print(f"[startup] 잔류 캐시 삭제: {c.name}")
                except Exception:
                    pass
    except Exception:
        pass  # 캐시 정리 실패해도 서버 시작은 정상 진행


# 미들웨어 등록 순서 주의:
# Starlette는 "나중에 add_middleware한 것이 바깥 레이어"가 됨.
# 따라서 CORSMiddleware는 가장 마지막에 add 해야 모든 응답(거부/예외 포함)에 CORS 헤더가 붙음.

# Rate limit (AI API 분당 2회) - CORS 안쪽에 위치
from api.services.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

_cors_env = os.environ.get("CORS_ORIGINS", "")
# "*"는 credentials와 함께 쓸 수 없으므로 필터링. regex로 처리.
_allowed_origins = [o.strip() for o in _cors_env.split(",") if o.strip() and o.strip() != "*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_origin_regex=r"https://(.*\.)?eazyhwpx\.kr",
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

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
app.include_router(coupon.router, prefix="/api/coupon", tags=["coupon"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


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
