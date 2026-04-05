"""업적 조회 API"""

from fastapi import APIRouter, HTTPException, Header

from api.services.supabase_client import get_supabase
from api.services import auth_service

router = APIRouter()

# 업적 정의 (credit_service.py와 동기화)
ACHIEVEMENT_DEFS = {
    "first_doc": {"label": "첫 문서 완성", "reward": 25, "condition": "문서 1건 완성"},
    "docs_5": {"label": "문서 5건 달성", "reward": 50, "condition": "문서 5건 완성"},
    "docs_10": {"label": "문서 10건 달성", "reward": 50, "condition": "문서 10건 완성"},
    "streak_3": {"label": "3일 연속 사용", "reward": 10, "condition": "3일 연속 사용"},
    "streak_7": {"label": "7일 연속 사용", "reward": 25, "condition": "7일 연속 사용"},
    "streak_14": {"label": "14일 연속 사용", "reward": 25, "condition": "14일 연속 사용"},
    "streak_30": {"label": "30일 연속 사용", "reward": 50, "condition": "30일 연속 사용"},
    "level_2": {"label": "Lv.2 문서러 달성", "reward": 25, "condition": "문서 5건 완성"},
    "level_3": {"label": "Lv.3 자동화 전문가 달성", "reward": 50, "condition": "문서 20건 완성"},
    "level_4": {"label": "Lv.4 문서 마스터 달성", "reward": 50, "condition": "문서 50건 완성"},
    "level_5": {"label": "Lv.5 DocFlow 달인 달성", "reward": 50, "condition": "문서 100건 완성"},
}


@router.get("/list")
async def list_achievements(authorization: str = Header(None)):
    """달성한 업적 목록 + 전체 업적 정의"""
    user = await _require_auth(authorization)
    sb = get_supabase()

    result = sb.table("docflow_achievements").select(
        "achievement_key, gauge_reward, created_at"
    ).eq("user_id", user.id).order("created_at", desc=True).execute()

    return {
        "achievements": result.data or [],
        "definitions": ACHIEVEMENT_DEFS,
    }


async def _require_auth(authorization: str):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    token = authorization.split(" ", 1)[1]
    user = await auth_service.get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    return user
