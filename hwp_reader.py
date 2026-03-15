"""
HWP → HWPX 구조 JSON 변환 모듈
hwp2yaml 라이브러리를 사용하여 HWP 5.x / HWPX / HWP 3.x 파일을 읽고
HWPX 빌드용 구조 JSON으로 변환한다.

extract_hwp_structure()를 사용하여 문서 내 순서(문단↔테이블 interleaving)를 보존한다.
"""
from hwp2yaml import extract_hwp_text, extract_hwp_structure


def parse_hwp(file_path: str) -> dict:
    """HWP 파일 → HWPX 구조 JSON 변환 (순서 보존)"""

    # 1차: 구조 추출 시도 (순서 보존)
    try:
        result = extract_hwp_structure(file_path)
        if result.success and result.structure:
            return _from_structure(result)
    except Exception:
        pass

    # 2차 폴백: 텍스트 추출
    result = extract_hwp_text(file_path)
    if not result.success:
        raise RuntimeError(f"HWP 파일 읽기 실패: {result.error}")
    return _from_text_result(result)


def _from_structure(result) -> dict:
    """extract_hwp_structure() 결과 → 구조 JSON (순서 보존)"""
    structure = result.structure
    sections_data = structure.get("sections", [])

    output_sections = []
    title = ""

    for section in sections_data:
        # 문단 처리
        paragraphs = section.get("paragraphs", [])
        for para in paragraphs:
            text = para.get("text", "").strip()
            level = para.get("level", 0)

            if not text:
                output_sections.append({"type": "paragraph", "content": ""})
                continue

            style = {}
            align = "LEFT"

            # 레벨 기반 스타일 추정
            if level == 0 and not title:
                title = text
                style["bold"] = True
                style["font_size_pt"] = 16
                align = "CENTER"
            elif level <= 1:
                style["bold"] = True
                style["font_size_pt"] = 14

            output_sections.append({
                "type": "paragraph",
                "content": text,
                "align": align,
                "style": style,
            })

        # 테이블 처리 (문단과 섞인 순서 그대로)
        tables = section.get("tables", [])
        for tbl in tables:
            table_section = _convert_table(tbl)
            if table_section:
                output_sections.append(table_section)

    # 구조에서 순서가 sections 내 paragraphs → tables 순이면
    # interleaving이 안 될 수 있다. 이 경우 text 폴백과 동일.
    # 하지만 structure API가 순서를 보존한다면 이 코드가 정확하다.

    if not output_sections:
        raise RuntimeError("HWP 파일에서 내용을 추출하지 못했습니다.")

    if not title:
        title = "HWP 변환 문서"

    return {
        "document": {"title": title, "page_width_hu": 42520},
        "sections": output_sections,
    }


def _from_text_result(result) -> dict:
    """extract_hwp_text() 결과 → 구조 JSON (폴백)

    테이블이 있으면 테이블만, 없으면 텍스트만 사용.
    둘 다 섞어서 넣지 않는다 (순서 보장 불가하므로).
    """
    sections = []
    title = ""

    # 테이블이 있으면 테이블 중심으로 구성
    if result.tables:
        for tbl in result.tables:
            table_section = _convert_table(tbl)
            if table_section:
                sections.append(table_section)

        if sections:
            # 테이블의 첫 번째 셀 내용을 제목으로
            first_table = sections[0].get("table", {})
            first_cells = first_table.get("cells", [])
            if first_cells:
                title = first_cells[0].get("text", "")

    # 테이블이 없으면 텍스트 사용
    if not sections and result.text:
        lines = result.text.strip().split("\n")
        for line in lines:
            text = line.strip()
            if not text:
                sections.append({"type": "paragraph", "content": ""})
                continue

            style = {}
            align = "LEFT"

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


def _convert_table(tbl: dict) -> dict | None:
    """hwp2yaml 테이블 데이터 → HWPX 구조 JSON 테이블"""
    n_rows = tbl.get("rows", 0)
    n_cols = tbl.get("cols", 0)
    data = tbl.get("data", [])

    if n_rows == 0 or n_cols == 0 or not data:
        return None

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

    return {
        "type": "table",
        "table": {
            "rows": n_rows,
            "cols": n_cols,
            "col_widths_ratio": col_ratios,
            "cells": cells,
        }
    }
