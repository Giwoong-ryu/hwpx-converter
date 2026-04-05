"""매핑 저장/불러오기/공개/좋아요 API"""

from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel
from typing import Optional

from api.services.supabase_client import get_supabase
from api.services import auth_service, credit_service

router = APIRouter()


class MappingSave(BaseModel):
    form_name: str
    mappings: dict
    form_field_count: int = 0


class MappingUpdate(BaseModel):
    form_name: Optional[str] = None
    mappings: Optional[dict] = None
    is_public: Optional[bool] = None


# ═══ 내 매핑 ═══

@router.get("/list")
async def list_my_mappings(authorization: str = Header(None)):
    """내 저장된 매핑 목록"""
    user = await _require_auth(authorization)
    sb = get_supabase()
    result = sb.table("docflow_saved_mappings").select(
        "id, form_name, form_field_count, is_public, likes, created_at, updated_at"
    ).eq("user_id", user.id).order("updated_at", desc=True).execute()
    return {"mappings": result.data or []}


@router.post("/save")
async def save_mapping(req: MappingSave, authorization: str = Header(None)):
    """매핑 저장 (플랜별 개수 제한)"""
    user = await _require_auth(authorization)
    sb = get_supabase()

    # 개수 제한 체크
    status = await credit_service.get_user_status(user.id)
    limit = status.get("mapping_save_limit", 0) if status else 0
    existing = sb.table("docflow_saved_mappings").select(
        "id", count="exact"
    ).eq("user_id", user.id).execute()
    count = existing.count if existing.count is not None else len(existing.data or [])

    if count >= limit:
        plan = status.get("plan", "free") if status else "free"
        if plan == "free":
            msg = "무료 플랜은 매핑 저장이 불가합니다. Plus로 업그레이드하면 10개까지 저장할 수 있습니다."
        elif plan == "plus":
            msg = "Plus 플랜은 매핑 10개까지 저장 가능합니다. Pro로 업그레이드하면 무제한 사용할 수 있습니다."
        else:
            msg = "매핑 저장 한도에 도달했습니다."
        raise HTTPException(status_code=429, detail={
            "detail": msg,
            "error_code": "MAPPING_LIMIT",
            "plan": plan,
            "current": count,
            "limit": limit,
        })

    result = sb.table("docflow_saved_mappings").insert({
        "user_id": user.id,
        "form_name": req.form_name,
        "form_field_count": req.form_field_count,
        "mappings": req.mappings,
    }).execute()

    return {"mapping": result.data[0] if result.data else None}


@router.get("/{mapping_id}")
async def get_mapping(mapping_id: int, authorization: str = Header(None)):
    """매핑 상세 조회 (본인 것 또는 공개된 것)"""
    user = await _require_auth(authorization)
    sb = get_supabase()

    result = sb.table("docflow_saved_mappings").select("*").eq("id", mapping_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="매핑을 찾을 수 없습니다.")

    m = result.data[0]
    if m["user_id"] != user.id and not m.get("is_public"):
        raise HTTPException(status_code=404, detail="매핑을 찾을 수 없습니다.")

    return {"mapping": m}


@router.put("/{mapping_id}")
async def update_mapping(mapping_id: int, req: MappingUpdate, authorization: str = Header(None)):
    """매핑 수정 (공개 전환 포함)"""
    user = await _require_auth(authorization)
    sb = get_supabase()

    existing = sb.table("docflow_saved_mappings").select(
        "id, is_public"
    ).eq("id", mapping_id).eq("user_id", user.id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="매핑을 찾을 수 없습니다.")

    update = {}
    if req.form_name is not None:
        update["form_name"] = req.form_name
    if req.mappings is not None:
        update["mappings"] = req.mappings

    # 공개 전환 시 보상 처리 (매핑당 1회만)
    rewards = []
    was_public = existing.data[0].get("is_public", False)
    if req.is_public is not None:
        update["is_public"] = req.is_public
        if req.is_public and not was_public:
            share_key = f"share_mapping_{mapping_id}"
            already = sb.table("docflow_achievements").select("id").eq(
                "user_id", user.id
            ).eq("achievement_key", share_key).execute()
            if not already.data:
                reward = await credit_service.on_mapping_shared(user.id)
                from api.services.credit_service import _grant_achievement
                _grant_achievement(user.id, share_key, 25.0)
                if reward:
                    rewards.append(reward)

    if not update:
        raise HTTPException(status_code=400, detail="수정할 내용이 없습니다.")

    result = sb.table("docflow_saved_mappings").update(update).eq(
        "id", mapping_id
    ).eq("user_id", user.id).execute()

    resp = {"mapping": result.data[0] if result.data else None}
    if rewards:
        resp["rewards"] = rewards
    return resp


@router.delete("/{mapping_id}")
async def delete_mapping(mapping_id: int, authorization: str = Header(None)):
    """매핑 삭제"""
    user = await _require_auth(authorization)
    sb = get_supabase()

    existing = sb.table("docflow_saved_mappings").select("id").eq(
        "id", mapping_id
    ).eq("user_id", user.id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="매핑을 찾을 수 없습니다.")

    sb.table("docflow_saved_mappings").delete().eq(
        "id", mapping_id
    ).eq("user_id", user.id).execute()

    return {"deleted": True}


# ═══ 공개 매핑 탐색 ═══

@router.get("/public/list")
async def list_public_mappings(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
):
    """공개 매핑 목록 (인기순)"""
    sb = get_supabase()
    offset = (page - 1) * size
    result = sb.table("docflow_saved_mappings").select(
        "id, form_name, form_field_count, likes, created_at, user_id"
    ).eq("is_public", True).order(
        "likes", desc=True
    ).range(offset, offset + size - 1).execute()

    return {"mappings": result.data or [], "page": page, "size": size}


# ═══ 좋아요 ═══

@router.post("/{mapping_id}/like")
async def toggle_like(mapping_id: int, authorization: str = Header(None)):
    """좋아요 토글 (누르면 추가, 다시 누르면 제거)"""
    user = await _require_auth(authorization)
    sb = get_supabase()

    # 매핑 존재 + 공개 확인
    mapping = sb.table("docflow_saved_mappings").select(
        "id, is_public, likes"
    ).eq("id", mapping_id).execute()
    if not mapping.data:
        raise HTTPException(status_code=404, detail="매핑을 찾을 수 없습니다.")
    if not mapping.data[0].get("is_public"):
        raise HTTPException(status_code=400, detail="비공개 매핑에는 좋아요할 수 없습니다.")

    # 이미 좋아요했는지
    existing = sb.table("docflow_likes").select("id").eq(
        "user_id", user.id
    ).eq("mapping_id", mapping_id).execute()

    current_likes = mapping.data[0].get("likes", 0)

    if existing.data:
        # 좋아요 취소
        sb.table("docflow_likes").delete().eq(
            "user_id", user.id
        ).eq("mapping_id", mapping_id).execute()
        new_likes = max(current_likes - 1, 0)
        sb.table("docflow_saved_mappings").update(
            {"likes": new_likes}
        ).eq("id", mapping_id).execute()
        return {"liked": False, "likes": new_likes}
    else:
        # 좋아요 추가
        sb.table("docflow_likes").insert({
            "user_id": user.id,
            "mapping_id": mapping_id,
        }).execute()
        new_likes = current_likes + 1
        sb.table("docflow_saved_mappings").update(
            {"likes": new_likes}
        ).eq("id", mapping_id).execute()
        return {"liked": True, "likes": new_likes}


async def _require_auth(authorization: str):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    token = authorization.split(" ", 1)[1]
    user = await auth_service.get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    return user
