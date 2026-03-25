"""내용 뽑기 API"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from typing import List

from api.services.file_manager import file_manager
from features import extract_to_excel

router = APIRouter()


@router.post("/")
async def extract_data(files: List[UploadFile] = File(...)):
    paths = []
    for f in files:
        fid = await file_manager.save_upload(f)
        paths.append(file_manager.get_path(fid))

    ep, cnt, err = extract_to_excel(paths)
    if err:
        raise HTTPException(status_code=400, detail=err)

    return FileResponse(ep, filename="DocFlow_extracted.xlsx",
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
