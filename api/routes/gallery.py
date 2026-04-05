"""양식 갤러리 API - 빈 양식 공유/탐색/좋아요/다운로드"""

import os
import uuid

from fastapi import APIRouter, HTTPException, Header, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional

from api.services.supabase_client import get_supabase
from api.services import auth_service, credit_service

router = APIRouter()

CATEGORIES = ["사업계획서", "이력서", "견적서", "보고서", "계약서", "공문", "회의록", "수료증", "기타"]
BUCKET = "shared-forms"


# ═══ 공개 목록 (비로그인 가능) ═══

@router.get("/list")
async def list_forms(
    category: Optional[str] = Query(None),
    sort: str = Query("popular", regex="^(popular|recent|downloads)$"),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
):
    """공개 양식 목록"""
    sb = get_supabase()
    offset = (page - 1) * size

    query = sb.table("docflow_shared_forms").select(
        "id, title, category, field_count, doc_type, likes, downloads, created_at, user_id"
    )

    if category and category in CATEGORIES:
        query = query.eq("category", category)
    if q:
        query = query.ilike("title", f"%{q}%")

    order_col = {"popular": "likes", "recent": "created_at", "downloads": "downloads"}[sort]
    query = query.order(order_col, desc=True).range(offset, offset + size - 1)

    result = query.execute()
    return {"forms": result.data or [], "page": page, "size": size}


@router.get("/{form_id}")
async def get_form_detail(form_id: int):
    """양식 상세 (필드 수, 카테고리 등)"""
    sb = get_supabase()
    result = sb.table("docflow_shared_forms").select(
        "id, title, category, field_count, doc_type, likes, downloads, created_at, user_id, file_size"
    ).eq("id", form_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="양식을 찾을 수 없습니다.")

    return {"form": result.data[0]}


# ═══ 다운로드 (로그인 필요) ═══

