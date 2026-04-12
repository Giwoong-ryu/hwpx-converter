"""양식 분석 + 문서 생성 API"""

import os
import re
import tempfile

from fastapi import APIRouter, HTTPException, UploadFile, File, Header
from typing import Optional
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.services.file_manager import file_manager
from api.services.metrics import log as mlog, Timer
from api.services import credit_service, auth_service
from clone_form import (
    extract_texts, clone as clone_hwpx, validate_result,
    build_header_slot_map, inject_values_by_slot,
)

router = APIRouter()


_MAX_UPLOAD = 100 * 1024 * 1024  # 100MB


@router.post("/analyze")
async def analyze_form(file: UploadFile = File(...)):
    in_fmt = (file.filename or "").rsplit(".", 1)[-1].lower() if file.filename else "unknown"
    with Timer() as t:
        # 파일 크기 검사
        content = await file.read()
        if len(content) > _MAX_UPLOAD:
            mlog("analyze", success=False, input_format=in_fmt, error="파일 크기 초과")
            raise HTTPException(status_code=413, detail="파일이 너무 큽니다. 100MB 이하만 가능합니다.")
        await file.seek(0)

        file_id = await file_manager.save_upload(file)
        path = file_manager.get_path(file_id)

        # HWP → HWPX 변환
        if path and path.lower().endswith(".hwp"):
            try:
                file_id = file_manager.convert_hwp(file_id)
            except RuntimeError as e:
                mlog("analyze", success=False, input_format="hwp", error=str(e))
                raise HTTPException(status_code=400, detail=str(e))
            path = file_manager.get_path(file_id)

        # DOCX → HWPX 변환
        if path and path.lower().endswith(".docx"):
            try:
                file_id = file_manager.convert_docx(file_id)
            except RuntimeError as e:
                mlog("analyze", success=False, input_format="docx", error=str(e))
                raise HTTPException(status_code=400, detail=str(e))
            path = file_manager.get_path(file_id)

        texts = extract_texts(path)
        if not texts:
            mlog("analyze", success=False, input_format=in_fmt, error="텍스트 추출 실패")
            raise HTTPException(status_code=400, detail="텍스트를 추출할 수 없습니다.")

    warning = None
    if len(texts) > 3000:
        warning = f"문서가 매우 큽니다 ({len(texts)}개 필드). AI 매핑 시 최대 3000개까지만 처리되며, 시간이 오래 걸릴 수 있습니다."

    mlog("analyze", success=True, input_format=in_fmt, field_count=len(texts), duration_ms=t.ms)

    from api.services.doc_type_detector import detect_doc_type
    doc_info = detect_doc_type(texts)

    return {
        "file_id": file_id,
        "filename": file.filename,
        "field_count": len(texts),
        "fields": texts,
        "warning": warning,
        "doc_type": doc_info["type"],
        "doc_type_confidence": doc_info["confidence"],
        "smart_fields": doc_info["smart_fields"],
    }


class GenerateRequest(BaseModel):
    file_id: str
    replacements: dict[str, str]
    strip_images: bool = False
    output_format: str = "hwpx"  # "hwpx", "hwp", "docx"


