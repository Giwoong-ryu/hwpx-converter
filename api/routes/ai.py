"""AI 자동 매핑 API"""

import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Header
from typing import Optional, List

from api.services.file_manager import file_manager
from api.services.metrics import log as mlog, Timer
from api.services import credit_service, auth_service
from ai_mapper import map_content, direct_map

router = APIRouter()


@router.post("/map")
async def ai_map(
    file_id: str = Form(...),
    text: Optional[str] = Form(None),
    content_file: Optional[UploadFile] = File(None),
    content_files: Optional[List[UploadFile]] = File(None),
    mode: Optional[str] = Form(None),  # "direct" | "ai" (기본값: ai)
    authorization: Optional[str] = Header(None),
    x_fingerprint: Optional[str] = Header(None),
):
    # ── 모드 결정 (direct=AI없음, ai=AI사용) ──
    use_direct = (mode == "direct")

    # ── 게이트키퍼: 인증 + 크레딧 체크 (AI 모드만) ──
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
    if not use_direct:
        # AI 모드: 크레딧 차감
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

    # 복수 파일 처리 (content_files 우선, 없으면 content_file 단일)
    all_files = []
    if content_files:
        all_files = [f for f in content_files if f and f.filename]
    elif content_file and content_file.filename:
        all_files = [content_file]

    # 무료 사용자: 파일 1개 제한 (AI 모드만 — direct 모드는 5MB 총량으로만 제한)
    if len(all_files) > 1 and not use_direct:
        if user_id:
            try:
                status = await credit_service.get_user_status(user_id)
                plan = status.get("plan", "free") if status else "free"
                if plan == "free":
                    raise HTTPException(status_code=429, detail={
                        "detail": "무료 플랜은 파일 1개만 업로드할 수 있습니다. Plus로 업그레이드하면 여러 파일을 한번에 처리할 수 있습니다.",
                        "error_code": "FILE_LIMIT",
                    })
            except HTTPException:
                raise
            except Exception:
                pass
        else:
            raise HTTPException(status_code=401, detail={
                "detail": "여러 파일을 업로드하려면 로그인이 필요합니다.",
                "error_code": "LOGIN_REQUIRED",
            })

    # 파일 합산 크기 체크 (5MB)
    content_paths = []
    total_size = 0
    warnings = []
    for i, f in enumerate(all_files[:5]):  # 최대 5개
        try:
            cid = await file_manager.save_upload(f)
            cp = file_manager.get_path(cid)
            if cp:
                content_paths.append(cp)
                total_size += os.path.getsize(cp)
        except Exception as e:
            warnings.append(f"파일 '{f.filename}' 읽기 실패")
            print(f"[ai/map] 파일 {i+1} 업로드 실패: {e}")

    if total_size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="파일 총 크기가 5MB를 초과합니다. 파일을 줄여주세요.")

    # 하위 호환: 단일 content_path 또는 복수 content_paths
    content_path = content_paths[0] if len(content_paths) == 1 else None
    extra_paths = content_paths[1:] if len(content_paths) > 1 else []

    action_mode = "direct" if use_direct else ("generate" if action == "generation" else "mapping")
    with Timer() as t:
        try:
            print(f"[ai/map] mode={action_mode}, fields={len(fields)}, text_len={len(text or '')}, files={len(content_paths)}")
            if use_direct:
                # 레인 1: AI 없이 직접 매칭
                result, error = direct_map(fields, content_paths, text or "")
            else:
                result, error = map_content(
                    fields, text or "", content_path,
                    structured=structured,
                    extra_content_files=extra_paths if extra_paths else None,
                )
            print(f"[ai/map] result={'OK' if result else 'None'}, error={error}")
        except Exception as e:
            import traceback as tb
            err_msg = tb.format_exc()
            print(f"[ai/map] EXCEPTION: {err_msg}")
            with open("ai_error.log", "a", encoding="utf-8") as f:
                f.write(f"\n{'='*50}\n{err_msg}\n")
            mlog("ai_map", success=False, field_count=len(fields), duration_ms=0, error=str(e), detail=action_mode)
            # AI 실패 시 차감된 게이지 복구
            if user_id and gauge_cost > 0:
                try:
                    await credit_service.refund_gauge(user_id, gauge_cost)
                except Exception:
                    pass
            raise HTTPException(status_code=500, detail="처리 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.")

    if error:
        mlog("ai_map", success=False, field_count=len(fields), duration_ms=t.ms, error=error, detail=action_mode)
        raise HTTPException(status_code=400, detail=error)

    # 매핑 커버리지 계산 (__N 접미사 제거 후 원본 필드와 매칭)
    import re as _re
    field_set = set(fields)
    def _base_key(k):
        return _re.sub(r"__\d+$", "", k)
    base_field_set = {_base_key(f) for f in field_set}
    matched_count = sum(1 for k in result if k in field_set or _base_key(k) in base_field_set)
    coverage_pct = (matched_count / max(len(fields), 1)) * 100

    # 칸별 출처 판정
    sources = {}
    ai_count = 0
    if use_direct:
        # 직접 채우기: 모든 값은 사용자 자료에서 온 것
        for k in result:
            sources[k] = "user"
    else:
        user_text = (text or "").strip()
        for cp in content_paths:
            try:
                ext = os.path.splitext(cp)[1].lower()
                if ext in (".html", ".htm"):
                    # HTML은 태그 제거 후 텍스트만 추출 (raw 읽기 시 태그가 섞여 출처 판정 오작동)
                    from bs4 import BeautifulSoup
                    with open(cp, "r", encoding="utf-8", errors="ignore") as f:
                        soup = BeautifulSoup(f.read(), "html.parser")
                    for tag in soup(["script", "style"]):
                        tag.decompose()
                    user_text += "\n" + soup.get_text(separator="\n", strip=True)
                else:
                    with open(cp, "r", encoding="utf-8", errors="ignore") as f:
                        user_text += "\n" + f.read()
            except Exception:
                pass
        user_text_lower = user_text.lower().replace(" ", "")

        for k, v in result.items():
            if not v or not v.strip():
                sources[k] = "user"
                continue
            v_check = v.strip().lower().replace(" ", "")
            if len(v_check) >= 2 and v_check in user_text_lower:
                sources[k] = "user"
            elif user_text.strip():
                sources[k] = "ai"
                ai_count += 1
            else:
                sources[k] = "ai"
                ai_count += 1

    mlog("ai_map", success=True, field_count=len(fields), duration_ms=t.ms,
         detail=f"mode={action_mode}, mapped={len(result)}, matched={matched_count}, coverage={coverage_pct:.1f}%, ai_filled={ai_count}")

    return {
        "mapping_count": len(result),
        "mappings": result,
        "sources": sources,
        "coverage": {
            "total_fields": len(fields),
            "mapped": matched_count,
            "coverage_pct": round(coverage_pct, 1),
            "ai_filled": ai_count,
        },
    }
