"""오너 전용 API"""

import os
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from api.services.supabase_client import get_supabase
from api.services import auth_service

router = APIRouter()

OWNER_EMAILS = os.getenv("OWNER_EMAILS", "eazypick.dev@gmail.com").split(",")

PLAN_DEFAULTS = {
    "free": {"plan": "free", "gauge_percent": 0, "preset_limit": 1, "mapping_save_limit": 0, "streak_freeze_count": 0},
    "plus": {"plan": "plus", "gauge_percent": 100, "preset_limit": 3, "mapping_save_limit": 10, "streak_freeze_count": 1},
    "pro": {"plan": "pro", "gauge_percent": 100, "preset_limit": 9999, "mapping_save_limit": 9999, "streak_freeze_count": 2},
}


class SwitchPlanRequest(BaseModel):
    plan: str  # free, plus, pro


@router.post("/switch-plan")
async def switch_plan(req: SwitchPlanRequest, authorization: str = Header(None)):
    """오너 전용: 플랜 즉시 전환"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    token = authorization.split(" ", 1)[1]
    user = await auth_service.get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    # 오너 체크
    if user.email not in OWNER_EMAILS:
        raise HTTPException(status_code=403, detail="권한이 없습니다.")

    if req.plan not in PLAN_DEFAULTS:
        raise HTTPException(status_code=400, detail="유효하지 않은 플랜입니다.")

    sb = get_supabase()
    update_data = PLAN_DEFAULTS[req.plan].copy()

    sb.table("docflow_users").update(update_data).eq("id", user.id).execute()

    return {"ok": True, "plan": req.plan, "message": f"{req.plan.upper()} 플랜으로 전환되었습니다."}
