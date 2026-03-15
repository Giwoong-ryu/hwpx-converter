"""
HWP → HWPX 구조 JSON 변환 모듈
hwp2yaml 라이브러리를 사용하여 HWP 5.x / HWPX / HWP 3.x 파일을 읽고
HWPX 빌드용 구조 JSON으로 변환한다.
"""
from hwp2yaml import extract_hwp_text


def parse_hwp(file_path: str) -> dict:
    """HWP 파일 → HWPX 구조 JSON 변환"""
    result = extract_hwp_text(file_path)

    if not result.success:
        raise RuntimeError(f"HWP 파일 읽기 실패: {result.error}")

    sections = []
    title = ""

    # 테이블 추출
    if result.tables:
        for tbl in result.tables:
            n_rows = tbl.get("rows", 0)
            n_cols = tbl.get("cols", 0)
            data = tbl.get("data", [])

            if n_rows == 0 or n_cols == 0 or not data:
                continue

            col_ratios = [round(100 / n_cols, 1)] * n_cols
            remainder = 100 - sum(col_ratios)
            col_ratios[-1] = round(col_ratios[-1] + remainder, 1)

            cells = []
            for ri, row in enumerate(data):
                for ci, cell_text in enumerate(row):
                    if ci >= n_cols:
                        break
                    cell_style = {"align": "LEFT"}
                    if ri == 0:
                        cell_style["bold"] = True
                        cell_style["align"] = "CENTER"
                        cell_style["is_header"] = True
                    cells.append({
                        "row": ri,
                        "col": ci,
                        "text": str(cell_text) if cell_text else "",
                        "style": cell_style,
                    })

            sections.append({
                "type": "table",
                "table": {
                    "rows": n_rows,
                    "cols": n_cols,
                    "col_widths_ratio": col_ratios,
                    "cells": cells,
                }
            })

    # 텍스트 추출 (테이블 외 문단)
    if result.text:
        lines = result.text.strip().split("\n")
        for i, line in enumerate(lines):
            text = line.strip()
            if not text:
                sections.append({"type": "paragraph", "content": ""})
                continue

            style = {}
            align = "LEFT"

            # 첫 번째 비어있지 않은 줄을 제목으로 추정
            if not title:
                title = text
                style["bold"] = True
                style["font_size_pt"] = 16
                align = "CENTER"

            sections.append({
                "type": "paragraph",
                "content": text,
                "align": align,
                "style": style,
            })

    if not sections:
        raise RuntimeError("HWP 파일에서 내용을 추출하지 못했습니다.")

    if not title:
        title = "HWP 변환 문서"

    return {
        "document": {"title": title, "page_width_hu": 42520},
        "sections": sections,
    }
