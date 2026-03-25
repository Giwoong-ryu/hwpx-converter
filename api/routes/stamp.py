"""도장 삽입 API"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse

from api.services.file_manager import file_manager
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
        raise HTTPException(status_code=404, detail="양식 파일을 찾을 수 없습니다.")

    iid = await file_manager.save_upload(image)
    img_path = file_manager.get_path(iid)

    out, err = insert_stamp(path, img_path, target_text.strip())
    if err:
        raise HTTPException(status_code=400, detail=err)

    return FileResponse(out, filename="DocFlow_stamped.hwpx", media_type="application/octet-stream")
