"""인증 서비스 - Supabase Auth 기반"""

import random
import string
from api.services.supabase_client import get_supabase


def _gen_referral_code() -> str:
    chars = string.ascii_uppercase + string.digits
    return "EAZY-" + "".join(random.choices(chars, k=6))


async def sign_up(email: str, password: str, name: str = "", referral_code: str = ""):
    sb = get_supabase()
    result = sb.auth.sign_up({"email": email, "password": password})
    if result.user:
        sb.table("docflow_users").upsert({
            "id": result.user.id,
            "email": email,
            "name": name,
            "plan": "free",
            "gauge_percent": 0,
            "preset_limit": 1,
            "mapping_save_limit": 0,
            "streak_freeze_count": 0,
            "referral_code": _gen_referral_code(),
            "referred_by": referral_code or None,
        }).execute()
    return result


async def sign_in(email: str, password: str):
    sb = get_supabase()
    return sb.auth.sign_in_with_password({"email": email, "password": password})


async def get_user_from_token(token: str):
    sb = get_supabase()
    result = sb.auth.get_user(token)
    return result.user if result else None


async def get_profile(user_id: str):
    sb = get_supabase()
    result = sb.table("docflow_users").select("*").eq("id", user_id).single().execute()
    return result.data


async def sign_in_with_provider(provider: str, redirect_to: str):
    sb = get_supabase()
    result = sb.auth.sign_in_with_oauth({
        "provider": provider,
        "options": {"redirect_to": redirect_to}
    })
    return result
