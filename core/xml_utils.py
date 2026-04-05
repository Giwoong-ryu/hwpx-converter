"""
HWPX XML 공통 유틸리티
ID 생성, XML 이스케이프, 스타일 매핑 함수
"""
import os
import threading
from pathlib import Path

# 프로젝트 루트 기준 경로 (hwpx-converter/)
SKILL_DIR = str(Path(__file__).resolve().parent.parent)

# ═══ 색상 단일 소스 ═══
COLORS = {
    "header_bg": ("#D6DCE4", "#D9DEE4", "#DAE0E7"),  # 밝은 회색 헤더
    "dark_header": ("#2B4C7E", "#2D4F82", "#1F3864", "#333399"),  # 어두운 파란 헤더
    "light_gray": ("#F2F2F2", "#EDEDED", "#E8E8E8", "#D9D9D9"),  # 밝은 배경
    "white": ("#FFFFFF",),
    "black": ("#000000",),
}

# === ID 생성기 (스레드 안전) ===
_id_local = threading.local()
_ID_START = 2000000000


def next_id():
    if not hasattr(_id_local, "counter"):
        _id_local.counter = _ID_START
    _id_local.counter += 1
    return str(_id_local.counter)


def reset_id_counter():
    """ID 카운터 초기화 (요청별 호출)"""
    _id_local.counter = _ID_START


def esc(text):
    """XML 특수문자 이스케이프"""
    if not text:
        return ""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))


def color_to_charpr(color, bold=False, size_pt=10):
    """색상/스타일 -> charPr ID 매핑 (report 템플릿 기준)"""
    if color and color.upper() not in (*COLORS["black"], *COLORS["white"], ""):
        return 10
    if bold and size_pt >= 18:
        return 7
    if bold and size_pt >= 13:
        return 8
    if bold:
        return 9
    if size_pt <= 8:
        return 11
    return 0


def style_to_bf(bg_color, is_header=False):
    """배경색 -> borderFill ID 매핑"""
    if not bg_color or bg_color.upper() in (*COLORS["white"], ""):
        if is_header:
            return 7
        return 3
    bg = bg_color.upper()
    if bg in COLORS["header_bg"]:
        return 7
    if bg in COLORS["dark_header"]:
        return 8
    if bg in COLORS["light_gray"]:
        return 6
    return 6


def gen_cell(cell_data, total_width, col_widths):
    """셀 데이터 -> XML"""
    col = cell_data.get("col", 0)
    row = cell_data.get("row", 0)
    colspan = cell_data.get("colspan", 1)
    rowspan = cell_data.get("rowspan", 1)

    style = cell_data.get("style", {})
    bold = style.get("bold", False)
    size = style.get("font_size_pt", 10)
    text_color = style.get("text_color", "#000000")
    bg_color = style.get("bg_color", "")
    align = style.get("align", "CENTER")
    valign = style.get("valign", "CENTER")
    is_hdr = style.get("is_header", False)

    char_pr = color_to_charpr(text_color, bold, size)
    bf = style_to_bf(bg_color, is_hdr)

    end_col = min(col + colspan, len(col_widths))
    width = sum(col_widths[col:end_col]) or col_widths[-1]
    _text = cell_data.get("text", "")
    text_lines = max(1, _text.count('\n') + 1) if _text else 1
    height_per_line = max(1800, text_lines * 400)
    height = max(1800 * rowspan, height_per_line)

    para_map = {"CENTER": 21, "LEFT": 22, "RIGHT": 23}
    para_pr = para_map.get(align, 22)

    lines = cell_data.get("lines", [])
    text = cell_data.get("text", "")
    cell_paras = cell_data.get("cell_paragraphs", [])

    if cell_paras:
        paras = ""
        for cp in cell_paras:
            cp_text = cp.get("text", "")
            cp_bold = cp.get("bold", False)
            cp_color = cp.get("text_color", "#000000")
            cp_size = cp.get("font_size_pt", 10)
            cp_align = cp.get("align", "LEFT")
            cp_cpr = color_to_charpr(cp_color, cp_bold, cp_size)
            cp_ppr = {"CENTER": 21, "LEFT": 22, "RIGHT": 23}.get(cp_align, 22)
            paras += f'''
            <hp:p paraPrIDRef="{cp_ppr}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0" id="{next_id()}">
              <hp:run charPrIDRef="{cp_cpr}"><hp:t>{esc(cp_text)}</hp:t></hp:run>
            </hp:p>'''
        return f'''        <hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="1" borderFillIDRef="{bf}">
          <hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="TOP"
                     linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0"
                     hasTextRef="0" hasNumRef="0">{paras}
          </hp:subList>
          <hp:cellAddr colAddr="{col}" rowAddr="{row}"/>
          <hp:cellSpan colSpan="{colspan}" rowSpan="{rowspan}"/>
          <hp:cellSz width="{width}" height="{height}"/>
          <hp:cellMargin left="142" right="142" top="71" bottom="71"/>
        </hp:tc>'''
    elif lines and len(lines) > 1:
        paras = ""
        for line in lines:
            paras += f'''
            <hp:p paraPrIDRef="{para_pr}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0" id="{next_id()}">
              <hp:run charPrIDRef="{char_pr}"><hp:t>{esc(line)}</hp:t></hp:run>
            </hp:p>'''
        return f'''        <hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="1" borderFillIDRef="{bf}">
          <hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="{valign}"
                     linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0"
                     hasTextRef="0" hasNumRef="0">{paras}
          </hp:subList>
          <hp:cellAddr colAddr="{col}" rowAddr="{row}"/>
          <hp:cellSpan colSpan="{colspan}" rowSpan="{rowspan}"/>
          <hp:cellSz width="{width}" height="{height}"/>
          <hp:cellMargin left="142" right="142" top="71" bottom="71"/>
        </hp:tc>'''
    else:
        return f'''        <hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="1" borderFillIDRef="{bf}">
          <hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="{valign}"
                     linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0"
                     hasTextRef="0" hasNumRef="0">
            <hp:p paraPrIDRef="{para_pr}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0" id="{next_id()}">
              <hp:run charPrIDRef="{char_pr}"><hp:t>{esc(text)}</hp:t></hp:run>
            </hp:p>
          </hp:subList>
          <hp:cellAddr colAddr="{col}" rowAddr="{row}"/>
          <hp:cellSpan colSpan="{colspan}" rowSpan="{rowspan}"/>
          <hp:cellSz width="{width}" height="{height}"/>
          <hp:cellMargin left="142" right="142" top="71" bottom="71"/>
        </hp:tc>'''
