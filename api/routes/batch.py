"""대량 생성 API - 엑셀 헤더 AI 매핑 + 대량 생성"""

import json
import os
import tempfile
import zipfile

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.services.file_manager import file_manager
from api.services.metrics import log as mlog, Timer
from clone_form import extract_texts, clone as clone_hwpx

router = APIRouter()


@router.post("/map-headers")
async def map_excel_headers(
    file_id: str = Form(...),
    excel: UploadFile = File(...),
):
    """엑셀 헤더와 양식 텍스트를 AI로 매핑"""
    form_path = file_manager.get_path(file_id)
    if not form_path:
        raise HTTPException(status_code=404, detail="양식 파일을 찾을 수 없습니다.")

    eid = await file_manager.save_upload(excel)
    excel_path = file_manager.get_path(eid)

    # 엑셀 헤더 읽기
    import openpyxl
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 2:
        raise HTTPException(status_code=400, detail="엑셀에 최소 2행(헤더 + 데이터)이 필요합니다.")

    headers = [str(h).strip() if h else "" for h in rows[0]]
    sample_row = [str(v).strip() if v else "" for v in rows[1]]
    row_count = len(rows) - 1

    # 양식 텍스트
    form_texts = extract_texts(form_path)

    # AI로 헤더 ↔ 양식 텍스트 매핑
    from ai_mapper import _get_api_key, _parse_json_response
    import google.generativeai as genai

    api_key = _get_api_key()
    if not api_key:
        raise HTTPException(status_code=500, detail="AI 서비스 설정에 문제가 있습니다. 관리자에게 문의해주세요.")

    prompt = f"""양식 문서의 텍스트 목록과 엑셀의 헤더+샘플 데이터가 있습니다.
각 엑셀 헤더가 양식의 어떤 텍스트에 해당하는지 매핑해주세요.

양식 텍스트 (일부):
{json.dumps(form_texts[:50], ensure_ascii=False)}

엑셀 헤더: {json.dumps(headers, ensure_ascii=False)}
엑셀 샘플 (1행): {json.dumps(sample_row, ensure_ascii=False)}

JSON 배열로 응답: [{{"header": "엑셀헤더", "form_text": "양식에서 매칭되는 텍스트"}}]
매칭 안 되는 헤더는 form_text를 빈 문자열로.
"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt, generation_config=genai.GenerationConfig(temperature=0.1))
        parsed = _parse_json_response(response.text)
        if isinstance(parsed, list):
            mappings = parsed
        elif isinstance(parsed, dict):
            mappings = parsed.get("mappings", parsed.get("매핑", []))
        else:
            mappings = []
    except Exception as e:
        raise HTTPException(status_code=500, detail="AI 매핑 처리 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.")

    return {
        "excel_id": eid,
        "headers": headers,
        "sample_row": sample_row,
        "row_count": row_count,
        "mappings": mappings,
    }


class BatchGenerateRequest(BaseModel):
    file_id: str
    excel_id: str
    column_mappings: list  # [{"header": "이름", "form_text": "홍길동"}, ...]


@router.post("/generate-mapped")
def batch_generate_mapped(req: BatchGenerateRequest):
    """AI 매핑 결과를 기반으로 대량 생성"""
    form_path = file_manager.get_path(req.file_id)
    if not form_path:
        raise HTTPException(status_code=404, detail="양식 파일을 찾을 수 없습니다.")

    excel_path = file_manager.get_path(req.excel_id)
    if not excel_path:
        raise HTTPException(status_code=404, detail="엑셀 파일을 찾을 수 없습니다.")

    # 매핑 테이블: header_index -> form_text
    import openpyxl
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    headers = [str(h).strip() if h else "" for h in rows[0]]

    header_to_form = {}
    for m in req.column_mappings:
        h = m.get("header", "")
        ft = m.get("form_text", "")
        if h and ft:
            header_to_form[h] = ft

    out_dir = tempfile.mkdtemp()
    generated = []

    for i, row in enumerate(rows[1:], start=1):
        replacements = {}
        for j, val in enumerate(row):
            if j < len(headers) and headers[j] in header_to_form and val is not None:
                form_text = header_to_form[headers[j]]
                replacements[form_text] = str(val).strip()

        if not replacements:
            continue

        first_val = str(row[0]).strip() if row[0] else f"문서_{i}"
        safe_name = "".join(c for c in first_val if c not in r'\/:*?"<>|')[:50]
        out_path = os.path.join(out_dir, f"{safe_name}.hwpx")
        if os.path.exists(out_path):
            out_path = os.path.join(out_dir, f"{safe_name}_{i}.hwpx")

        clone_hwpx(form_path, out_path, replacements=replacements)
        generated.append(out_path)

    if not generated:
        mlog("batch", success=False, error="생성할 데이터 없음")
        raise HTTPException(status_code=400, detail="생성할 데이터가 없습니다.")

    zip_path = os.path.join(tempfile.mkdtemp(), "DocFlow_batch.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fp in generated:
            zf.write(fp, os.path.basename(fp))

    mlog("batch", success=True, field_count=len(generated), detail=f"docs={len(generated)}")
    return FileResponse(zip_path, filename="DocFlow_batch.zip", media_type="application/zip")


# 기존 API도 유지 (하위 호환)
@router.post("/generate")
async def batch_gen(
    file_id: str = Form(...),
    excel: UploadFile = File(...),
):
    from features import batch_generate
    path = file_manager.get_path(file_id)
    if not path:
        raise HTTPException(status_code=404, detail="양식 파일을 찾을 수 없습니다.")
    eid = await file_manager.save_upload(excel)
    excel_path = file_manager.get_path(eid)
    with Timer() as t:
        zp, cnt, err = batch_generate(path, excel_path)
    if err:
        mlog("batch_legacy", success=False, duration_ms=t.ms, error=err)
        raise HTTPException(status_code=400, detail=err)
    mlog("batch_legacy", success=True, field_count=cnt, duration_ms=t.ms)
    return FileResponse(zp, filename="DocFlow_batch.zip", media_type="application/zip")
