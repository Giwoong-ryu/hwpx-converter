"""문서 합치기 API"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from typing import List

from api.services.file_manager import file_manager
from api.services.metrics import log as mlog, Timer
from features import merge_documents

router = APIRouter()


@router.post("/")
async def merge_docs(files: List[UploadFile] = File(...)):
    if len(files) < 2:
        mlog("merge", success=False, error="파일 2개 미만")
        raise HTTPException(status_code=400, detail="최소 2개 파일이 필요합니다.")

    with Timer() as t:
        paths = []
        for f in files:
            fid = await file_manager.save_upload(f)
            p = file_manager.get_path(fid)
            # HWP만 변환, DOCX는 그대로 전달 (features.py에서 네이티브 처리)
            if p and p.lower().endswith(".hwp"):
                try:
                    fid = file_manager.convert_hwp(fid)
                except Exception as e:
                    raise HTTPException(status_code=400, detail=str(e))
            paths.append(file_manager.get_path(fid))

        out, cnt, err = merge_documents(paths)

    if err:
        mlog("merge", success=False, field_count=len(paths), duration_ms=t.ms, error=err)
        raise HTTPException(status_code=400, detail=err)

    # 결과 파일 형식에 맞는 이름과 MIME 타입
    filename = "DocFlow_merged.docx" if out.endswith(".docx") else "DocFlow_merged.hwpx"
    mlog("merge", success=True, field_count=cnt, duration_ms=t.ms, detail=f"files={len(paths)}")
    return FileResponse(out, filename=filename, media_type="application/octet-stream")
