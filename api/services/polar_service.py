"""Polar 결제 서비스"""

import os
import httpx

POLAR_API = "https://api.polar.sh/v1"


def _headers():
    token = os.environ.get("POLAR_ACCESS_TOKEN", "")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


async def create_checkout(product_id: str, success_url: str, customer_email: str = "") -> dict:
    """Polar 체크아웃 세션 생성 → 결제 URL 반환"""
    payload = {
        "product_id": product_id,
        "success_url": success_url,
        "allow_discount_codes": True,
    }
    if customer_email:
        payload["customer_email"] = customer_email

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{POLAR_API}/checkouts/custom/",
            json=payload,
            headers=_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()


async def get_order(order_id: str) -> dict:
    """주문 상세 조회 (결제 완료 확인용)"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{POLAR_API}/orders/{order_id}",
            headers=_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()


async def get_subscription(subscription_id: str) -> dict:
    """구독 상태 조회"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{POLAR_API}/subscriptions/{subscription_id}",
            headers=_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
