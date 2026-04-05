"""사용 이력 API (gauge_cost 절대 미포함)"""

from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Header, Query

from api.services.supabase_client import get_supabase
from api.services import auth_service

router = APIRouter()


@router.get("/history")
async def usage_history(
    days: int = Query(30, ge=1, le=90),
    authorization: str = Header(None),
):
    """최근 N일간 사용 이력 (행동 + 날짜만, 차감량 미포함)"""
    user = await _require_auth(authorization)
    sb = get_supabase()

    since = (date.today() - timedelta(days=days)).isoformat()
    result = sb.table("docflow_usage_log").select(
        "action, created_at"
    ).eq("user_id", user.id).gte(
        "created_at", f"{since}T00:00:00"
    ).order("created_at", desc=True).execute()

    rows = result.data or []

    doc_completions = sum(1 for r in rows if r["action"] == "doc_complete")
    mappings_used = sum(1 for r in rows if r["action"] == "mapping")
    generations = sum(1 for r in rows if r["action"] == "generation")

    return {
        "history": rows,
        "summary": {
            "total_actions": len(rows),
            "doc_completions": doc_completions,
            "mappings_used": mappings_used,
            "generations": generations,
            "period_days": days,
        },
    }


async def _require_auth(authorization: str):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    token = authorization.split(" ", 1)[1]
    user = await auth_service.get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    return user
