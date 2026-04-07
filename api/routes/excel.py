"""엑셀 양식 채우기 API"""

import json

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.services.file_manager import file_manager
from excel_filler import extract_excel_texts, fill_excel, batch_fill_excel

router = APIRouter()


@router.post("/analyze")
async def analyze_excel(file: UploadFile = File(...)):
    """엑셀 양식 분석 - 텍스트가 있는 셀 목록 반환"""
    fid = await file_manager.save_upload(file)
    path = file_manager.get_path(fid)
    texts = extract_excel_texts(path)
    return {
        "file_id": fid,
        "filename": file.filename,
        "cell_count": len(texts),
        "cells": texts,
    }


class ExcelFillRequest(BaseModel):
    file_id: str
    replacements: dict[str, str]


@router.post("/fill")
def fill_single(req: ExcelFillRequest):
    """엑셀 양식에 내용 채우기 (1건)"""
    path = file_manager.get_path(req.file_id)
    if not path:
        raise HTTPException(status_code=404, detail="엑셀 양식 파일을 찾을 수 없습니다.")

    out = fill_excel(path, req.replacements)
    return FileResponse(out, filename="DocFlow_excel_result.xlsx",
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.post("/batch")
async def batch_fill(
    file_id: str = Form(...),
    data_excel: UploadFile = File(...),
):
    """엑셀 양식 + 데이터 엑셀 → N개 생성"""
    path = file_manager.get_path(file_id)
    if not path:
        raise HTTPException(status_code=404, detail="엑셀 양식 파일을 찾을 수 없습니다.")

    did = await file_manager.save_upload(data_excel)
    data_path = file_manager.get_path(did)

    zp, cnt, err = batch_fill_excel(path, data_path)
    if err:
        raise HTTPException(status_code=400, detail=err)

    return FileResponse(zp, filename="DocFlow_excel_batch.zip", media_type="application/zip")


@router.post("/map-and-batch")
async def map_and_batch(
    file_id: str = Form(...),
    data_excel: UploadFile = File(...),
):
    """엑셀 양식 + 데이터 엑셀 → AI 헤더 매핑 → N개 생성"""
    path = file_manager.get_path(file_id)
    if not path:
        raise HTTPException(status_code=404, detail="엑셀 양식 파일을 찾을 수 없습니다.")

    did = await file_manager.save_upload(data_excel)
    data_path = file_manager.get_path(did)

    # 양식 텍스트 추출
    form_texts = extract_excel_texts(path)
    form_values = [t["value"] for t in form_texts]

    # 데이터 엑셀 헤더 읽기
    import openpyxl
    wb = openpyxl.load_workbook(data_path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if len(rows) < 2:
        raise HTTPException(status_code=400, detail="데이터 엑셀에 최소 2행이 필요합니다.")

    headers = [str(h).strip() if h else "" for h in rows[0]]
    sample = [str(v).strip() if v else "" for v in rows[1]]

    # AI 매핑
    from ai_mapper import _get_api_key, _parse_json_response
    from google import genai
    from google.genai import types

    api_key = _get_api_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY가 설정되지 않았습니다.")

    prompt = f"""엑셀 양식의 셀 값 목록과 데이터 엑셀의 헤더+샘플이 있습니다.
각 데이터 헤더가 양식의 어떤 셀 값에 해당하는지 매핑해주세요.

양식 셀 값 (일부): {json.dumps(form_values[:30], ensure_ascii=False)}
데이터 헤더: {json.dumps(headers, ensure_ascii=False)}
데이터 샘플: {json.dumps(sample, ensure_ascii=False)}

JSON 배열로 응답: [{{"header": "데이터헤더", "form_text": "양식에서 매칭되는 셀값"}}]
매칭 안 되는 헤더는 form_text를 빈 문자열로."""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1),
        )
        parsed = _parse_json_response(response.text)
        if isinstance(parsed, list):
            mappings = parsed
        elif isinstance(parsed, dict):
            mappings = parsed.get("mappings", [])
        else:
            mappings = []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 매핑 실패: {e}")

    return {
        "excel_id": did,
        "headers": headers,
        "sample": sample,
        "row_count": len(rows) - 1,
        "mappings": mappings,
    }
