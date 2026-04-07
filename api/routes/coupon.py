"""쿠폰 API - 코드 입력으로 게이지 충전"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from api.services.supabase_client import get_supabase
from api.services import auth_service

router = APIRouter()

# 쿠폰별 표시 이름 (코드 → 라벨)
COUPON_LABELS: dict[str, str] = {
    "HELLO": "지인 전용 Plus 혜택",
    "OPEN2026": "오픈 기념 Plus 체험",
}


def _coupon_label(code: str, coupon_type: str, value: float) -> str:
    if code in COUPON_LABELS:
        return COUPON_LABELS[code]
    if coupon_type == "plus_free":
        return "Plus 무료 체험"
    return f"게이지 +{value}%"


class RedeemRequest(BaseModel):
    code: str


@router.post("/check")
async def check_coupon(req: RedeemRequest, authorization: str = Header(None)):
    """쿠폰 코드 유효성 확인 (적용하지 않고 정보만 반환)"""
    user = await _get_user(authorization)
    sb = get_supabase()
    code = req.code.strip().upper()

    if not code:
        raise HTTPException(status_code=400, detail="쿠폰 코드를 입력해주세요.")

    result = sb.table("docflow_coupons").select("*").eq("code", code).eq("is_active", True).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="유효하지 않은 쿠폰 코드입니다.")

    coupon = result.data[0]

    if coupon.get("expires_at"):
        expires = datetime.fromisoformat(coupon["expires_at"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expires:
            raise HTTPException(status_code=410, detail="만료된 쿠폰입니다.")

    if coupon.get("max_uses") is not None:
        if coupon.get("used_count", 0) >= coupon["max_uses"]:
            raise HTTPException(status_code=410, detail="모두 소진된 쿠폰입니다.")

    used = sb.table("docflow_coupon_uses").select("id").eq("coupon_id", coupon["id"]).eq("user_id", user.id).execute()
    if used.data:
        raise HTTPException(status_code=409, detail="이미 사용한 쿠폰입니다.")

    coupon_label = _coupon_label(code, coupon["type"], float(coupon["value"]))
    expires_str = coupon["expires_at"][:10] if coupon.get("expires_at") else "무기한"

    return {
        "ok": True,
        "code": code,
        "label": coupon_label,
        "value": coupon["value"],
        "type": coupon["type"],
        "expires": expires_str,
        "remaining": (coupon["max_uses"] - coupon.get("used_count", 0)) if coupon.get("max_uses") else None,
    }


@router.post("/redeem")
async def redeem_coupon(req: RedeemRequest, authorization: str = Header(None)):
    """쿠폰 코드 적용 -> 게이지 충전"""
    user = await _get_user(authorization)
    sb = get_supabase()
    code = req.code.strip().upper()

    if not code:
        raise HTTPException(status_code=400, detail="쿠폰 코드를 입력해주세요.")

    # 1. 쿠폰 조회
    result = sb.table("docflow_coupons").select("*").eq("code", code).eq("is_active", True).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="유효하지 않은 쿠폰 코드입니다.")

    coupon = result.data[0]

    # 2. 만료일 체크
    if coupon.get("expires_at"):
        expires = datetime.fromisoformat(coupon["expires_at"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expires:
            raise HTTPException(status_code=410, detail="만료된 쿠폰입니다.")

    # 3. 사용 횟수 체크
    if coupon.get("max_uses") is not None:
        if coupon.get("used_count", 0) >= coupon["max_uses"]:
            raise HTTPException(status_code=410, detail="모두 소진된 쿠폰입니다.")

    # 4. 이미 사용했는지 체크 (1인 1회)
    used = sb.table("docflow_coupon_uses").select("id").eq(
        "coupon_id", coupon["id"]
    ).eq("user_id", user.id).execute()

    if used.data:
        raise HTTPException(status_code=409, detail="이미 사용한 쿠폰입니다.")

    # 5. 타입별 처리
    gauge_added = float(coupon["value"])
    coupon_type = coupon["type"]

    if coupon_type in ("plus_free", "gauge_bonus"):
        # 게이지 충전
        user_row = sb.table("docflow_users").select(
            "gauge_percent, plan"
        ).eq("id", user.id).single().execute()

        if not user_row.data:
            raise HTTPException(status_code=404, detail="사용자 정보를 찾을 수 없습니다.")

        current_gauge = float(user_row.data.get("gauge_percent", 0))
        new_gauge = round(current_gauge + gauge_added, 1)

        update_data = {"gauge_percent": new_gauge}
        # plus_free 쿠폰이면 플랜도 plus로 업그레이드
        if coupon_type == "plus_free" and user_row.data.get("plan") == "free":
            update_data["plan"] = "plus"
            update_data["preset_limit"] = 3
            update_data["mapping_save_limit"] = 10
            update_data["streak_freeze_count"] = 1

        sb.table("docflow_users").update(update_data).eq("id", user.id).execute()
    else:
        raise HTTPException(status_code=400, detail="지원하지 않는 쿠폰 타입입니다.")

    # 6. 사용 기록 저장
    try:
        sb.table("docflow_coupon_uses").insert({
            "coupon_id": coupon["id"],
            "user_id": user.id,
        }).execute()
    except Exception:
        # UNIQUE 제약 위반 (동시 요청 방어)
        raise HTTPException(status_code=409, detail="이미 사용한 쿠폰입니다.")

    # 7. used_count +1
    sb.table("docflow_coupons").update({
        "used_count": coupon.get("used_count", 0) + 1,
    }).eq("id", coupon["id"]).execute()

    # 8. 응답
    message = _get_success_message(coupon_type, gauge_added)
    return {"ok": True, "message": message, "gauge_added": gauge_added}


@router.get("/my-coupon")
async def my_coupon(authorization: str = Header(None)):
    """현재 사용자의 활성 쿠폰 정보 조회"""
    user = await _get_user(authorization)
    sb = get_supabase()

    # 사용자가 사용한 쿠폰 조회
    uses = sb.table("docflow_coupon_uses").select(
        "coupon_id, used_at"
    ).eq("user_id", user.id).order("used_at", desc=True).limit(1).execute()

    if not uses.data:
        return {"active": False}

    coupon_id = uses.data[0]["coupon_id"]
    coupon = sb.table("docflow_coupons").select(
        "code, type, value, expires_at"
    ).eq("id", coupon_id).single().execute()

    if not coupon.data:
        return {"active": False}

    c = coupon.data
    # 만료 체크
    if c.get("expires_at"):
        expires = datetime.fromisoformat(c["expires_at"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expires:
            return {"active": False}

    coupon_name = "Plus 체험중" if c["type"] == "plus_free" else f"보너스 +{c['value']}%"
    return {"active": True, "coupon_name": coupon_name, "code": c["code"]}


def _get_success_message(coupon_type: str, value: float) -> str:
    """쿠폰 타입별 성공 메시지"""
    if coupon_type == "plus_free":
        return f"Plus 무료 체험이 적용되었습니다! 게이지 {value}% 충전"
    elif coupon_type == "gauge_bonus":
        return f"게이지 {value}%가 충전되었습니다!"
    return f"쿠폰이 적용되었습니다! +{value}%"


async def _get_user(authorization: str):
    """인증 토큰에서 사용자 추출"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    token = authorization.split(" ", 1)[1]
    user = await auth_service.get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    return user
