"""AI 자동 매핑 API"""

import traceback

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional

from api.services.file_manager import file_manager
from ai_mapper import map_content

router = APIRouter()


@router.post("/map")
async def ai_map(
    file_id: str = Form(...),
    text: Optional[str] = Form(None),
    content_file: Optional[UploadFile] = File(None),
):
    path = file_manager.get_path(file_id)
    if not path:
        raise HTTPException(status_code=404, detail="양식 파일을 찾을 수 없습니다. 다시 분석해주세요.")

    try:
        from clone_form import extract_texts
        fields = extract_texts(path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"양식 분석 실패: {e}")

    content_path = None
    if content_file and content_file.filename:
        try:
            cid = await file_manager.save_upload(content_file)
            content_path = file_manager.get_path(cid)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"파일 업로드 실패: {e}")

    try:
        print(f"[ai/map] fields={len(fields)}, text_len={len(text or '')}, content_path={content_path}")
        result, error = map_content(fields, text or "", content_path)
        print(f"[ai/map] result={'OK' if result else 'None'}, error={error}")
    except Exception as e:
        import traceback as tb
        err_msg = tb.format_exc()
        print(f"[ai/map] EXCEPTION: {err_msg}")
        # 로그 파일에도 기록
        with open("ai_error.log", "a", encoding="utf-8") as f:
            f.write(f"\n{'='*50}\n{err_msg}\n")
        raise HTTPException(status_code=500, detail=f"AI 처리 중 오류: {e}")

    if error:
        raise HTTPException(status_code=400, detail=error)

    return {
        "mapping_count": len(result),
        "mappings": result,
    }