@router.get("/{form_id}/download")
async def download_form(form_id: int, authorization: str = Header(None)):
    """양식 파일 다운로드"""
    await _require_auth(authorization)
    sb = get_supabase()

    result = sb.table("docflow_shared_forms").select(
        "id, title, file_path, downloads"
    ).eq("id", form_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="양식을 찾을 수 없습니다.")

    form = result.data[0]
    file_path = form["file_path"]

    # 다운로드 수 증가
    sb.table("docflow_shared_forms").update(
        {"downloads": (form.get("downloads") or 0) + 1}
    ).eq("id", form_id).execute()

    # Supabase Storage에서 파일 다운로드
    try:
        file_data = sb.storage.from_(BUCKET).download(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 다운로드 실패: {e}")

    filename = f"{form['title']}.hwpx"
    return StreamingResponse(
        iter([file_data]),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
    )


# ═══ 양식 공유 (로그인 필요) ═══

@router.post("/share")
async def share_form(
    title: str = Form(...),
    category: str = Form("기타"),
    file: UploadFile = File(...),
    authorization: str = Header(None),
):
    """빈 양식을 갤러리에 공유"""
    user = await _require_auth(authorization)

    if category not in CATEGORIES:
        category = "기타"

    # 파일 확장자 체크
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in (".hwpx", ".hwp", ".docx"):
        raise HTTPException(status_code=400, detail="HWP, HWPX, DOCX 파일만 공유할 수 있습니다.")

    # 파일 읽기
    content = await file.read()
    file_size = len(content)
    if file_size > 100 * 1024 * 1024:  # 100MB
        raise HTTPException(status_code=400, detail="파일 크기가 100MB를 초과합니다.")

    # 필드 수 추출 (HWPX만)
    field_count = 0
    doc_type = None
    if ext == ".hwpx":
        try:
            import tempfile
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            tmp.write(content)
            tmp.close()
            from clone_form import extract_texts
            fields = extract_texts(tmp.name)
            field_count = len(fields)
            from api.services.doc_type_detector import detect_doc_type
            doc_info = detect_doc_type(fields)
            doc_type = doc_info.get("type")
            os.unlink(tmp.name)
        except Exception:
            pass

    # Supabase Storage에 업로드
    sb = get_supabase()
    storage_path = f"forms/{user.id}/{uuid.uuid4().hex}{ext}"
    try:
        sb.storage.from_(BUCKET).upload(
            storage_path, content,
            file_options={"content-type": "application/octet-stream"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 업로드 실패: {e}")

    # DB에 메타데이터 저장
    result = sb.table("docflow_shared_forms").insert({
        "user_id": user.id,
        "title": title[:100],
        "category": category,
        "file_path": storage_path,
        "file_size": file_size,
        "field_count": field_count,
        "doc_type": doc_type,
    }).execute()

    # 공유 보상 (+25%)
    rewards = []
    try:
        form_id = result.data[0]["id"] if result.data else 0
        share_key = f"share_form_{form_id}"
        from api.services.credit_service import _grant_achievement
        _grant_achievement(user.id, share_key, 25.0)

        # 게이지 추가
        user_data = sb.table("docflow_users").select("gauge_percent").eq("id", user.id).single().execute()
        if user_data.data:
            current = float(user_data.data.get("gauge_percent", 0))
            sb.table("docflow_users").update(
                {"gauge_percent": round(current + 25.0, 1)}
            ).eq("id", user.id).execute()
            rewards.append({"type": "share", "label": "양식 공유 보상", "amount": 25})
    except Exception:
        pass

    return {
        "form": result.data[0] if result.data else None,
        "rewards": rewards,
    }


# ═══ 좋아요 (로그인 필요) ═══

@router.post("/{form_id}/like")
async def toggle_like(form_id: int, authorization: str = Header(None)):
    """좋아요 토글"""
    user = await _require_auth(authorization)
    sb = get_supabase()

    form = sb.table("docflow_shared_forms").select(
        "id, likes, user_id"
    ).eq("id", form_id).execute()
    if not form.data:
        raise HTTPException(status_code=404, detail="양식을 찾을 수 없습니다.")

    current_likes = form.data[0].get("likes", 0)
    form_owner = form.data[0].get("user_id")

    # 이미 좋아요했는지
    existing = sb.table("docflow_form_likes").select("id").eq(
        "user_id", user.id
    ).eq("form_id", form_id).execute()

    if existing.data:
        sb.table("docflow_form_likes").delete().eq(
            "user_id", user.id
        ).eq("form_id", form_id).execute()
        new_likes = max(current_likes - 1, 0)
        sb.table("docflow_shared_forms").update(
            {"likes": new_likes}
        ).eq("id", form_id).execute()
        return {"liked": False, "likes": new_likes}
    else:
        sb.table("docflow_form_likes").insert({
            "user_id": user.id,
            "form_id": form_id,
        }).execute()
        new_likes = current_likes + 1
        sb.table("docflow_shared_forms").update(
            {"likes": new_likes}
        ).eq("id", form_id).execute()

        # 좋아요 10개 단위 보상 (양식 소유자에게)
        if form_owner and new_likes > 0 and new_likes % 10 == 0:
            try:
                owner_data = sb.table("docflow_users").select("gauge_percent").eq("id", form_owner).single().execute()
                if owner_data.data:
                    current = float(owner_data.data.get("gauge_percent", 0))
                    sb.table("docflow_users").update(
                        {"gauge_percent": round(current + 50.0, 1)}
                    ).eq("id", form_owner).execute()
            except Exception:
                pass

        return {"liked": True, "likes": new_likes}


# ═══ 삭제 (본인만) ═══

@router.delete("/{form_id}")
async def delete_form(form_id: int, authorization: str = Header(None)):
    """내 공유 양식 삭제"""
    user = await _require_auth(authorization)
    sb = get_supabase()

    existing = sb.table("docflow_shared_forms").select(
        "id, file_path"
    ).eq("id", form_id).eq("user_id", user.id).execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="양식을 찾을 수 없습니다.")

    # Storage에서 파일 삭제
    try:
        sb.storage.from_(BUCKET).remove([existing.data[0]["file_path"]])
    except Exception:
        pass

    # DB에서 삭제
    sb.table("docflow_form_likes").delete().eq("form_id", form_id).execute()
    sb.table("docflow_shared_forms").delete().eq("id", form_id).eq("user_id", user.id).execute()

    return {"deleted": True}


async def _require_auth(authorization: str):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    token = authorization.split(" ", 1)[1]
    user = await auth_service.get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    return user
