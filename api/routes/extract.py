"""내용 뽑기 API"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from typing import List

from api.services.file_manager import file_manager
from api.services.metrics import log as mlog, Timer
from features import extract_to_excel

router = APIRouter()


@router.post("/")
async def extract_data(files: List[UploadFile] = File(...)):
    with Timer() as t:
        paths = []
        for f in files:
            fid = await file_manager.save_upload(f)
            p = file_manager.get_path(fid)
            # DOCX는 변환 없이 그대로 전달 (features.py에서 네이티브 처리)
            if p and p.lower().endswith(".hwp"):
                try:
                    fid = file_manager.convert_hwp(fid)
                except Exception as e:
                    raise HTTPException(status_code=400, detail=str(e))
            paths.append(file_manager.get_path(fid))

        ep, cnt, err = extract_to_excel(paths)

    if err:
        mlog("extract", success=False, field_count=len(paths), duration_ms=t.ms, error=err)
        raise HTTPException(status_code=400, detail=err)

    mlog("extract", success=True, field_count=cnt, duration_ms=t.ms, detail=f"files={len(paths)}")
    return FileResponse(ep, filename="DocFlow_extracted.xlsx",
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
