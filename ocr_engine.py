"""
OCR 엔진 모듈
PaddleOCR (기본, API 불필요) + Gemini Vision (선택, API 필요)
이미지 -> 구조 JSON 변환
"""
import json
import os
import sys
import tempfile
from pathlib import Path


def ocr_with_paddle(image_path: str) -> dict:
    """PaddleOCR로 이미지 텍스트 추출 -> 구조 JSON"""
    from paddleocr import PaddleOCR

    ocr = PaddleOCR(use_angle_cls=True, lang='korean', show_log=False)
    result = ocr.ocr(image_path, cls=True)

    if not result or not result[0]:
        return {
            "document": {"title": "OCR 결과 없음", "page_width_hu": 42520},
            "sections": [{"type": "paragraph", "content": "(텍스트를 인식하지 못했습니다)"}]
        }

    lines = result[0]

    # bbox 기반으로 행 그룹핑
    line_data = []
    for item in lines:
        bbox = item[0]
        text = item[1][0]
        confidence = item[1][1]

        x_min = min(p[0] for p in bbox)
        y_min = min(p[1] for p in bbox)
        x_max = max(p[0] for p in bbox)
        y_max = max(p[1] for p in bbox)

        line_data.append({
            "text": text,
            "confidence": confidence,
            "x": x_min,
            "y": y_min,
            "w": x_max - x_min,
            "h": y_max - y_min,
        })

    # Y좌표 기반 행 그룹핑
    Y_TOLERANCE = 15
    line_data.sort(key=lambda d: (d["y"], d["x"]))

    rows = []
    current_row = [line_data[0]]
    for item in line_data[1:]:
        if abs(item["y"] - current_row[0]["y"]) <= Y_TOLERANCE:
            current_row.append(item)
        else:
            rows.append(current_row)
            current_row = [item]
    rows.append(current_row)

    # 행 수와 열 패턴으로 테이블 vs 문단 판별
    col_counts = [len(row) for row in rows]
    avg_cols = sum(col_counts) / len(col_counts) if col_counts else 1
    is_table = avg_cols >= 2 and len(rows) >= 3

    if is_table:
        return _build_table_structure(rows)
    else:
        return _build_paragraph_structure(rows)


def _build_table_structure(rows: list) -> dict:
    """행/열 데이터 -> 테이블 구조 JSON"""
    n_rows = len(rows)
    n_cols = max(len(row) for row in rows)

    col_ratios = [round(100 / n_cols, 1)] * n_cols
    remainder = 100 - sum(col_ratios)
    col_ratios[-1] = round(col_ratios[-1] + remainder, 1)

    cells = []
    title = ""
    for ri, row in enumerate(rows):
        row.sort(key=lambda d: d["x"])
        for ci, item in enumerate(row):
            style = {"align": "CENTER" if ri == 0 else "LEFT"}
            if ri == 0:
                style["bold"] = True
                style["is_header"] = True
                if item["text"] and len(item["text"]) > len(title):
                    title = item["text"]

            cells.append({
                "row": ri,
                "col": ci,
                "text": item["text"],
                "style": style,
            })

    return {
        "document": {"title": title, "page_width_hu": 42520},
        "sections": [{
            "type": "table",
            "table": {
                "rows": n_rows,
                "cols": n_cols,
                "col_widths_ratio": col_ratios,
                "cells": cells,
            }
        }]
    }


def _build_paragraph_structure(rows: list) -> dict:
    """행 데이터 -> 문단 구조 JSON"""
    sections = []
    title = ""

    for ri, row in enumerate(rows):
        row.sort(key=lambda d: d["x"])
        text = " ".join(item["text"] for item in row)

        if ri == 0 and text:
            title = text
            sections.append({
                "type": "paragraph",
                "content": text,
                "align": "CENTER",
                "style": {"bold": True, "font_size_pt": 16}
            })
        else:
            sections.append({
                "type": "paragraph",
                "content": text,
                "align": "LEFT",
                "style": {}
            })

    return {
        "document": {"title": title, "page_width_hu": 42520},
        "sections": sections,
    }


def ocr_with_gemini(image_path: str, api_key: str) -> dict:
    """Gemini Vision API로 이미지 레이아웃 분석 -> 구조 JSON"""
    import base64
    import urllib.request
    import urllib.error

    ext = Path(image_path).suffix.lower()
    mime_map = {
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
    }
    mime = mime_map.get(ext, "image/png")

    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    prompt = """이 문서 이미지를 분석하여 HWPX 구조 JSON으로 변환하세요.

출력 형식:
{
  "document": {"title": "문서 제목", "page_width_hu": 42520},
  "sections": [
    {"type": "paragraph", "content": "텍스트", "align": "CENTER", "style": {"bold": true, "font_size_pt": 16}},
    {"type": "table", "table": {"rows": 3, "cols": 2, "col_widths_ratio": [50, 50], "cells": [
      {"row": 0, "col": 0, "text": "헤더1", "style": {"bold": true, "align": "CENTER", "is_header": true}},
      {"row": 0, "col": 1, "text": "헤더2", "style": {"bold": true, "align": "CENTER", "is_header": true}}
    ]}}
  ]
}

규칙:
1. 모든 텍스트를 빠짐없이 추출
2. 표는 table 타입으로, 일반 텍스트는 paragraph 타입으로
3. 병합 셀은 colspan/rowspan으로 표현
4. 배경색은 bg_color, 글자색은 text_color (hex)
5. 반드시 JSON만 출력"""

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    payload = json.dumps({
        "contents": [{"parts": [
            {"inlineData": {"mimeType": mime, "data": b64}},
            {"text": prompt}
        ]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 32768,
            "responseMimeType": "application/json"
        }
    }).encode("utf-8")

    req = urllib.request.Request(f"{url}?key={api_key}", data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("x-goog-api-key", api_key)

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise RuntimeError(f"Gemini API 오류 ({e.code}): {body[:300]}")

    try:
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except (KeyError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Gemini 응답 파싱 실패: {e}")


def process_image(image_path: str, engine: str = "paddle", api_key: str = "") -> dict:
    """이미지 -> 구조 JSON (엔진 선택)"""
    if engine == "gemini":
        if not api_key:
            raise ValueError("Gemini 엔진 사용 시 API 키가 필요합니다")
        return ocr_with_gemini(image_path, api_key)
    else:
        return ocr_with_paddle(image_path)
