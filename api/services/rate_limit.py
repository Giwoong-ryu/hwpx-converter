"""Rate limit - AI API 분당 2회 제한 (메모리 기반)"""

import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# AI API 경로 (rate limit 적용 대상)
_AI_PATHS = {"/api/ai/map", "/api/batch/map-headers"}

# 분당 최대 요청 수
_MAX_PER_MINUTE = 2

# 키별 요청 타임스탬프
_requests: dict[str, deque] = defaultdict(lambda: deque(maxlen=100))


def _get_key(request: Request) -> str:
    """사용자 식별 키: Authorization 토큰 또는 IP"""
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        return f"token:{auth[7:20]}"  # 토큰 앞 13자로 구분
    fp = request.headers.get("x-fingerprint", "")
    if fp:
        return f"fp:{fp}"
    ip = request.client.host if request.client else "unknown"
    return f"ip:{ip}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method != "POST" or request.url.path not in _AI_PATHS:
            return await call_next(request)

        key = _get_key(request)
        now = time.time()
        window = now - 60  # 1분 윈도우

        # 오래된 기록 제거
        timestamps = _requests[key]
        while timestamps and timestamps[0] < window:
            timestamps.popleft()

        if len(timestamps) >= _MAX_PER_MINUTE:
            # BaseHTTPMiddleware 안에서 raise HTTPException은 ExceptionHandler가 잡지 못해
            # CORS 헤더가 빠진 채 500으로 빠질 수 있음. JSONResponse를 직접 반환해야
            # 바깥의 CORSMiddleware가 정상적으로 헤더를 부착할 수 있다.
            return JSONResponse(
                status_code=429,
                content={"detail": "요청이 너무 빠릅니다. 30초 후 다시 시도해주세요."},
            )

        timestamps.append(now)

        # 주기적으로 빈 키 정리 (1000개 초과 시)
        if len(_requests) > 1000:
            # list()로 복사하여 iteration 중 변경 방지
            empty_keys = [k for k, v in list(_requests.items()) if not v or v[-1] < window]
            for k in empty_keys:
                _requests.pop(k, None)

        return await call_next(request)
