"""사업제안서/구매제안서 전용 processor.

대상 양식:
- 구매제안서, 사업제안서, 용역제안서
- 표 기반 (제안자 정보 헤더 + 제안 내용 + 품목 반복 행 + 참고사항)

특징:
- bold/bg 헤더가 많음 (build_header_slot_map이 잘 작동)
- 품목 반복 행 (물품(서비스)명, 규격∙사양, 수량, 단가, 금액)
- 서술 필드 (제목, 제안내용, 참고사항)

구현 전략:
- slot_map 빌더: build_header_slot_map 재사용 (form.py에서 처리)
- 라벨 사전 PROPOSAL_LABELS: AI에게 extra_labels로 전달 → 라벨 보호
"""
from __future__ import annotations


# 사업제안서 라벨 사전
_PROPOSAL_HEADER_LABELS = {
    "제안자", "담당", "담  당",
    "성명", "성  명", "소속", "소    속",
    "직급", "직  급", "직위",
    "연락처", "연 락 처",
}

_PROPOSAL_CONTENT_LABELS = {
    "제목", "제  목",
    "제안내용", "제 안 내 용",
    "제안물품", "제 안 물 품",
    "참고사항", "참 고 사 항",
    "물품(서비스)명", "서비스명",
    "규격", "규격∙사양", "사양",
    "수량", "수  량", "단가", "단  가", "금액", "금  액",
    "비고",
}

_PROPOSAL_SIGNATURE_LABELS = {
    "제안자 :", "신청자 :",
    "일자", "작성일",
}

PROPOSAL_LABELS = _PROPOSAL_HEADER_LABELS | _PROPOSAL_CONTENT_LABELS | _PROPOSAL_SIGNATURE_LABELS


class ProposalProcessor:
    """사업제안서 전용 processor (가벼운 래퍼).

    slot_map은 form.py의 build_header_slot_map으로 처리되고,
    이 클래스는 주로 PROPOSAL_LABELS를 AI extra_labels로 제공하기 위한 식별자 역할.
    """

    def __init__(self, hwpx_path: str, structured: dict):
        self.hwpx_path = hwpx_path
        self.structured = structured

    def build_slot_map(self) -> dict:
        """빈 dict 반환 (form.py가 build_header_slot_map으로 폴백)."""
        return {}
