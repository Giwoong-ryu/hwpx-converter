"""양식 타입 자동 분류기.

원칙: **whitelist 방식**. 매우 구체적인 시그널만 특정 타입으로 분류.
불확실하면 "legacy"를 반환하여 기존 build_header_slot_map 경로로 폴백.

반환 값:
    "invoice_style" — 견적서/세금계산서/납품확인서 (일반 텍스트 라벨 기반)
    "section_based" — 자기소개서 (섹션 헤더 + 제목 append + 본문)
    "legacy"        — 기존 슬롯형 양식 (bold/bg 헤더 기반, build_header_slot_map)
"""
from __future__ import annotations
import re


def _collect_all_text(structured: dict) -> str:
    """양식의 모든 셀 텍스트를 하나의 문자열로 합쳐 반환."""
    parts = []
    for table in structured.get("tables", []):
        for row in table.get("rows", []):
            for cell in row:
                text = cell.get("text", "").strip()
                if text:
                    parts.append(text)
    for p in structured.get("paragraphs", []):
        if p.strip():
            parts.append(p.strip())
    return " ".join(parts)


def classify_form(structured: dict) -> str:
    """양식 구조를 분석해 타입을 분류한다.

    판정 우선순위: section_based → invoice_style → legacy
    (자기소개서는 정확한 시그널이 있으므로 먼저 체크)
    """
    all_text = _collect_all_text(structured)
    text_norm = re.sub(r"\s+", "", all_text)

    # ─ 1. section_based 판정 (자기소개서형)
    # 시그널: "자기소개서" 제목 + "제목 :" 반복 3회 이상 + 1컬럼 섹션 테이블
    if _is_section_based(structured, all_text, text_norm):
        return "section_based"

    # ─ 2. invoice_style 판정 (견적서/세금계산서/납품확인서)
    if _is_invoice_style(all_text, text_norm):
        return "invoice_style"

    # ─ 3. 기본값: legacy (기존 경로)
    return "legacy"


def _is_section_based(structured: dict, all_text: str, text_norm: str) -> bool:
    """자기소개서형 판정.

    시그널:
    - 제목이 "자기소개서" 포함
    - "제목 :" 3회 이상 반복 (여러 섹션)
    - 단일 컬럼 테이블 (모든 행이 1셀)
    """
    if "자기소개서" not in text_norm and "자  기  소  개  서" not in all_text:
        return False

    title_count = all_text.count("제목 :") + all_text.count("제목:")
    if title_count < 3:
        return False

    # 단일 컬럼 테이블 확인
    for table in structured.get("tables", []):
        rows = table.get("rows", [])
        if rows and all(len(r) == 1 for r in rows):
            return True
    return False


def _is_invoice_style(all_text: str, text_norm: str) -> bool:
    """인보이스형 판정.

    강한 시그널 (하나라도 매칭되면 invoice):
    - "공급자" + "공급받는자" 동시 존재
    - "견적서" 또는 "견 적 서"
    - "세금계산서"
    - "납품확인서" 또는 ("납품" + "공급가액")
    """
    signals = []

    # 공급자/공급받는자 쌍 (세금계산서, 견적서, 납품확인서 공통)
    if "공급자" in text_norm and "공급받는자" in text_norm:
        signals.append("supplier_buyer_pair")

    # 견적서 타이틀
    if "견적서" in text_norm or "견 적 서" in all_text:
        signals.append("quotation_title")

    # 세금계산서 타이틀
    if "세금계산서" in text_norm:
        signals.append("tax_invoice_title")

    # 납품확인서/검수확인서 타이틀
    if "납품확인서" in text_norm or "납품 확인서" in all_text:
        signals.append("delivery_confirmation_title")
    if "검수확인서" in text_norm or "검수 확인서" in all_text or "검 수 확 인 서" in all_text:
        signals.append("inspection_confirmation_title")

    # 납품 + 공급가액 조합
    if "납품" in text_norm and "공급가액" in text_norm:
        signals.append("delivery_supply_amount")

    # 납품/검수 + 품목 테이블 (품명 + 수량 + 단가 등 3+개 헤더)
    if ("납품" in text_norm or "검수" in text_norm):
        item_cols = sum(1 for kw in ["품명", "품목", "수량", "단가", "규격", "모델명"]
                        if kw in text_norm)
        if item_cols >= 3:
            signals.append("delivery_item_table")

    return len(signals) > 0
