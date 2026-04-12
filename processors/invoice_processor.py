"""인보이스형 양식 전용 processor.

대상 양식:
- 견적서 (고객/업체 정보 + 품목 반복 행 + 합계)
- 세금계산서 (공급자/공급받는자 + 품목 + 세액)
- 납품확인서 (납품처/공급자 + 품목 + 확인일)

특징:
- 라벨이 **일반 텍스트 셀** (bold/bg 없음)
- `build_header_slot_map`이 빈 결과 반환 → 기존 경로 실패
- 라벨 사전 + 인접 빈 셀 매칭으로 슬롯 구축

원칙:
- 라벨 사전에 매칭된 텍스트는 **치환 대상에서 제외** (라벨 손실 방지)
- 빈 셀에만 값 주입 (inject_values_by_slot 재사용)
- 품목 반복 행은 헤더 행 감지 + 아래 빈 행 N개 슬롯화
"""
from __future__ import annotations
import re
import zipfile
from lxml import etree


# ─────────────────────────────────────────────────────────
# 라벨 사전 (정규화된 형태)
# ─────────────────────────────────────────────────────────

# 개체 정보 (공급자/공급받는자 공통)
_PARTY_LABELS = {
    "사업자등록번호", "사업자번호", "등록번호",
    "상호", "상호명", "회사명", "법인명", "업체명",
    "성명", "이름", "대표자", "대표자명", "대표이사",
    "사업장소재지", "사업장주소", "주소", "소재지",
    "업태", "종목", "업종",
    "전화", "전화번호", "연락처", "팩스",
    "이메일", "홈페이지",
}

# 거래 메타 정보
_TRANSACTION_LABELS = {
    "작성년월일", "작성일", "발행일", "견적일", "납품일",
    "납품일자", "계약일", "시행일", "일자",
    "비고", "적요", "참조",
    "귀하", "수신", "수신자",
    "공급자", "공급받는자", "납품처", "발주처",
    "공급가액", "세액", "부가세", "합계금액", "총액",
    "합계", "소계", "계",
}

# 품목 테이블 헤더 (반복 행)
_ITEM_HEADER_LABELS = {
    "월일", "일자", "NO", "번호", "No",
    "품목", "품명", "내역", "내용",
    "규격", "사양",
    "수량", "단위",
    "단가", "가격",
    "금액", "공급가액", "세액", "합계",
}

# 전체 라벨 (치환 금지 판정용)
INVOICE_LABELS = _PARTY_LABELS | _TRANSACTION_LABELS | _ITEM_HEADER_LABELS


def _normalize(text: str) -> str:
    """공백 제거 + 소문자화 (매칭용)."""
    return re.sub(r"\s+", "", text).lower()


# 정규화된 라벨 집합 (매칭용 캐시)
_NORMALIZED_LABELS = {_normalize(lbl) for lbl in INVOICE_LABELS}

# 합계/총액류 비표준 라벨 패턴
# "총 견적 금 액", "견적 총액", "합계 금액" 등 INVOICE_LABELS 미등재 변형 커버
_TOTAL_LABEL_RE = re.compile(r"합계|총액|소계|견적금액|총금액")


def _is_total_label(text: str) -> bool:
    """합계/총액류 라벨 판정 — INVOICE_LABELS 미등재 변형 포함.

    Examples: '총 견적 금 액', '견적 총액', '합계 금액'
    표준 라벨('합계금액', '총액' 등)도 True 반환하므로 is_invoice_label과 OR 조합.
    """
    if not text:
        return False
    t = text.strip()
    if len(t) > 20:
        return False
    norm = _normalize(t)
    return bool(_TOTAL_LABEL_RE.search(norm))


def is_invoice_label(text: str) -> bool:
    """텍스트가 인보이스 라벨인지 판정."""
    if not text:
        return False
    t = text.strip()
    if len(t) > 30:  # 라벨은 짧아야 함
        return False
    norm = _normalize(t)
    if not norm:
        return False
    # 정확 매칭
    if norm in _NORMALIZED_LABELS:
        return True
    # 접미사 패턴 (XX등록번호, XX회사명 등)
    suffixes = ["등록번호", "사업자번호", "회사명", "상호", "주소", "전화"]
    for suf in suffixes:
        if norm.endswith(_normalize(suf)) and len(norm) <= 15:
            return True
    return False


# ─────────────────────────────────────────────────────────
# InvoiceProcessor
# ─────────────────────────────────────────────────────────

