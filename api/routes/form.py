"""양식 분석 + 문서 생성 API"""

import os
import tempfile

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.services.file_manager import file_manager
from clone_form import extract_texts, clone as clone_hwpx

router = APIRouter()


_MAX_UPLOAD = 100 * 1024 * 1024  # 100MB


@router.post("/analyze")
async def analyze_form(file: UploadFile = File(...)):
    # 파일 크기 검사
    content = await file.read()
    if len(content) > _MAX_UPLOAD:
        raise HTTPException(status_code=413, detail="파일이 너무 큽니다. 100MB 이하만 가능합니다.")
    await file.seek(0)

    file_id = await file_manager.save_upload(file)

    # HWP이면 HWPX로 변환
    path = file_manager.get_path(file_id)
    if path and path.lower().endswith(".hwp"):
        try:
            file_id = file_manager.convert_hwp(file_id)
        except RuntimeError as e:
            raise HTTPException(status_code=400, detail=str(e))

    path = file_manager.get_path(file_id)
    texts = extract_texts(path)
    if not texts:
        raise HTTPException(status_code=400, detail="텍스트를 추출할 수 없습니다.")

    warning = None
    if len(texts) > 3000:
        warning = f"문서가 매우 큽니다 ({len(texts)}개 필드). AI 매핑 시 최대 3000개까지만 처리되며, 시간이 오래 걸릴 수 있습니다."

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
    output_format: str = "hwpx"  # "hwpx" 또는 "hwp"


@router.post("/generate")
def generate_form(req: GenerateRequest):
    path = file_manager.get_path(req.file_id)
    if not path:
        raise HTTPException(status_code=404, detail="양식 파일을 찾을 수 없습니다. 다시 분석해주세요.")

    out_path = os.path.join(tempfile.mkdtemp(), "EazyHWPX_result.hwpx")
    clone_hwpx(path, out_path, replacements=req.replacements, strip_images=req.strip_images)

    # HWP 형식 요청 시 변환
    if req.output_format.lower() == "hwp":
        try:
            hwpx_id = file_manager.save(out_path, "result.hwpx")
            hwp_id = file_manager.convert_to_hwp(hwpx_id)
            hwp_path = file_manager.get_path(hwp_id)
            return FileResponse(
                hwp_path,
                filename="EazyHWPX_result.hwp",
                media_type="application/octet-stream",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"HWP 변환 실패: {e}")

    return FileResponse(
        out_path,
        filename="EazyHWPX_result.hwpx",
        media_type="application/octet-stream",
    )