@router.post("/generate")
async def generate_form(req: GenerateRequest, authorization: Optional[str] = Header(None)):
    path = file_manager.get_path(req.file_id)
    if not path:
        mlog("generate", success=False, error="파일 없음")
        raise HTTPException(status_code=404, detail="양식 파일을 찾을 수 없습니다. 다시 분석해주세요.")

    # 라벨 셀 카운트 추출: 같은 텍스트가 라벨(bold/bg)과 값 셀에 모두 있을 때
    # __N 치환 시 라벨 셀을 건너뛰기 위해 사용 (A1 수정)
    label_counts: dict[str, int] = {}
    try:
        from clone_form import extract_structured_fields
        structured_data = extract_structured_fields(path)
        seen_cell_ids: set[int] = set()
        for table in structured_data.get("tables", []):
            for row in table["rows"]:
                for cell in row:
                    cid = id(cell)
                    if cid in seen_cell_ids:
                        continue  # 병합 셀 중복 제외
                    seen_cell_ids.add(cid)
                    if (cell.get("bold") or cell.get("bg")) and cell.get("text", "").strip():
                        t = cell["text"].strip()
                        label_counts[t] = label_counts.get(t, 0) + 1
    except Exception:
        pass  # 실패해도 label_counts={} 로 계속 (치환 순서만 약간 어긋날 수 있음)

    # ── 양식 타입 분류 (invoice/section/legacy) ──
    form_type = "legacy"
    try:
        from processors.form_classifier import classify_form
        form_type = classify_form(structured_data) if structured_data else "legacy"
        print(f"[classify] form_type={form_type}")
    except Exception as cls_e:
        print(f"[classify] 분류 실패 (legacy 폴백): {cls_e}")

    # ── 슬롯 맵 빌드: form_type에 따라 분기 ──
    slot_map: dict = {}
    try:
        if form_type == "invoice_style":
            # 인보이스형: 일반 텍스트 라벨 인식
            from processors.invoice_processor import InvoiceProcessor
            proc = InvoiceProcessor(path, structured_data)
            slot_map = proc.build_slot_map()
            print(f"[generate] invoice_style 슬롯 맵: {len(slot_map)}개 라벨 탐지")
        else:
            # 기존 경로 (legacy / section_based)
            slot_map = build_header_slot_map(path)
            if slot_map:
                print(f"[generate] 슬롯 맵: {len(slot_map)}개 헤더 탐지")
    except Exception as slot_e:
        print(f"[generate] 슬롯 맵 빌드 실패 (폴백): {slot_e}")

    # ── 한국 포맷터 후처리 (금액 콤마, 날짜, 전화, 사업자번호) ──
    formatted_replacements = dict(req.replacements)
    try:
        from kr_formatter import KrFormatter
        fmt_result = KrFormatter.auto_detect_and_format(formatted_replacements)
        formatted_replacements = fmt_result["formatted"]
        for log_entry in fmt_result["log"]:
            print(f"[generate] {log_entry}")
    except ImportError:
        print("[generate] kr_formatter 미설치, 포맷팅 스킵")
    except Exception as fmt_err:
        print(f"[generate] 포맷팅 실패 (원본 사용): {fmt_err}")

    # replacements를 슬롯 주입용 vs 일반 텍스트 치환으로 분리
    # __N 접미사는 연속 가능: 월일__1__2 → base=월일, indices=[1,2]
    # __N__M (더블언더스코어 복수) 또는 __N_M (더블+싱글언더스코어 2D) 접미사 제거
    _base_re = re.compile(r'(?:__\d+)+$|__\d+(?:_\d+)+$')
    _ws_re = re.compile(r'\s+')
    slot_assignments: list = []
    normal_repl: dict[str, str] = {}

    # 슬롯 맵 키 정규화 인덱스 (공백 차이 무시: "성 명" vs "성명" 매칭)
    slot_map_norm = {_ws_re.sub('', k): k for k in slot_map}

    for key, value in formatted_replacements.items():
        base = _base_re.sub('', key)  # __N 또는 __N_M 접미사 제거
        suffix_match = _base_re.search(key)
        # suffix에서 모든 숫자 그룹 추출 (구형 __1__2, 신형 __1_2 모두 지원)
        indices = [int(x) for x in re.findall(r'\d+', suffix_match.group(0))] if suffix_match else []
        base_norm = _ws_re.sub('', base)
        real_key = slot_map_norm.get(base_norm)
        # 복합 키 폴백 1: "__" 세그먼트 마지막 부분 ("금   액__합계" → "합계")
        if real_key is None and '__' in base:
            last_seg = base.split('__')[-1]
            if last_seg:
                real_key = slot_map_norm.get(_ws_re.sub('', last_seg))
        # 복합 키 폴백 2: base_norm이 슬롯키를 포함하는 경우 슬롯 수 가장 적은 키로 매칭
        # 예: "합계금액" → 합계(2슬롯) vs 금액(31슬롯) → 슬롯 적은 "합  계" 선택
        if real_key is None and slot_map_norm:
            candidates = [(snk, sk) for snk, sk in slot_map_norm.items()
                          if len(snk) >= 2 and snk in base_norm]
            if candidates:
                # 슬롯 수 오름차순 → 가장 구체적인(슬롯 적은) 키 선택
                best = min(candidates, key=lambda x: len(slot_map[x[1]]))
                real_key = best[1]
        if real_key is not None and slot_map[real_key]:
            slots = slot_map[real_key]
            if indices:
                # 복수 인덱스 → 평탄화 슬롯 인덱스로 변환 (2분할 양식 지원)
                if len(indices) == 1:
                    flat_idx = indices[0] - 1
                else:
                    n = len(slots) // max(indices[0], 2)
                    flat_idx = (indices[0] - 1) * n + (indices[-1] - 1)
                if 0 <= flat_idx < len(slots):
                    sa = dict(slots[flat_idx])
                    sa["value"] = value
                    slot_assignments.append(sa)
            else:
                # suffix 없음: 연속된 모든 슬롯에 동일 값 주입
                for slot in slots:
                    sa = dict(slot)
                    sa["value"] = value
                    slot_assignments.append(sa)
        else:
            normal_repl[key] = value

    print(f"[generate] 슬롯 주입={len(slot_assignments)}개, 일반치환={len(normal_repl)}개")

    fmt = req.output_format.lower()
    with Timer() as t:
        try:
            out_path = os.path.join(tempfile.mkdtemp(), "EazyHWPX_result.hwpx")

            # Phase 1: 빈 셀에 슬롯 주입 (빈칸형 양식)
            src_for_clone = path
            if slot_assignments:
                injected_path = os.path.join(tempfile.mkdtemp(), "EazyHWPX_injected.hwpx")
                inject_values_by_slot(path, injected_path, slot_assignments)
                src_for_clone = injected_path
                print(f"[generate] 슬롯 주입 완료: {len(slot_assignments)}개 셀")

            # Phase 2: 플레이스홀더형 텍스트 치환
            clone_hwpx(src_for_clone, out_path, replacements=normal_repl,
                       strip_images=req.strip_images, label_counts=label_counts or None)
        except Exception as e:
            mlog("generate", success=False, output_format=fmt, field_count=len(req.replacements), error=str(e))
            raise HTTPException(status_code=500, detail=f"문서 생성 실패: {e}")

        # 출력 형식 변환
        if fmt == "hwp":
            try:
                hwpx_id = file_manager.save(out_path, "result.hwpx")
                hwp_id = file_manager.convert_to_hwp(hwpx_id)
                result_path = file_manager.get_path(hwp_id)
            except Exception as e:
                mlog("generate", success=False, output_format="hwp", field_count=len(req.replacements), error=str(e))
                raise HTTPException(status_code=500, detail=f"HWP 변환 실패: {e}")
        elif fmt == "docx":
            try:
                hwpx_id = file_manager.save(out_path, "result.hwpx")
                docx_id = file_manager.convert_to_docx(hwpx_id)
                result_path = file_manager.get_path(docx_id)
            except Exception as e:
                mlog("generate", success=False, output_format="docx", field_count=len(req.replacements), error=str(e))
                raise HTTPException(status_code=500, detail=f"DOCX 변환 실패: {e}")
        else:
            result_path = out_path

        # 치환 커버리지 측정
        cov_detail = ""
        coverage_data = {}
        try:
            v = validate_result(path, out_path, replacements=formatted_replacements)
            coverage_data = v
            cov_detail = f"coverage={v['coverage_pct']:.1f}%, replaced={v['replaced']}/{v['total_originals']}, remaining={v['remaining']}"
        except Exception as ve:
            cov_detail = f"coverage_check_failed: {ve}"

    mlog("generate", success=True, output_format=fmt, field_count=len(req.replacements),
         duration_ms=t.ms, detail=cov_detail)

    # 문서 완성 보상 (로그인 사용자만)
    if authorization and authorization.startswith("Bearer "):
        try:
            token = authorization.split(" ", 1)[1]
            user = await auth_service.get_user_from_token(token)
            if user:
                await credit_service.on_doc_complete(user.id)
        except Exception:
            pass  # 보상 실패해도 다운로드는 정상 진행

    filename = f"EazyHWPX_result.{fmt}"
    response = FileResponse(result_path, filename=filename, media_type="application/octet-stream")
    # 커버리지 정보를 응답 헤더에 포함 (프론트엔드에서 읽기 가능)
    if coverage_data:
        response.headers["X-Coverage-Pct"] = f"{coverage_data.get('coverage_pct', 0):.1f}"
        response.headers["X-Coverage-Replaced"] = str(coverage_data.get('replaced', 0))
        response.headers["X-Coverage-Total"] = str(coverage_data.get('total_originals', 0))
        response.headers["X-Coverage-Remaining"] = str(coverage_data.get('remaining', 0))
        response.headers["Access-Control-Expose-Headers"] = "X-Coverage-Pct, X-Coverage-Replaced, X-Coverage-Total, X-Coverage-Remaining"
    return response
