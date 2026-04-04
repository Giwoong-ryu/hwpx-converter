"""결제 API - Polar 연동 + % 게이지 시스템"""

import os
from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel

from api.services import auth_service, credit_service, polar_service

router = APIRouter()

PRODUCT_PLANS = {
    os.environ.get("POLAR_STARTER_PRODUCT_ID", ""): "plus",
    os.environ.get("POLAR_PRO_PRODUCT_ID", ""): "pro",
}


class CheckoutRequest(BaseModel):
    product_id: str


@router.post("/checkout")
async def create_checkout(req: CheckoutRequest, request: Request, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="결제하려면 로그인이 필요합니다.")
    token = authorization.split(" ", 1)[1]
    user = await auth_service.get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    base = str(request.base_url).rstrip("/")
    success_url = f"{base}/pricing?payment=success&user_id={user.id}&product_id={req.product_id}"

    try:
        result = await polar_service.create_checkout(
            product_id=req.product_id,
            success_url=success_url,
            customer_email=user.email or "",
        )
        return {"checkout_url": result.get("url", "")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"결제 생성 실패: {e}")


@router.post("/webhook")
async def polar_webhook(request: Request):
    body = await request.json()
    event_type = body.get("type", "")

    if event_type == "order.created":
        await _handle_order(body.get("data", {}))
    elif event_type == "subscription.created":
        await _handle_subscription(body.get("data", {}))
    elif event_type == "subscription.canceled":
        await _handle_cancel(body.get("data", {}))

    return {"received": True}


@router.post("/confirm")
async def confirm_payment(user_id: str, product_id: str, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증 필요")

    plan = PRODUCT_PLANS.get(product_id)
    if not plan:
        raise HTTPException(status_code=400, detail="알 수 없는 상품입니다.")

    await credit_service.charge_gauge(user_id, plan)
    return {"ok": True, "plan": plan}


async def _handle_order(data: dict):
    """일회성 결제 (Plus) → 게이지 충전"""
    product_id = data.get("product_id", "")
    customer_email = data.get("customer", {}).get("email", "")
    plan = PRODUCT_PLANS.get(product_id)
    if not plan or not customer_email:
        return

    from api.services.supabase_client import get_supabase
    sb = get_supabase()
    result = sb.table("docflow_users").select("id").eq("email", customer_email).single().execute()
    if not result.data:
        return

    await credit_service.charge_gauge(result.data["id"], plan)


async def _handle_subscription(data: dict):
    """구독 시작 (Pro)"""
    product_id = data.get("product", {}).get("id", "")
    customer_email = data.get("customer", {}).get("email", "")
    plan = PRODUCT_PLANS.get(product_id)
    if not plan or not customer_email:
        return

    from api.services.supabase_client import get_supabase
    sb = get_supabase()
    result = sb.table("docflow_users").select("id").eq("email", customer_email).single().execute()
    if not result.data:
        return

    await credit_service.charge_gauge(result.data["id"], plan)
    sb.table("docflow_users").update({
        "polar_subscription_id": data.get("id", ""),
    }).eq("id", result.data["id"]).execute()


async def _handle_cancel(data: dict):
    """구독 취소 → free로"""
    customer_email = data.get("customer", {}).get("email", "")
    if not customer_email:
        return

    from api.services.supabase_client import get_supabase
    sb = get_supabase()
    result = sb.table("docflow_users").select("id").eq("email", customer_email).single().execute()
    if not result.data:
        return

    defaults = credit_service.PLAN_DEFAULTS["free"]
    sb.table("docflow_users").update({
        "plan": "free",
        "gauge_percent": 0,
        "polar_subscription_id": None,
        **defaults,
    }).eq("id", result.data["id"]).execute()
