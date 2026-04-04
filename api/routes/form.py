"""양식 분석 + 문서 생성 API"""

import os
import tempfile

from fastapi import APIRouter, HTTPException, UploadFile, File, Header
from typing import Optional
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.services.file_manager import file_manager
from api.services.metrics import log as mlog, Timer
from api.services import credit_service, auth_service
from clone_form import extract_texts, clone as clone_hwpx, validate_result

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

    return {
        "file_id": file_id,
        "filename": file.filename,
        "field_count": len(texts),
        "fields": texts,
        "warning": warning,
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

    fmt = req.output_format.lower()
    with Timer() as t:
        try:
            out_path = os.path.join(tempfile.mkdtemp(), "EazyHWPX_result.hwpx")
            clone_hwpx(path, out_path, replacements=req.replacements, strip_images=req.strip_images)
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
            v = validate_result(path, out_path, replacements=req.replacements)
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
