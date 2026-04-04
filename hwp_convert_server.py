"""HWP 변환 전용 서버 (Windows 로컬 PC에서 실행)

pyhwpx COM을 사용하여 HWP <-> HWPX 변환만 담당.
메인 API(Railway)에서 HTTP로 호출.

실행: uvicorn hwp_convert_server:app --host 0.0.0.0 --port 8001
"""

import os
import tempfile
import threading

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="HWP Convert Server")

_hwp_lock = threading.Lock()
_HWP_TIMEOUT = 30


def _com_convert(src_path: str, dst_path: str, dst_format: str):
    acquired = _hwp_lock.acquire(timeout=_HWP_TIMEOUT)
    if not acquired:
        raise RuntimeError("다른 변환 작업이 진행 중입니다.")
    try:
        import pythoncom
        pythoncom.CoInitialize()
        try:
            from pyhwpx import Hwp
            hwp = Hwp(visible=False, register_module=True)
            hwp.open(src_path)
            hwp.save_as(dst_path, dst_format)
            hwp.clear()
            hwp.quit()
        finally:
            pythoncom.CoUninitialize()
    finally:
        _hwp_lock.release()


@app.post("/convert")
async def convert_hwp_to_hwpx(file: UploadFile = File(...)):
    """HWP -> HWPX 변환"""
    if not file.filename.lower().endswith(".hwp"):
        raise HTTPException(400, "HWP 파일만 지원합니다.")

    tmp_dir = tempfile.mkdtemp()
    src = os.path.join(tmp_dir, file.filename)
    dst = os.path.join(tmp_dir, "converted.hwpx")

    content = await file.read()
    with open(src, "wb") as f:
        f.write(content)

    try:
        _com_convert(src, dst, "HWPX")
    except Exception as e:
        raise HTTPException(500, f"HWP 변환 실패: {e}")

    return FileResponse(
        dst,
        filename=file.filename.rsplit(".", 1)[0] + ".hwpx",
        media_type="application/octet-stream",
    )


@app.post("/convert-to-hwp")
async def convert_hwpx_to_hwp(file: UploadFile = File(...)):
    """HWPX -> HWP 변환"""
    if not file.filename.lower().endswith(".hwpx"):
        raise HTTPException(400, "HWPX 파일만 지원합니다.")

    tmp_dir = tempfile.mkdtemp()
    src = os.path.join(tmp_dir, file.filename)
    dst = os.path.join(tmp_dir, "converted.hwp")

    content = await file.read()
    with open(src, "wb") as f:
        f.write(content)

    try:
        _com_convert(src, dst, "HWP")
    except Exception as e:
        raise HTTPException(500, f"HWPX→HWP 변환 실패: {e}")

    return FileResponse(
        dst,
        filename=file.filename.rsplit(".", 1)[0] + ".hwp",
        media_type="application/octet-stream",
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "hwp-convert"}
