"""정부공문/행정양식 전용 processor.

대상 양식:
- 공문, 기안문, 보고서 (행정안전부 양식 등)
- 결재란/서명란 + 본문 글머리 구조

특징:
- 표와 단락 혼재 (상단 헤더 테이블 + 본문 단락)
- 라벨: 작성과, 담당자, 연락처, 수신, 제목, 시행일자
- 기호 라벨: ▸, ○, □ (제목/본문 글머리)
- 서명란: 차관/대표이사/기관장 등

원칙:
- InvoiceProcessor와 동일한 "라벨 → 인접 빈 셀" 매칭
- 단락 빈칸 (시행일자 `20 년 월 일`) 은 _apply_date_inline 재사용
- 기호 라벨(▸ ▸) 주변 셀도 슬롯화
"""
from __future__ import annotations
import re
import zipfile
from lxml import etree


# ─────────────────────────────────────────────────────────
# 라벨 사전 (정규화된 형태)
# ─────────────────────────────────────────────────────────

# 공문 헤더 필드
_HEADER_LABELS = {
    "작성과", "작성부서", "부서", "주관부서",
    "담당자", "담당", "담당자명",
    "연락처", "전화", "전화번호",
    "이메일", "팩스",
}

# 수신/발신/제목
_ADDRESS_LABELS = {
    "수신", "수신자", "참조",
    "발신", "발신기관", "기관명",
    "제목", "문서제목",
}

# 날짜/번호
_META_LABELS = {
    "시행일자", "시행일", "문서번호", "일자",
    "보존기간", "보존년수", "분류번호",
}

# 결재선 / 서명란
_SIGN_LABELS = {
    "기안자", "검토자", "결재자", "전결", "대결",
    "차관", "장관", "국장", "과장",
    "대표이사", "사장", "대표자",
    "기관장", "원장", "처장", "실장",
}

# 첨부
_ATTACH_LABELS = {
    "붙임", "첨부", "첨부파일",
}

GOVERNMENT_LABELS = _HEADER_LABELS | _ADDRESS_LABELS | _META_LABELS | _SIGN_LABELS | _ATTACH_LABELS


def _normalize(text: str) -> str:
    """공백 제거 + 소문자화 (매칭용)."""
    return re.sub(r"\s+", "", text).lower()


_NORMALIZED_LABELS = {_normalize(lbl) for lbl in GOVERNMENT_LABELS}


def is_government_label(text: str) -> bool:
    """텍스트가 공문 라벨인지 판정."""
    if not text:
        return False
    t = text.strip()
    if len(t) > 30:
        return False
    norm = _normalize(t)
    if not norm:
        return False
    # 정확 매칭
    if norm in _NORMALIZED_LABELS:
        return True
    # "차    관 : (인)", "대표이사 :" 같은 라벨+콜론+추가기호 형태
    # 콜론 앞 부분만 추출해서 정규화 후 재판정 (공백 포함 라벨 지원)
    base_match = re.match(r"^([가-힣A-Za-z\s]+?)\s*[:：]", t)
    if base_match:
        base = _normalize(base_match.group(1))
        if base in _NORMALIZED_LABELS:
            return True
    # 접미사 패턴 ("담당자", "(주)담당자")
    for suf in ["담당자", "담당", "연락처", "기관", "부서"]:
        if norm.endswith(_normalize(suf)) and len(norm) <= 15:
            return True
    # "붙임1", "붙임 2" 같은 번호 포함
    if re.match(r"^붙임\s*\d*$", t) or re.match(r"^첨부\s*\d*$", t):
        return True
    return False


# 기호 라벨 (제목/본문 글머리)
_SYMBOL_RE = re.compile(r"^[▸▪●○□◎◇☞※→➤]+$")


def is_symbol_label(text: str) -> bool:
    """▸, ○, □ 같은 기호만 있는 셀인지 판정 (제목/본문 자리)."""
    if not text:
        return False
    t = text.strip()
    if len(t) > 10:
        return False
    return bool(_SYMBOL_RE.match(t))


