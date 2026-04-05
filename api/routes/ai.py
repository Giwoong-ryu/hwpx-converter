"""AI 자동 매핑 API"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Header
from typing import Optional

from api.services.file_manager import file_manager
from api.services.metrics import log as mlog, Timer
from api.services import credit_service, auth_service
from ai_mapper import map_content

router = APIRouter()


@router.post("/map")
async def ai_map(
    file_id: str = Form(...),
    text: Optional[str] = Form(None),
    content_file: Optional[UploadFile] = File(None),
    authorization: Optional[str] = Header(None),
    x_fingerprint: Optional[str] = Header(None),
):
    # ── 게이트키퍼: 인증 + 크레딧 체크 ──
    user_id = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            user = await auth_service.get_user_from_token(token)
            if user:
                user_id = user.id
        except Exception:
            pass  # 만료/유효하지 않은 토큰 → 비로그인으로 처리

    from ai_mapper import _is_generation_request
    action = "generation" if _is_generation_request(text) else "mapping"

    gauge_cost = 0.0
    if user_id:
        credit_result = await credit_service.use_gauge(user_id, action)
        if not credit_result["ok"]:
            code = credit_result.get("error_code", "GAUGE_EMPTY")
            status = 401 if code == "LOGIN_REQUIRED" else 429
            raise HTTPException(status_code=status, detail={
                "detail": credit_result.get("detail", "사용량 초과"),
                "error_code": code,
                "plan": credit_result.get("plan", ""),
                "gauge_pct": credit_result.get("gauge_pct", 0),
            })
        gauge_cost = credit_result.get("cost", 0.0)
    else:
        # 비로그인: 핑거프린트 기반 맛보기
        fp = x_fingerprint or "unknown"
        anon_result = await credit_service.check_anon(fp, action)
        if not anon_result["ok"]:
            raise HTTPException(status_code=401, detail={
                "detail": anon_result.get("detail", "로그인이 필요합니다."),
                "error_code": anon_result.get("error_code", "LOGIN_REQUIRED"),
            })

    path = file_manager.get_path(file_id)
    if not path:
        mlog("ai_map", success=False, error="파일 없음")
        raise HTTPException(status_code=404, detail="양식 파일을 찾을 수 없습니다. 다시 분석해주세요.")

    try:
        from clone_form import extract_texts, extract_structured_fields
        fields = extract_texts(path)
        # 테이블 구조 추출 (실패 시 None → 평면 리스트로 폴백)
        structured = None
        try:
            structured = extract_structured_fields(path)
            print(f"[ai/map] 구조 추출: 표 {len(structured.get('tables', []))}개, 본문 {len(structured.get('paragraphs', []))}개")
        except Exception as se:
            print(f"[ai/map] 구조 추출 실패, 평면 모드로 폴백: {se}")
    except Exception as e:
        mlog("ai_map", success=False, error=f"양식 분석: {e}")
        raise HTTPException(status_code=500, detail=f"양식 파일을 분석할 수 없습니다: {e}")

    content_path = None
    if content_file and content_file.filename:
        try:
            cid = await file_manager.save_upload(content_file)
            content_path = file_manager.get_path(cid)
        except Exception as e:
            mlog("ai_map", success=False, error=f"파일 업로드: {e}")
            raise HTTPException(status_code=500, detail="파일 업로드에 실패했습니다. 다시 시도해주세요.")

    mode = "generate" if action == "generation" else "mapping"
    with Timer() as t:
        try:
            print(f"[ai/map] fields={len(fields)}, text_len={len(text or '')}, content_path={content_path}")
            result, error = map_content(fields, text or "", content_path, structured=structured)
            print(f"[ai/map] result={'OK' if result else 'None'}, error={error}")
        except Exception as e:
            import traceback as tb
            err_msg = tb.format_exc()
            print(f"[ai/map] EXCEPTION: {err_msg}")
            with open("ai_error.log", "a", encoding="utf-8") as f:
                f.write(f"\n{'='*50}\n{err_msg}\n")
            mlog("ai_map", success=False, field_count=len(fields), duration_ms=0, error=str(e), detail=mode)
            # AI 실패 시 차감된 게이지 복구
            if user_id and gauge_cost > 0:
                try:
                    await credit_service.refund_gauge(user_id, gauge_cost)
                except Exception:
                    pass
            raise HTTPException(status_code=500, detail="AI 처리 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.")

    if error:
        mlog("ai_map", success=False, field_count=len(fields), duration_ms=t.ms, error=error, detail=mode)
        raise HTTPException(status_code=400, detail=error)

    # 매핑 커버리지 계산
    field_set = set(fields)
    matched_count = sum(1 for k in result if k in field_set)
    coverage_pct = (matched_count / max(len(fields), 1)) * 100
    is_generation = mode == "generate"

    mlog("ai_map", success=True, field_count=len(fields), duration_ms=t.ms,
         detail=f"{mode}, mapped={len(result)}, matched={matched_count}, coverage={coverage_pct:.1f}%")

    return {
        "mapping_count": len(result),
        "mappings": result,
        "coverage": {
            "total_fields": len(fields),
            "mapped": matched_count,
            "coverage_pct": round(coverage_pct, 1),
        },
        "is_generation": is_generation,
    }