class InvoiceProcessor:
    """인보이스형 양식 전용 슬롯 맵 빌더."""

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

        # zip에서 실제 XML 읽기 (build_header_slot_map과 동일 방식)
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
        # 물리 셀 목록 (row, col, text, width, height)
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

        # ─ 단계 1: 라벨 → 인접 빈 셀 매핑 (가로형)
        #
        # Phase 1: 기존 알고리즘 — 첫 번째 빈 셀, 다른 라벨에서 스캔 중단
        # Phase 2 (합계류 전용): Phase 1 실패 시 → 전체 행 재스캔 → 마지막 빈 셀
        #   대상: '합계금액', '총 견적 금 액', '소계' 등 합계/총액 라벨
        #   이유: 다른 라벨(예: '부가세')이 사이에 있어 Phase 1이 중단된 경우 커버
        for r, cells in by_row.items():
            for idx, (c, text) in enumerate(cells):
                is_std = is_invoice_label(text)
                is_total = _is_total_label(text)
                if not is_std and not is_total:
                    continue

                # Phase 1: 첫 번째 빈 셀 탐색 (기존 동작 유지)
                target_col: int | None = None
                for c2, text2 in cells[idx + 1:]:
                    if not text2.strip():
                        target_col = c2
                        break
                    elif is_invoice_label(text2):
                        break  # 다른 라벨 = 경계, 스캔 종료

                # Phase 2: 합계류 라벨 + Phase 1 실패 → 전체 행 재스캔 (마지막 빈 셀)
                if target_col is None and is_total:
                    empties = [c2 for c2, t2 in cells[idx + 1:] if not t2.strip()]
                    if empties:
                        target_col = empties[-1]

                if target_col is not None:
                    slot = {
                        "file": fname, "tbl": tbl_idx,
                        "row": r, "col": target_col,
                    }
                    key = text.strip()
                    if slot not in result.setdefault(key, []):
                        result[key].append(slot)

        # ─ 단계 2: 품목 반복 행 감지 + 슬롯화
        self._detect_item_rows(by_row, tbl_idx, fname, result)

    def _detect_item_rows(self, by_row: dict, tbl_idx: int, fname: str, result: dict) -> None:
        """품목 헤더 행을 찾고 그 아래 빈 행들을 품목 슬롯으로 등록.

        예: r17 = [월일, 품목, 수량, 단가, 금액] (헤더)
            r18 ~ r32 = 빈 행들 (품목 슬롯)
            r33 = 합계
        """
        # 품목 헤더 후보 찾기: 한 행에 품목 헤더 라벨 3개 이상
        item_header_keywords = {"품목", "품 목", "품명", "수량", "단가", "단 가", "금액", "금 액"}

        for r, cells in by_row.items():
            label_count = 0
            header_cols = {}  # col -> label
            for c, text in cells:
                t = text.strip()
                if t in item_header_keywords or _normalize(t) in {_normalize(k) for k in item_header_keywords}:
                    label_count += 1
                    header_cols[c] = t

            if label_count < 3:
                continue

            # 이 행이 품목 헤더 → 아래 행들 탐색
            item_idx = 0
            sorted_rows = sorted(by_row.keys())
            start_idx = sorted_rows.index(r) + 1
            for next_r in sorted_rows[start_idx:]:
                next_cells = by_row[next_r]
                # 합계 행이면 종료
                has_total_label = any(
                    _normalize(t) in {"합계", "소계", "계", "총액"}
                    for _, t in next_cells
                )
                if has_total_label:
                    break

                # 이 행의 헤더 컬럼 위치에 빈 셀이 있으면 슬롯 등록
                has_any = False
                for c, text in next_cells:
                    if c not in header_cols:
                        continue
                    if not text.strip():
                        item_idx_local = item_idx + 1
                        label = header_cols[c]  # "품목", "수량" 등
                        slot = {
                            "file": fname, "tbl": tbl_idx,
                            "row": next_r, "col": c,
                        }
                        key = label
                        if slot not in result.setdefault(key, []):
                            result[key].append(slot)
                        has_any = True

                if has_any:
                    item_idx += 1

    def _get_tc_text(self, tc) -> str:
        """tc 요소에서 텍스트 추출 (clone_form._get_cell_text와 동일 로직)."""
        texts = []
        for t in tc.findall(".//hp:t", self._ns):
            tx = "".join(t.itertext()).strip()
            if tx:
                texts.append(tx)
        return " ".join(texts).strip()
