"""정기 문서 생성 API"""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.services.file_manager import file_manager
from api.services.metrics import log as mlog, Timer
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
        mlog("periodic", success=False, error="파일 없음")
        raise HTTPException(status_code=404, detail="양식 파일을 찾을 수 없습니다.")

    try:
        sd = datetime.strptime(req.start.strip(), "%Y-%m-%d")
        ed = datetime.strptime(req.end.strip(), "%Y-%m-%d")
    except ValueError:
        mlog("periodic", success=False, error="날짜 형식 오류")
        raise HTTPException(status_code=400, detail="날짜 형식: YYYY-MM-DD")

    with Timer() as t:
        zp, cnt, err = generate_periodic(path, req.date_text.strip(), sd, ed, req.interval, req.date_format.strip())

    if err:
        mlog("periodic", success=False, duration_ms=t.ms, error=err)
        raise HTTPException(status_code=400, detail=err)

    mlog("periodic", success=True, field_count=cnt, duration_ms=t.ms, detail=req.interval)
    return FileResponse(zp, filename="DocFlow_periodic.zip", media_type="application/zip")
