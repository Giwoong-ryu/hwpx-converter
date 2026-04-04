"""도장 삽입 API"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse

from api.services.file_manager import file_manager
from api.services.metrics import log as mlog, Timer
from features import insert_stamp

router = APIRouter()


@router.post("/insert")
async def stamp_insert(
    file_id: str = Form(...),
    image: UploadFile = File(...),
    target_text: str = Form("(인)"),
):
    path = file_manager.get_path(file_id)
    if not path:
        mlog("stamp", success=False, error="파일 없음")
        raise HTTPException(status_code=404, detail="양식 파일을 찾을 수 없습니다.")

    iid = await file_manager.save_upload(image)
    img_path = file_manager.get_path(iid)

    with Timer() as t:
        out, err = insert_stamp(path, img_path, target_text.strip())

    if err:
        mlog("stamp", success=False, duration_ms=t.ms, error=err)
        raise HTTPException(status_code=400, detail=err)

    mlog("stamp", success=True, duration_ms=t.ms, detail=f"target={target_text.strip()}")
    return FileResponse(out, filename="DocFlow_stamped.hwpx", media_type="application/octet-stream")
