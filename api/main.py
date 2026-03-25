"""DocFlow FastAPI 백엔드 - 프론트엔드 직접 서빙"""

import os
import sys

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# 프로젝트 루트를 path에 추가 (기존 모듈 import용)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from api.routes import form, ai, batch, extract, periodic, stamp, merge, excel

app = FastAPI(title="DocFlow API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.get("/api/health")
def health():
    return {"status": "ok"}


# 프론트엔드 정적 파일 서빙 (Next.js export 결과)
_FRONTEND_DIR = os.path.join(_ROOT, "frontend", "out")
if os.path.isdir(_FRONTEND_DIR):
    # /_next 등 정적 자산
    app.mount("/_next", StaticFiles(directory=os.path.join(_FRONTEND_DIR, "_next")), name="next-static")

    # SPA 폴백: /api가 아닌 모든 요청 → index.html
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        # 정적 파일이 있으면 그것을 서빙
        file_path = os.path.join(_FRONTEND_DIR, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        # 없으면 index.html (SPA)
        return FileResponse(os.path.join(_FRONTEND_DIR, "index.html"))