# ─────────────────────────────────────────────────────────
# GovernmentProcessor
# ─────────────────────────────────────────────────────────

class GovernmentProcessor:
    """정부공문/행정양식 전용 슬롯 맵 빌더."""

    def __init__(self, hwpx_path: str, structured: dict):
        self.hwpx_path = hwpx_path
        self.structured = structured
        self._ns = {
            "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
            "hc": "http://www.hancom.co.kr/hwpml/2011/core",
            "hh": "http://www.hancom.co.kr/hwpml/2011/head",
        }

    def build_slot_map(self) -> dict:
        """라벨-값 쌍 기반 슬롯 맵 구축.

        Returns:
            dict: {라벨_텍스트: [{"file", "tbl", "row", "col"}, ...]}
        """
        result: dict[str, list[dict]] = {}

        with zipfile.ZipFile(self.hwpx_path, "r") as zf:
            for fname in sorted(zf.namelist()):
                if not (fname.startswith("Contents/") and fname.endswith(".xml")):
                    continue
                if fname == "Contents/header.xml":
                    continue
                try:
                    root = etree.fromstring(zf.read(fname))
                except Exception:
                    continue

                for tbl_idx, tbl in enumerate(root.findall(".//hp:tbl", self._ns)):
                    self._scan_table(tbl, tbl_idx, fname, result)

        return result

    def _scan_table(self, tbl, tbl_idx: int, fname: str, result: dict) -> None:
        """하나의 테이블을 스캔하여 라벨-값 슬롯 추출."""
        phys_cells = []
        for tc in tbl.findall("hp:tr/hp:tc", self._ns):
            addr = tc.find("hp:cellAddr", self._ns)
            if addr is None:
                continue
            r = int(addr.get("rowAddr", "0"))
            c = int(addr.get("colAddr", "0"))
            text = self._get_tc_text(tc)
            phys_cells.append((r, c, text))

        if not phys_cells:
            return

        # 행별 그룹
        by_row: dict[int, list] = {}
        for r, c, t in phys_cells:
            by_row.setdefault(r, []).append((c, t))
        for r in by_row:
            by_row[r].sort(key=lambda x: x[0])

        # 라벨 → 인접 빈 셀 매핑 (양방향: 오른쪽/왼쪽 모두)
        for r, cells in by_row.items():
            for idx, (c, text) in enumerate(cells):
                is_govlbl = is_government_label(text)
                is_symbol = is_symbol_label(text)
                if not is_govlbl and not is_symbol:
                    continue

                # 기호 라벨(▸ ▸)은 셀 자체가 값 자리 (텍스트 치환 경로)
                # 일반 라벨은 인접 빈 셀을 값 자리로

                if is_govlbl:
                    # 오른쪽 빈 셀 우선 탐색
                    target_col: int | None = None
                    for c2, text2 in cells[idx + 1:]:
                        if not text2.strip():
                            target_col = c2
                            break
                        elif is_government_label(text2) or is_symbol_label(text2):
                            break

                    # 오른쪽 없으면 왼쪽 빈 셀 탐색 (정부공문은 라벨이 가운데인 경우 많음)
                    if target_col is None:
                        for c2, text2 in reversed(cells[:idx]):
                            if not text2.strip():
                                target_col = c2
                                break
                            elif is_government_label(text2) or is_symbol_label(text2):
                                break

                    if target_col is not None:
                        slot = {"file": fname, "tbl": tbl_idx, "row": r, "col": target_col}
                        key = text.strip()
                        if slot not in result.setdefault(key, []):
                            result[key].append(slot)

    def _get_tc_text(self, tc) -> str:
        """tc 요소에서 텍스트 추출."""
        texts = []
        for t in tc.findall(".//hp:t", self._ns):
            tx = "".join(t.itertext()).strip()
            if tx:
                texts.append(tx)
        return " ".join(texts).strip()
