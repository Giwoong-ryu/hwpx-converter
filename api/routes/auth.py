"""인증 + 사용자 상태 API"""

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel

from api.services import auth_service, credit_service

router = APIRouter()


class SignUpRequest(BaseModel):
    email: str
    password: str
    name: str = ""
    referral_code: str = ""


class SignInRequest(BaseModel):
    email: str
    password: str


@router.post("/signup")
async def signup(req: SignUpRequest):
    try:
        result = await auth_service.sign_up(req.email, req.password, req.name)
        if result.user:
            # 추천 코드 생성
            code = credit_service.generate_referral_code()
            from api.services.supabase_client import get_supabase
            sb = get_supabase()
            sb.table("docflow_users").upsert({
                "id": result.user.id,
                "email": req.email,
                "name": req.name,
                "plan": "free",
                "gauge_percent": 0,
                "referral_code": code,
                "referred_by": req.referral_code or None,
            }).execute()

            # 추천인 보상 (추천 코드가 있으면)
            if req.referral_code:
                referrer = sb.table("docflow_users").select("id").eq(
                    "referral_code", req.referral_code
                ).single().execute()
                if referrer.data:
                    # 추천 보상은 첫 문서 완성 시 지급 (on_doc_complete에서)
                    sb.table("docflow_users").update({
                        "referred_by": req.referral_code,
                    }).eq("id", result.user.id).execute()

            return {"user_id": result.user.id, "email": result.user.email}
        raise HTTPException(status_code=400, detail="가입 실패")
    except Exception as e:
        if "already registered" in str(e).lower():
            raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다.")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(req: SignInRequest):
    try:
        result = await auth_service.sign_in(req.email, req.password)
        if result.session:
            return {
                "access_token": result.session.access_token,
                "refresh_token": result.session.refresh_token,
                "user_id": result.user.id,
                "email": result.user.email,
            }
        raise HTTPException(status_code=401, detail="로그인 실패")
    except Exception:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")


@router.get("/me")
async def get_me(authorization: str = Header(None)):
    user = await _get_user(authorization)
    status = await credit_service.get_user_status(user.id)
    if not status:
        raise HTTPException(status_code=404, detail="프로필을 찾을 수 없습니다.")
    return {"user_id": user.id, "email": user.email, **status}


@router.get("/status")
async def get_status(authorization: str = Header(None)):
    """게이지 + 레벨 + 스트릭 상태 (도구 페이지 헤더용)"""
    user = await _get_user(authorization)
    status = await credit_service.get_user_status(user.id)
    return status


@router.get("/oauth/{provider}")
async def oauth_login(provider: str, request: Request):
    if provider not in ("kakao", "google"):
        raise HTTPException(status_code=400, detail="지원하지 않는 로그인 방식입니다.")
    base = str(request.base_url).rstrip("/")
    redirect_to = f"{base}/auth/callback"
    result = await auth_service.sign_in_with_provider(provider, redirect_to)
    return {"url": result.url}


async def _get_user(authorization: str):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    token = authorization.split(" ", 1)[1]
    user = await auth_service.get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    return user
