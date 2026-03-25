"""정기 문서 생성 API"""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.services.file_manager import file_manager
from features import generate_periodic

router = APIRouter()


class PeriodicRequest(BaseModel):
    file_id: str
    date_text: str
    start: str
    end: str
    interval: str = "monthly"
    date_format: str = "%Y.%m.%d"


@router.post("/generate")
def periodic_gen(req: PeriodicRequest):
    path = file_manager.get_path(req.file_id)
    if not path:
        raise HTTPException(status_code=404, detail="양식 파일을 찾을 수 없습니다.")

    try:
        sd = datetime.strptime(req.start.strip(), "%Y-%m-%d")
        ed = datetime.strptime(req.end.strip(), "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="날짜 형식: YYYY-MM-DD")

    zp, cnt, err = generate_periodic(path, req.date_text.strip(), sd, ed, req.interval, req.date_format.strip())
    if err:
        raise HTTPException(status_code=400, detail=err)

    return FileResponse(zp, filename="DocFlow_periodic.zip", media_type="application/zip")
