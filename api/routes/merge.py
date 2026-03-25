"""문서 합치기 API"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from typing import List

from api.services.file_manager import file_manager
from features import merge_documents

router = APIRouter()


@router.post("/")
async def merge_docs(files: List[UploadFile] = File(...)):
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="최소 2개 파일이 필요합니다.")

    paths = []
    for f in files:
        fid = await file_manager.save_upload(f)
        paths.append(file_manager.get_path(fid))

    out, cnt, err = merge_documents(paths)
    if err:
        raise HTTPException(status_code=400, detail=err)

    return FileResponse(out, filename="DocFlow_merged.hwpx", media_type="application/octet-stream")
