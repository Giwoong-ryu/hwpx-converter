"""근로계약서/계약서 전용 processor.

대상 양식:
- 표준근로계약서, 일반 계약서 (갑/을 구조)
- 단락 기반 양식 (테이블이 거의 없음)

특징:
- 단락 내 "라벨 :" 패턴 위주 (근 무 장 소 :, 업무의 내용 :)
- 연속 공백 슬롯 (시/분/년/월/일) → _apply_date_inline에서 처리
- 체크박스 (    ), [    ]
- 갑/을 구분 앞 공백
- 한 단락 안에 여러 라벨이 나열되는 경우 많음 (서명란)

원칙:
- 라벨 사전을 AI 프롬프트에 [H] 태그로 전달 (라벨 보호)
- 테이블 슬롯보다는 AI 매핑 품질 향상에 초점
- 빈 slot_map 반환 (단락 기반이라 테이블 slot 불가)
"""
from __future__ import annotations
import re


# ─────────────────────────────────────────────────────────
# 라벨 사전
# ─────────────────────────────────────────────────────────

# 계약 당사자
_PARTY_LABELS = {
    "사업주", "근로자", "갑", "을", "사용자", "피용자",
    "계약당사자", "양 당사자",
}

# 회사/개인 정보
_COMPANY_LABELS = {
    "사업체명", "회사명", "업체명", "사업장명",
    "대표자", "대 표 자", "대표이사",
    "사업자등록번호", "사업자 등록번호",
    "주소", "주    소", "사업장 주소", "사업장 소재지",
    "전화", "연 락 처", "연락처",
    "성명", "성    명",
}

# 계약 조건
_CONDITION_LABELS = {
    "근로개시일", "근 로 개 시 일",
    "근무장소", "근 무 장 소",
    "업무의 내용", "업무내용",
    "소정근로시간", "소 정 근 로 시 간",
    "근무일", "휴일", "근무일/휴일",
    "임금", "월급", "일급", "시급",
    "월(일, 시간)급",
    "상여금", "약정수당", "그 밖의 수당",
    "임금지급일", "지급방법",
    "연차유급휴가", "연차",
    "사회보험", "4대 사회보험",
    "퇴직금", "계약기간",
}

# 시간 단위 (연속 공백 슬롯 대상)
_TIME_UNIT_LABELS = {
    "시", "분", "시간", "요일", "주", "월",
}

# 체크박스 주변 라벨
_CHECK_LABELS = {
    "있음", "없음",
}

CONTRACT_LABELS = (
    _PARTY_LABELS | _COMPANY_LABELS | _CONDITION_LABELS
    | _TIME_UNIT_LABELS | _CHECK_LABELS
)


def _normalize(text: str) -> str:
    """공백 제거 + 소문자화."""
    return re.sub(r"\s+", "", text).lower()


_NORMALIZED_LABELS = {_normalize(lbl) for lbl in CONTRACT_LABELS}


def is_contract_label(text: str) -> bool:
    """텍스트가 계약서 라벨인지 판정."""
    if not text:
        return False
    t = text.strip()
    if len(t) > 30:
        return False
    norm = _normalize(t)
    if not norm:
        return False
    if norm in _NORMALIZED_LABELS:
        return True
    # "라벨 :" 패턴
    base_match = re.match(r"^([가-힣A-Za-z\s()]+?)\s*[:：]", t)
    if base_match:
        base = _normalize(base_match.group(1))
        if base in _NORMALIZED_LABELS:
            return True
    # 번호 접두사 ("1. 근로개시일 :")
    num_match = re.match(r"^\d+\.\s*(.+?)\s*[:：]?\s*$", t)
    if num_match:
        base = _normalize(num_match.group(1))
        if base in _NORMALIZED_LABELS:
            return True
        # 번호 뒤에 라벨:뭐가 붙어있을 수도
        for lbl in _NORMALIZED_LABELS:
            if base.startswith(lbl):
                return True
    return False


# ─────────────────────────────────────────────────────────
# ContractProcessor
# ─────────────────────────────────────────────────────────

class ContractProcessor:
    """계약서 전용 processor.

    단락 기반 양식이므로 테이블 슬롯 맵은 비어있는 경우 많음.
    대신 CONTRACT_LABELS를 AI에게 extra_labels로 전달하여
    AI가 라벨을 [H]로 인식하고 라벨 텍스트를 값으로 교체하지 않도록 함.
    """

    def __init__(self, hwpx_path: str, structured: dict):
        self.hwpx_path = hwpx_path
        self.structured = structured

    def build_slot_map(self) -> dict:
        """라벨 + 인접 빈 셀 기반 slot map.

        계약서는 테이블이 거의 없어서 반환값이 빈 dict일 가능성 높음.
        실제 슬롯 주입은 clone_form의 _apply_date_inline_in_xml + normal_repl로 처리.

        Returns:
            dict: {라벨: [{file, tbl, row, col}, ...]} — 비어있을 수 있음
        """
        # 현재는 빈 map 반환. ai_mapper가 CONTRACT_LABELS를 extra_labels로 받음.
        return {}
