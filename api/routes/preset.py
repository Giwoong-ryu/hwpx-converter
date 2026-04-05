"""프리셋 (내 정보) CRUD API"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

from api.services.supabase_client import get_supabase
from api.services import auth_service, credit_service

router = APIRouter()


class PresetCreate(BaseModel):
    name: str
    data: dict


class PresetUpdate(BaseModel):
    name: Optional[str] = None
    data: Optional[dict] = None


@router.get("/list")
async def list_presets(authorization: str = Header(None)):
    """내 프리셋 목록"""
    user = await _require_auth(authorization)
    sb = get_supabase()
    result = sb.table("docflow_presets").select(
        "id, name, data, created_at, updated_at"
    ).eq("user_id", user.id).order("updated_at", desc=True).execute()
    return {"presets": result.data or []}


@router.post("/create")
async def create_preset(req: PresetCreate, authorization: str = Header(None)):
    """프리셋 생성 (플랜별 개수 제한)"""
    user = await _require_auth(authorization)
    sb = get_supabase()

    # 개수 제한 체크
    status = await credit_service.get_user_status(user.id)
    limit = status.get("preset_limit", 1) if status else 1
    existing = sb.table("docflow_presets").select(
        "id", count="exact"
    ).eq("user_id", user.id).execute()
    count = existing.count if existing.count is not None else len(existing.data or [])

    if count >= limit:
        plan = status.get("plan", "free") if status else "free"
        if plan == "free":
            msg = "무료 플랜은 프리셋 1개까지 저장 가능합니다. Plus로 업그레이드하면 3개까지 사용할 수 있습니다."
        elif plan == "plus":
            msg = "Plus 플랜은 프리셋 3개까지 저장 가능합니다. Pro로 업그레이드하면 무제한 사용할 수 있습니다."
        else:
            msg = "프리셋 저장 한도에 도달했습니다."
        raise HTTPException(status_code=429, detail={
            "detail": msg,
            "error_code": "PRESET_LIMIT",
            "plan": plan,
            "current": count,
            "limit": limit,
        })

    result = sb.table("docflow_presets").insert({
        "user_id": user.id,
        "name": req.name,
        "data": req.data,
    }).execute()

    return {"preset": result.data[0] if result.data else None}


@router.put("/{preset_id}")
async def update_preset(preset_id: int, req: PresetUpdate, authorization: str = Header(None)):
    """프리셋 수정"""
    user = await _require_auth(authorization)
    sb = get_supabase()

    # 소유권 확인
    existing = sb.table("docflow_presets").select("id").eq(
        "id", preset_id
    ).eq("user_id", user.id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="프리셋을 찾을 수 없습니다.")

    update = {}
    if req.name is not None:
        update["name"] = req.name
    if req.data is not None:
        update["data"] = req.data
    if not update:
        raise HTTPException(status_code=400, detail="수정할 내용이 없습니다.")

    result = sb.table("docflow_presets").update(update).eq(
        "id", preset_id
    ).eq("user_id", user.id).execute()

    return {"preset": result.data[0] if result.data else None}


@router.delete("/{preset_id}")
async def delete_preset(preset_id: int, authorization: str = Header(None)):
    """프리셋 삭제"""
    user = await _require_auth(authorization)
    sb = get_supabase()

    existing = sb.table("docflow_presets").select("id").eq(
        "id", preset_id
    ).eq("user_id", user.id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="프리셋을 찾을 수 없습니다.")

    sb.table("docflow_presets").delete().eq(
        "id", preset_id
    ).eq("user_id", user.id).execute()

    return {"deleted": True}


async def _require_auth(authorization: str):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    token = authorization.split(" ", 1)[1]
    user = await auth_service.get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    return user
