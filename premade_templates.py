"""
프리메이드 템플릿 라이브러리
공통 업무 양식을 {{플레이스홀더}} 포함하여 제공
사용자는 값만 입력하면 됨
"""

TEMPLATES = {
    "gonmun": {
        "name": "공문",
        "description": "관공서/회사 공식 공문 양식",
        "fields": ["문서번호", "수신", "참조", "제목", "내용", "발신부서", "발신자", "날짜"],
        "structure": {
            "document": {"title": "공문", "page_width_hu": 42520},
            "sections": [
                {"type": "paragraph", "content": "{{제목}}", "align": "CENTER",
                 "style": {"bold": True, "font_size_pt": 18}},
                {"type": "paragraph", "content": ""},
                {"type": "table", "table": {
                    "rows": 4, "cols": 2, "col_widths_ratio": [25, 75],
                    "cells": [
                        {"row": 0, "col": 0, "text": "문서번호", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 0, "col": 1, "text": "{{문서번호}}", "style": {"align": "LEFT"}},
                        {"row": 1, "col": 0, "text": "수신", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 1, "col": 1, "text": "{{수신}}", "style": {"align": "LEFT"}},
                        {"row": 2, "col": 0, "text": "참조", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 2, "col": 1, "text": "{{참조}}", "style": {"align": "LEFT"}},
                        {"row": 3, "col": 0, "text": "날짜", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 3, "col": 1, "text": "{{날짜}}", "style": {"align": "LEFT"}},
                    ]
                }},
                {"type": "paragraph", "content": ""},
                {"type": "paragraph", "content": "{{내용}}", "align": "LEFT", "style": {}},
                {"type": "paragraph", "content": ""},
                {"type": "paragraph", "content": "{{발신부서}}", "align": "RIGHT", "style": {"bold": True}},
                {"type": "paragraph", "content": "{{발신자}}", "align": "RIGHT", "style": {}},
            ]
        }
    },
    "meeting": {
        "name": "회의록",
        "description": "회의 내용 기록 양식",
        "fields": ["회의명", "일시", "장소", "참석자", "안건", "결정사항", "후속조치", "작성자"],
        "structure": {
            "document": {"title": "회의록", "page_width_hu": 42520},
            "sections": [
                {"type": "paragraph", "content": "회의록", "align": "CENTER",
                 "style": {"bold": True, "font_size_pt": 20}},
                {"type": "paragraph", "content": ""},
                {"type": "table", "table": {
                    "rows": 4, "cols": 2, "col_widths_ratio": [25, 75],
                    "cells": [
                        {"row": 0, "col": 0, "text": "회의명", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 0, "col": 1, "text": "{{회의명}}", "style": {"align": "LEFT"}},
                        {"row": 1, "col": 0, "text": "일시", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 1, "col": 1, "text": "{{일시}}", "style": {"align": "LEFT"}},
                        {"row": 2, "col": 0, "text": "장소", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 2, "col": 1, "text": "{{장소}}", "style": {"align": "LEFT"}},
                        {"row": 3, "col": 0, "text": "참석자", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 3, "col": 1, "text": "{{참석자}}", "style": {"align": "LEFT"}},
                    ]
                }},
                {"type": "paragraph", "content": ""},
                {"type": "paragraph", "content": "1. 안건", "align": "LEFT", "style": {"bold": True, "font_size_pt": 14}},
                {"type": "paragraph", "content": "{{안건}}", "align": "LEFT", "style": {}},
                {"type": "paragraph", "content": ""},
                {"type": "paragraph", "content": "2. 결정사항", "align": "LEFT", "style": {"bold": True, "font_size_pt": 14}},
                {"type": "paragraph", "content": "{{결정사항}}", "align": "LEFT", "style": {}},
                {"type": "paragraph", "content": ""},
                {"type": "paragraph", "content": "3. 후속조치", "align": "LEFT", "style": {"bold": True, "font_size_pt": 14}},
                {"type": "paragraph", "content": "{{후속조치}}", "align": "LEFT", "style": {}},
                {"type": "paragraph", "content": ""},
                {"type": "paragraph", "content": "작성자: {{작성자}}", "align": "RIGHT", "style": {}},
            ]
        }
    },
    "report": {
        "name": "업무보고서",
        "description": "업무 현황 보고 양식",
        "fields": ["제목", "보고일", "보고자", "부서", "현황", "성과", "계획", "비고"],
        "structure": {
            "document": {"title": "업무보고서", "page_width_hu": 42520},
            "sections": [
                {"type": "paragraph", "content": "{{제목}}", "align": "CENTER",
                 "style": {"bold": True, "font_size_pt": 20}},
                {"type": "paragraph", "content": ""},
                {"type": "table", "table": {
                    "rows": 3, "cols": 4, "col_widths_ratio": [15, 35, 15, 35],
                    "cells": [
                        {"row": 0, "col": 0, "text": "보고일", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 0, "col": 1, "text": "{{보고일}}", "style": {"align": "CENTER"}},
                        {"row": 0, "col": 2, "text": "부서", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 0, "col": 3, "text": "{{부서}}", "style": {"align": "CENTER"}},
                        {"row": 1, "col": 0, "text": "보고자", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 1, "col": 1, "text": "{{보고자}}", "style": {"align": "CENTER"}},
                        {"row": 1, "col": 2, "text": "비고", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 1, "col": 3, "text": "{{비고}}", "style": {"align": "CENTER"}},
                        {"row": 2, "col": 0, "text": "현황", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 2, "col": 1, "text": "{{현황}}", "style": {"align": "LEFT"}, "colspan": 3},
                    ]
                }},
                {"type": "paragraph", "content": ""},
                {"type": "paragraph", "content": "1. 성과", "align": "LEFT", "style": {"bold": True, "font_size_pt": 14}},
                {"type": "paragraph", "content": "{{성과}}", "align": "LEFT", "style": {}},
                {"type": "paragraph", "content": ""},
                {"type": "paragraph", "content": "2. 향후 계획", "align": "LEFT", "style": {"bold": True, "font_size_pt": 14}},
                {"type": "paragraph", "content": "{{계획}}", "align": "LEFT", "style": {}},
            ]
        }
    },
    "personnel": {
        "name": "인사발령통보서",
        "description": "인사 발령 통보 양식",
        "fields": ["성명", "사번", "현부서", "현직급", "발령부서", "발령직급", "발령일", "사유"],
        "structure": {
            "document": {"title": "인사발령통보서", "page_width_hu": 42520},
            "sections": [
                {"type": "paragraph", "content": "인사발령통보서", "align": "CENTER",
                 "style": {"bold": True, "font_size_pt": 22}},
                {"type": "paragraph", "content": ""},
                {"type": "table", "table": {
                    "rows": 6, "cols": 4, "col_widths_ratio": [20, 30, 20, 30],
                    "cells": [
                        {"row": 0, "col": 0, "text": "성명", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 0, "col": 1, "text": "{{성명}}", "style": {"align": "CENTER"}},
                        {"row": 0, "col": 2, "text": "사번", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 0, "col": 3, "text": "{{사번}}", "style": {"align": "CENTER"}},
                        {"row": 1, "col": 0, "text": "현 부서", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 1, "col": 1, "text": "{{현부서}}", "style": {"align": "CENTER"}},
                        {"row": 1, "col": 2, "text": "현 직급", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 1, "col": 3, "text": "{{현직급}}", "style": {"align": "CENTER"}},
                        {"row": 2, "col": 0, "text": "발령 부서", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 2, "col": 1, "text": "{{발령부서}}", "style": {"align": "CENTER"}},
                        {"row": 2, "col": 2, "text": "발령 직급", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 2, "col": 3, "text": "{{발령직급}}", "style": {"align": "CENTER"}},
                        {"row": 3, "col": 0, "text": "발령일", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 3, "col": 1, "text": "{{발령일}}", "style": {"align": "CENTER"}, "colspan": 3},
                        {"row": 4, "col": 0, "text": "사유", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 4, "col": 1, "text": "{{사유}}", "style": {"align": "LEFT"}, "colspan": 3},
                    ]
                }},
            ]
        }
    },
    "estimate": {
        "name": "견적서",
        "description": "견적/청구 양식",
        "fields": ["업체명", "담당자", "연락처", "날짜", "품목1", "수량1", "단가1", "품목2", "수량2", "단가2", "합계", "비고"],
        "structure": {
            "document": {"title": "견적서", "page_width_hu": 42520},
            "sections": [
                {"type": "paragraph", "content": "견 적 서", "align": "CENTER",
                 "style": {"bold": True, "font_size_pt": 24}},
                {"type": "paragraph", "content": ""},
                {"type": "table", "table": {
                    "rows": 2, "cols": 4, "col_widths_ratio": [15, 35, 15, 35],
                    "cells": [
                        {"row": 0, "col": 0, "text": "업체명", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 0, "col": 1, "text": "{{업체명}}", "style": {"align": "LEFT"}},
                        {"row": 0, "col": 2, "text": "날짜", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 0, "col": 3, "text": "{{날짜}}", "style": {"align": "LEFT"}},
                        {"row": 1, "col": 0, "text": "담당자", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 1, "col": 1, "text": "{{담당자}}", "style": {"align": "LEFT"}},
                        {"row": 1, "col": 2, "text": "연락처", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 1, "col": 3, "text": "{{연락처}}", "style": {"align": "LEFT"}},
                    ]
                }},
                {"type": "paragraph", "content": ""},
                {"type": "table", "table": {
                    "rows": 4, "cols": 4, "col_widths_ratio": [40, 15, 20, 25],
                    "cells": [
                        {"row": 0, "col": 0, "text": "품목", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 0, "col": 1, "text": "수량", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 0, "col": 2, "text": "단가", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 0, "col": 3, "text": "금액", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 1, "col": 0, "text": "{{품목1}}", "style": {"align": "LEFT"}},
                        {"row": 1, "col": 1, "text": "{{수량1}}", "style": {"align": "CENTER"}},
                        {"row": 1, "col": 2, "text": "{{단가1}}", "style": {"align": "RIGHT"}},
                        {"row": 1, "col": 3, "text": "", "style": {"align": "RIGHT"}},
                        {"row": 2, "col": 0, "text": "{{품목2}}", "style": {"align": "LEFT"}},
                        {"row": 2, "col": 1, "text": "{{수량2}}", "style": {"align": "CENTER"}},
                        {"row": 2, "col": 2, "text": "{{단가2}}", "style": {"align": "RIGHT"}},
                        {"row": 2, "col": 3, "text": "", "style": {"align": "RIGHT"}},
                        {"row": 3, "col": 0, "text": "합계", "style": {"bold": True, "align": "CENTER", "is_header": True}},
                        {"row": 3, "col": 1, "text": "", "style": {"align": "CENTER"}},
                        {"row": 3, "col": 2, "text": "", "style": {"align": "CENTER"}},
                        {"row": 3, "col": 3, "text": "{{합계}}", "style": {"bold": True, "align": "RIGHT"}},
                    ]
                }},
                {"type": "paragraph", "content": ""},
                {"type": "paragraph", "content": "{{비고}}", "align": "LEFT", "style": {}},
            ]
        }
    },
}


def get_template_choices():
    """Gradio 드롭다운용 선택지 반환"""
    return [(v["name"], k) for k, v in TEMPLATES.items()]


def get_template_fields(template_key: str) -> list[str]:
    """템플릿의 필드 목록 반환"""
    t = TEMPLATES.get(template_key)
    return t["fields"] if t else []


def get_template_structure(template_key: str) -> dict:
    """템플릿의 구조 JSON 반환"""
    t = TEMPLATES.get(template_key)
    return t["structure"] if t else {}
