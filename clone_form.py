#!/usr/bin/env python3
"""
HWPX 양식 복제 도구 (Workflow F)

기존 HWPX 양식을 복사한 뒤 텍스트만 치환하여 새 문서를 생성한다.
원본의 테이블·이미지·스타일을 100% 유지하면서 내용만 교체한다.

2단계 치환:
  Phase 1 — 구문 수준(--map/--replace): 전체 XML에서 긴 문구를 먼저 치환
  Phase 2 — 키워드 수준(--keywords): <hp:t> 태그 내부에서만 남은 키워드를 치환

사용법:
  분석:    python clone_form.py --analyze sample.hwpx
  복제:    python clone_form.py sample.hwpx output.hwpx --map map.json
  키워드:  python clone_form.py sample.hwpx output.hwpx --map map.json --keywords kw.json
  CLI:     python clone_form.py sample.hwpx output.hwpx --replace "원본=대체" "A=B"

Import:
  from clone_form import clone, analyze, extract_texts
"""

import argparse
import json
import os
import re
import sys
import xml.sax.saxutils as saxutils
import zipfile

from lxml import etree

_NS = {
    'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
    'hs': 'http://www.hancom.co.kr/hwpml/2011/section',
    'hc': 'http://www.hancom.co.kr/hwpml/2011/core',
    'hh': 'http://www.hancom.co.kr/hwpml/2011/head',
}

# ai_mapper._SUB_LABELS와 동기화: 이 셀들은 서브 헤더로 취급 → 인접 빈 셀을 직접 슬롯으로 등록
_FORM_SUB_LABELS = {
    "H.P", "HP", "E-MAIL", "E.MAIL", "EMAIL", "TEL", "FAX",
    "전화", "휴대폰", "이메일", "홈페이지",
    "상", "중", "하", "상/중/하",
}


def _parse_header_styles(header_bytes):
    """header.xml에서 borderFill 배경색과 charPr bold 정보를 파싱한다."""
    root = etree.fromstring(header_bytes)
    bf_colors = {}
    for bf in root.findall('.//hh:borderFill', _NS):
        bid = bf.get('id', '')
        fill = bf.find('.//hc:winBrush', _NS)
        fc = fill.get('faceColor', 'none') if fill is not None else 'none'
        bf_colors[bid] = fc not in ('none', '#FFFFFF', 'rgb(255, 255, 255)')

    cp_bold = {}
    for cp in root.findall('.//hh:charPr', _NS):
        cid = cp.get('id', '')
        cp_bold[cid] = cp.find('hh:bold', _NS) is not None

    return bf_colors, cp_bold


def _get_cell_text(tc):
    """hp:tc 요소에서 텍스트를 추출한다. 여러 run을 합친다."""
    texts = []
    for t in tc.findall('.//hp:t', _NS):
        txt = re.sub(r'<[^>]+>', '', etree.tostring(t, encoding='unicode', method='text') or '').strip()
        if txt:
            texts.append(txt)
    return ' '.join(texts).strip()


def _build_table_data(tbl, bf_colors, cp_bold):
    """hp:tbl 요소에서 테이블 그리드를 구축한다. 병합 셀 처리 포함."""
    row_cnt = int(tbl.get('rowCnt', '0'))
    col_cnt = int(tbl.get('colCnt', '0'))
    if row_cnt == 0 or col_cnt == 0:
        return None

    # 그리드 초기화
    grid = [[None] * col_cnt for _ in range(row_cnt)]

    # 직접 자식 tc만 (중첩 테이블의 tc 제외)
    for tc in tbl.findall('hp:tr/hp:tc', _NS):
        addr = tc.find('hp:cellAddr', _NS)
        if addr is None:
            continue
        r = int(addr.get('rowAddr', '0'))
        c = int(addr.get('colAddr', '0'))
        rs = int(addr.get('rowSpan', '1'))
        cs = int(addr.get('colSpan', '1'))

        text = _get_cell_text(tc)
        bf_id = tc.get('borderFillIDRef', '')
        has_bg = bf_colors.get(bf_id, False)

        run = tc.find('.//hp:run', _NS)
        is_bold = False
        if run is not None:
            cp_id = run.get('charPrIDRef', '')
            is_bold = cp_bold.get(cp_id, False)

        cell = {"text": text, "bold": is_bold, "bg": has_bg}

        # 병합 영역 채우기 (같은 셀 참조)
        for dr in range(rs):
            for dc in range(cs):
                nr, nc = r + dr, c + dc
                if nr < row_cnt and nc < col_cnt:
                    grid[nr][nc] = cell

    return grid


def extract_structured_fields(hwpx_path):
    """HWPX에서 테이블 구조를 보존하여 필드를 추출한다.

    Returns:
        dict: {
            "tables": [{
                "rows": [[{"text", "bold", "bg"}, ...], ...]
            }, ...],
            "paragraphs": [str, ...],
            "flat_texts": [str, ...]  # 기존 extract_texts 호환
        }
    """
    with zipfile.ZipFile(hwpx_path, 'r') as zf:
        # header.xml에서 스타일 정보 파싱
        bf_colors, cp_bold = {}, {}
        if 'Contents/header.xml' in zf.namelist():
            try:
                bf_colors, cp_bold = _parse_header_styles(zf.read('Contents/header.xml'))
            except Exception:
                pass  # 스타일 파싱 실패해도 텍스트 추출은 계속

        tables = []
        table_texts = set()  # 테이블 내 텍스트 (문단과 구분용)
        flat_texts = []
        seen = set()

        for name in sorted(zf.namelist()):
            if not (name.startswith('Contents/') and name.endswith('.xml')):
                continue
            if name == 'Contents/header.xml':
                continue

            try:
                root = etree.fromstring(zf.read(name))
            except Exception:
                continue

            # 테이블 추출 (최상위만 - 중첩 테이블은 부모 테이블 안에서 처리)
            for tbl in root.findall('.//hp:tbl', _NS):
                # 이 테이블이 다른 테이블의 셀 안에 있는지 체크
                parent = tbl.getparent()
                in_nested = False
                while parent is not None:
                    if parent.tag == '{http://www.hancom.co.kr/hwpml/2011/paragraph}tc':
                        in_nested = True
                        break
                    parent = parent.getparent()
                if in_nested:
                    continue  # 중첩 테이블은 스킵 (부모에서 처리됨)

                grid = _build_table_data(tbl, bf_colors, cp_bold)
                if grid is None:
                    continue

                table_rows = []
                for row in grid:
                    row_cells = []
                    for cell in row:
                        if cell is None:
                            row_cells.append({"text": "", "bold": False, "bg": False})
                        else:
                            row_cells.append(cell)
                            if cell["text"] and cell["text"] not in seen:
                                seen.add(cell["text"])
                                flat_texts.append(cell["text"])
                            table_texts.add(cell["text"])
                    table_rows.append(row_cells)
                tables.append({"rows": table_rows})

        # 문단 텍스트 (테이블 밖)
        paragraphs = []
        for name in sorted(zf.namelist()):
            if not (name.startswith('Contents/') and name.endswith('.xml')):
                continue
            if name == 'Contents/header.xml':
                continue

            data = zf.read(name).decode('utf-8')
            for m in re.finditer(r'<hp:t>(.*?)</hp:t>', data, re.DOTALL):
                raw = m.group(1)
                clean = re.sub(r'<[^>]+>', '', raw).strip()
                if clean and clean not in seen and clean not in table_texts:
                    seen.add(clean)
                    flat_texts.append(clean)
                    paragraphs.append(clean)

    return {"tables": tables, "paragraphs": paragraphs, "flat_texts": flat_texts}


def extract_texts(hwpx_path):
    """HWPX에서 <hp:t> 태그의 텍스트를 모두 추출한다.

    Returns:
        list[str]: 고유 텍스트 목록 (등장 순서 유지)
    """
    texts = []
    seen = set()

    with zipfile.ZipFile(hwpx_path, "r") as zf:
        for name in zf.namelist():
            if name.startswith("Contents/") and name.endswith(".xml"):
                data = zf.read(name).decode("utf-8")
                for m in re.finditer(r"<hp:t>(.*?)</hp:t>", data, re.DOTALL):
                    # 인라인 XML 태그 제거하여 순수 텍스트 추출
                    raw = m.group(1)
                    clean = re.sub(r"<[^>]+>", "", raw).strip()
                    if clean and clean not in seen:
                        seen.add(clean)
                        texts.append(clean)
    return texts


def analyze(hwpx_path):
    """HWPX 양식을 분석하여 구조 요약과 텍스트 목록을 출력한다."""
    print(f"=== HWPX 양식 분석: {hwpx_path} ===\n")

    with zipfile.ZipFile(hwpx_path, "r") as zf:
        names = zf.namelist()
        print(f"ZIP 엔트리: {len(names)}개")

        # BinData 수
        bindata = [n for n in names if n.startswith("BinData/")]
        print(f"BinData (이미지 등): {len(bindata)}개")

        # section0.xml 분석
        if "Contents/section0.xml" in names:
            sec = zf.read("Contents/section0.xml").decode("utf-8")
            tables = len(re.findall(r"<hp:tbl ", sec))
            pics = len(re.findall(r"<hp:pic ", sec))
            paras = len(re.findall(r"<hp:p ", sec))
            runs = len(re.findall(r"<hp:run ", sec))
            print(f"문단: {paras}개, 런: {runs}개, 테이블: {tables}개, 이미지: {pics}개")
            print(f"section0.xml 크기: {len(sec):,} bytes")

    # 텍스트 추출
    texts = extract_texts(hwpx_path)
    print(f"\n고유 텍스트 조각: {len(texts)}개\n")
    for i, t in enumerate(texts, 1):
        display = t[:80] + "..." if len(t) > 80 else t
        print(f"  [{i:3d}] {display}")

    return texts


def auto_analyze(hwpx_path, output_json=None):
    """양식을 분석하고 치환 맵 템플릿을 JSON으로 출력한다.

    에이전트가 이 출력을 기반으로 치환 맵을 작성할 수 있도록
    원본 텍스트를 key로, 빈 문자열을 value로 하는 JSON을 생성한다.

    Args:
        hwpx_path: 분석할 .hwpx 파일
        output_json: 출력 JSON 경로 (None이면 stdout)

    Returns:
        dict: {structure: {...}, texts: [...], template: {...}}
    """
    structure = {}
    with zipfile.ZipFile(hwpx_path, "r") as zf:
        names = zf.namelist()
        bindata = [n for n in names if n.startswith("BinData/")]
        structure["zip_entries"] = len(names)
        structure["bindata_count"] = len(bindata)

        if "Contents/section0.xml" in names:
            sec = zf.read("Contents/section0.xml").decode("utf-8")
            structure["tables"] = len(re.findall(r"<hp:tbl ", sec))
            structure["images"] = len(re.findall(r"<hp:pic ", sec))
            structure["paragraphs"] = len(re.findall(r"<hp:p ", sec))
            structure["runs"] = len(re.findall(r"<hp:run ", sec))
            structure["section_size"] = len(sec)

    texts = extract_texts(hwpx_path)

    # 워크플로우 추천
    has_tables = structure.get("tables", 0) > 0
    has_images = structure.get("images", 0) > 0
    if has_tables or has_images:
        recommendation = "Workflow F (clone_form.py) — 테이블/이미지 포함, 양식 복제 필수"
    else:
        recommendation = "Workflow C 또는 F 가능 — 단순 텍스트 문서"

    # 치환 맵 템플릿 생성
    template = {}
    for t in texts:
        if len(t) > 1:  # 1글자 이하 건너뜀
            template[t] = ""

    result = {
        "source": hwpx_path,
        "structure": structure,
        "recommendation": recommendation,
        "text_count": len(texts),
        "template_map": template,
    }

    output = json.dumps(result, ensure_ascii=False, indent=2)

    if output_json:
        with open(output_json, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"자동 분석 완료: {output_json}")
        print(f"  구조: 테이블 {structure.get('tables', 0)}개, "
              f"이미지 {structure.get('images', 0)}개, "
              f"문단 {structure.get('paragraphs', 0)}개")
        print(f"  텍스트 조각: {len(texts)}개")
        print(f"  추천: {recommendation}")
    else:
        print(output)

    return result


def _prepare_keywords(keywords):
    """키워드를 길이 내림차순으로 정렬한다 (긴 것이 먼저 매칭되도록)."""
    return sorted(keywords.items(), key=lambda x: len(x[0]), reverse=True)


def _apply_keywords_to_text(text, sorted_keywords):
    """순수 텍스트에 키워드 치환을 적용한다."""
    for old, new in sorted_keywords:
        if old in text:
            text = text.replace(old, new)
    return text


def _apply_keywords_in_xml(xml_text, sorted_keywords):
    """<hp:t> 태그 내부의 텍스트에만 키워드 치환을 적용한다.

    인라인 XML 요소(<hp:fwSpace/>, <hp:tab/> 등)가 키워드를
    분리하는 경우를 처리하기 위해 태그 경계에서 텍스트를 분할하여
    각 조각에 개별적으로 치환을 적용한다.
    """
    def replace_in_t(match):
        inner = match.group(1)
        # 인라인 XML 태그로 분할
        parts = re.split(r"(<[^>]+>)", inner)
        result = []
        for part in parts:
            if part.startswith("<"):
                # XML 태그는 그대로 유지
                result.append(part)
            else:
                # 텍스트 부분에만 키워드 치환 적용
                result.append(_apply_keywords_to_text(part, sorted_keywords))
        return "<hp:t>" + "".join(result) + "</hp:t>"

    return re.sub(r"<hp:t>(.*?)</hp:t>", replace_in_t, xml_text, flags=re.DOTALL)


def _replace_across_runs(xml_text, replacements):
    """Phase 0: 같은 <hp:p> 안의 여러 <hp:t> 텍스트를 합쳐서 치환 매칭.

    한글에서 서식(볼드, 폰트크기 등)이 바뀔 때마다 새 <hp:run>이 생성되어
    같은 문장이 여러 <hp:t>로 분할된다. AI는 합쳐진 텍스트를 키로 돌려주므로
    개별 <hp:t>에서는 매칭 실패한다.

    해결: 문단(<hp:p>) 단위로 모든 <hp:t> 텍스트를 이어 붙여 매칭 시도.
    매칭 성공 시 첫 번째 <hp:t>에 치환 결과를 넣고 나머지 <hp:t>를 비운다.
    """
    def _replace_para(para_match):
        para = para_match.group(0)
        # 이 문단의 모든 hp:t 텍스트 추출
        t_matches = list(re.finditer(r"<hp:t>(.*?)</hp:t>", para, re.DOTALL))
        if len(t_matches) < 2:
            return para  # 단일 run이면 Phase 1에서 처리

        # 각 hp:t의 클린 텍스트를 합침
        t_texts = []
        for m in t_matches:
            clean = re.sub(r"<[^>]+>", "", m.group(1)).strip()
            t_texts.append(clean)
        combined = "".join(t_texts)

        if not combined:
            return para

        # 합쳐진 텍스트로 매칭 시도 (replacements는 이미 긴 키 우선 정렬됨)
        matched_key = None
        matched_val = None
        for old_text, new_text in replacements.items():
            if old_text in combined:
                matched_key = old_text
                matched_val = new_text
                break

        if not matched_key:
            return para

        # 매칭 성공: 합쳐진 텍스트에서 치환 수행
        replaced_combined = combined.replace(matched_key, saxutils.escape(matched_val))

        # 첫 번째 hp:t에 결과 전체를 넣고, 나머지 hp:t는 비움
        result = para
        for i, m in enumerate(t_matches):
            old_tag = m.group(0)
            if i == 0:
                new_tag = "<hp:t>" + replaced_combined + "</hp:t>"
            else:
                new_tag = "<hp:t></hp:t>"
            result = result.replace(old_tag, new_tag, 1)

        return result

    return re.sub(r"<hp:p\b[^>]*>.*?</hp:p>", _replace_para, xml_text, flags=re.DOTALL)


def _split_ordered_replacements(replacements):
    """__N 접미사 키를 일반 치환과 순서 기반 치환으로 분리한다.

    반환:
        normal: {원본텍스트: 새텍스트} (기존 방식)
        ordered: {원본텍스트: [val1, val2, val3, ...]} (N번째 occurrence 치환)
    """
    normal = {}
    ordered_raw = {}

    for k, v in replacements.items():
        m = re.match(r"^(.*?)__(\d+)$", k)
        if m and int(m.group(2)) >= 1:
            base = m.group(1)
            idx = int(m.group(2)) - 1  # 1-based → 0-based
            if base not in ordered_raw:
                ordered_raw[base] = {}
            ordered_raw[base][idx] = v
        else:
            normal[k] = v

    ordered = {}
    for base, idx_map in ordered_raw.items():
        max_idx = max(idx_map.keys())
        ordered[base] = [idx_map.get(i, "") for i in range(max_idx + 1)]

    return normal, ordered


def _apply_ordered_in_xml(xml_text, ordered_map, label_counts=None):
    """base_text의 N번째 문단(셀) occurrence를 values[N]으로 순서대로 치환한다.

    ordered_map: {base_text: [val1, val2, val3, ...]}
    label_counts: {base_text: 라벨 셀 수} — 앞 N개 occurrence를 스킵 (A1 수정)

    처리 방식 (문단 레벨):
      - 케이스 1: <hp:t> 하나에 base_text 발견 → 해당 <hp:t>만 치환
      - 케이스 2: 분산 run (<hp:t> 여러 개에 나뉨) → 합산 텍스트로 치환 (A2 수정)
    """
    label_counts = label_counts or {}

    for base_text, values in ordered_map.items():
        if not base_text or not values:
            continue

        skip = label_counts.get(base_text, 0)  # 라벨 셀 수 (앞에서 스킵할 개수)
        total_occ = [0]   # 라벨+값 전체 카운터
        val_occ = [0]     # 값 셀 카운터

        def _replace_para(para_match,
                          _base=base_text, _vals=values,
                          _total=total_occ, _vcnt=val_occ, _skip=skip):
            para = para_match.group(0)
            t_matches = list(re.finditer(r"<hp:t>(.*?)</hp:t>", para, re.DOTALL))
            if not t_matches:
                return para

            # 케이스 1: 단일 <hp:t>에서 base_text 발견 여부 (정확 매칭 우선)
            # substring 매칭 금지: "기간"이 "교육기간(이수시간)" 안에서 오탐하는 것을 방지
            single_hit_idx = None
            for i, m in enumerate(t_matches):
                inner_clean = re.sub(r"<[^>]+>", "", m.group(1)).strip()
                if inner_clean == _base:  # 정확 매칭만 허용
                    single_hit_idx = i
                    break

            # 케이스 2: 분산 run — 합산 텍스트가 base_text와 정확히 일치하는지
            combined_clean = "".join(
                re.sub(r"<[^>]+>", "", m.group(1)) for m in t_matches
            )
            has_in_combined = combined_clean.strip() == _base

            if single_hit_idx is None and not has_in_combined:
                return para  # 이 문단에 base_text 없음

            t_idx = _total[0]
            _total[0] += 1

            if t_idx < _skip:
                return para  # 라벨 셀 구간: 원본 유지 (치환하지 않음)

            v_idx = _vcnt[0]
            _vcnt[0] += 1

            if v_idx >= len(_vals) or not _vals[v_idx]:
                return para  # 해당 순번 값 없음: 원본 유지

            new_val = saxutils.escape(_vals[v_idx])

            if single_hit_idx is not None:
                # 케이스 1: 해당 <hp:t>에서만 치환
                m = t_matches[single_hit_idx]
                inner = m.group(1)
                parts = re.split(r"(<[^>]+>)", inner)
                result_parts = []
                for part in parts:
                    if part.startswith("<"):
                        result_parts.append(part)
                    elif part.strip() == _base:  # 정확 매칭
                        result_parts.append(new_val)
                    else:
                        result_parts.append(part)
                new_t = "<hp:t>" + "".join(result_parts) + "</hp:t>"
                return para.replace(m.group(0), new_t, 1)
            else:
                # 케이스 2: 분산 run → 합산 텍스트로 치환, 첫 <hp:t>에 결과 넣기
                replaced = combined_clean.replace(_base, new_val, 1)
                result = para
                for i, m in enumerate(t_matches):
                    old_tag = m.group(0)
                    new_tag = f"<hp:t>{replaced}</hp:t>" if i == 0 else "<hp:t></hp:t>"
                    result = result.replace(old_tag, new_tag, 1)
                return result

        xml_text = re.sub(
            r"<hp:p\b[^>]*>.*?</hp:p>",
            _replace_para,
            xml_text,
            flags=re.DOTALL,
        )

    return xml_text


def clone(src_path, dst_path, replacements=None, keywords=None,
          title=None, creator=None, strip_images=False, label_counts=None):
    """HWPX 양식을 복제하고 텍스트를 치환한다.

    Args:
        src_path: 원본 .hwpx 파일 경로
        dst_path: 출력 .hwpx 파일 경로
        replacements: Phase 1 구문 치환 dict (old → new)
        keywords: Phase 2 키워드 치환 dict (old → new), <hp:t> 내부에서만 적용
        title: 문서 제목 (메타데이터)
        creator: 작성자 (메타데이터)
        label_counts: {base_text: 라벨 셀 수} — __N 치환 시 앞 N개 occurrence 스킵
    """
    # __N 접미사 키 분리 (순서 기반 치환 vs 일반 치환)
    normal_repl, ordered_repl = _split_ordered_replacements(replacements or {})
    # 긴 키 우선 정렬: "중소벤처기업부 장관"이 "중소벤처기업부"보다 먼저 매칭되어야 함
    replacements = dict(sorted(normal_repl.items(), key=lambda x: len(x[0]), reverse=True))
    sorted_keywords = _prepare_keywords(keywords) if keywords else []

    tmp_path = dst_path + ".tmp"

    with zipfile.ZipFile(src_path, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            # mimetype을 반드시 첫 번째 엔트리로 (OPF 규격)
            if "mimetype" in zin.namelist():
                info = zin.getinfo("mimetype")
                zout.writestr(info, zin.read("mimetype"), compress_type=zipfile.ZIP_STORED)

            for item in zin.infolist():
                if item.filename == "mimetype":
                    continue  # 이미 처리

                # 이미지 제거 모드: BinData/ 파일 스킵
                if strip_images and item.filename.startswith("BinData/"):
                    continue

                data = zin.read(item.filename)

                if item.filename.startswith("Contents/") and item.filename.endswith(".xml"):
                    text = data.decode("utf-8")

                    # section XML에서 linesegarray 제거 (레이아웃 캐시 → 한글이 자동 재계산)
                    if item.filename.startswith("Contents/section"):
                        text = re.sub(
                            r"<hp:linesegarray>.*?</hp:linesegarray>",
                            "", text, flags=re.DOTALL,
                        )
                        # 이미지 제거 모드: <hp:pic> 요소 제거
                        if strip_images:
                            text = re.sub(
                                r"<hp:pic\b[^>]*>.*?</hp:pic>",
                                "", text, flags=re.DOTALL,
                            )

                    # fieldBegin~fieldEnd 영역 보호 (하이퍼링크, 날짜 필드 등)
                    # 치환 전에 마커로 치환하고, 치환 후 복원
                    _field_regions = []
                    def _protect_field(m):
                        _field_regions.append(m.group(0))
                        return f"__FIELD_PROTECTED_{len(_field_regions) - 1}__"
                    text = re.sub(
                        r"<hp:fieldBegin\b[^>]*>.*?<hp:fieldEnd\b[^>]*/>",
                        _protect_field, text, flags=re.DOTALL,
                    )

                    # Phase -1: __N 순서 기반 치환 (중복 셀 개별 처리)
                    if ordered_repl:
                        text = _apply_ordered_in_xml(text, ordered_repl, label_counts=label_counts)

                    # Phase 0: run 경계 병합 치환
                    if replacements:
                        text = _replace_across_runs(text, replacements)

                    # Phase 1: <hp:t> 태그 내부에서만 구문 치환 (XML 속성 보호)
                    if replacements:
                        def _replace_in_t(match):
                            inner = match.group(1)
                            # [Fix 2] 인라인 태그 제거한 텍스트로 매칭 시도
                            inner_clean = re.sub(r"<[^>]+>", "", inner)
                            for old_text, new_text in replacements.items():
                                escaped = saxutils.escape(new_text)
                                if old_text in inner:
                                    # 직접 매칭 (인라인 태그 없는 경우)
                                    inner = inner.replace(old_text, escaped)
                                elif old_text in inner_clean:
                                    # 인라인 태그(lineBreak, fwSpace 등)가 텍스트를 분할한 경우
                                    inline_tags = re.findall(r"<[^>]+>", inner)
                                    stripped = re.sub(r"<[^>]+>", "", inner)
                                    stripped = stripped.replace(old_text, escaped)
                                    inner = stripped
                            return "<hp:t>" + inner + "</hp:t>"
                        text = re.sub(r"<hp:t>(.*?)</hp:t>", _replace_in_t, text, flags=re.DOTALL)

                    # Phase 2: 키워드 수준 치환 (<hp:t> 내부만)
                    if sorted_keywords:
                        text = _apply_keywords_in_xml(text, sorted_keywords)

                    # fieldBegin~fieldEnd 영역 복원
                    for idx, region in enumerate(_field_regions):
                        text = text.replace(f"__FIELD_PROTECTED_{idx}__", region)

                    # 메타데이터 치환 (content.hpf의 제목/작성자)
                    if item.filename == "Contents/content.hpf":
                        if title:
                            text = re.sub(
                                r"(<dc:title>).*?(</dc:title>)",
                                rf"\1{title}\2",
                                text,
                            )
                        if creator:
                            text = re.sub(
                                r"(<dc:creator>).*?(</dc:creator>)",
                                rf"\1{creator}\2",
                                text,
                            )

                    data = text.encode("utf-8")

                zout.writestr(item, data)

    os.replace(tmp_path, dst_path)


def validate_result(src_path, dst_path, replacements=None, keywords=None):
    """치환 결과를 검증한다. 내용 기반으로 원본 텍스트가 결과에 남아있는지 확인.

    Returns:
        dict: {total_originals, replaced, remaining, remaining_texts, coverage_pct}
    """
    replacements = replacements or {}
    keywords = keywords or {}
    all_old_terms = set(replacements.keys()) | set(keywords.keys())

    if not all_old_terms:
        total = len(extract_texts(src_path))
        return {"total_originals": total, "replaced": 0, "remaining": total,
                "remaining_texts": [], "coverage_pct": 0.0}

    # 결과 파일의 전체 텍스트를 하나로 합침 (위치 무관, 내용만 확인)
    result_texts = set(_extract_all_hpt(dst_path))

    target_count = 0
    changed_count = 0
    remaining_samples = []

    # 치환 대상 키 각각이 결과에 남아있는지 확인
    for old_text in all_old_terms:
        if not old_text or len(old_text) <= 1:
            continue
        target_count += 1
        # 결과 텍스트 어디에도 원본이 남아있지 않으면 → 치환 성공
        still_exists = any(old_text in rt for rt in result_texts)
        if not still_exists:
            changed_count += 1
        else:
            if len(remaining_samples) < 20:
                remaining_samples.append(old_text[:60])

    remaining = target_count - changed_count
    coverage = (changed_count / max(target_count, 1)) * 100

    return {
        "total_originals": target_count,
        "replaced": changed_count,
        "remaining": remaining,
        "remaining_texts": remaining_samples,
        "coverage_pct": coverage,
    }


def _extract_all_hpt(hwpx_path):
    """HWPX에서 모든 <hp:t> 텍스트를 순서대로 추출 (중복 포함)."""
    texts = []
    with zipfile.ZipFile(hwpx_path, "r") as zf:
        for name in sorted(zf.namelist()):
            if name.startswith("Contents/") and name.endswith(".xml"):
                data = zf.read(name).decode("utf-8")
                for m in re.finditer(r"<hp:t>(.*?)</hp:t>", data, re.DOTALL):
                    clean = re.sub(r"<[^>]+>", "", m.group(1)).strip()
                    if clean:
                        texts.append(clean)
    return texts


def build_header_slot_map(hwpx_path):
    """[H] 헤더 셀의 인접 빈 값 셀 좌표를 구축한다.

    Returns:
        dict: {
            header_text: [
                {"file": "Contents/section0.xml", "tbl": tbl_idx, "row": row_addr, "col": col_addr},
                ...  # 복수 슬롯 (세로형: 아래로 여러 행)
            ]
        }
    """
    result = {}

    with zipfile.ZipFile(hwpx_path, 'r') as zf:
        bf_colors, cp_bold = {}, {}
        if 'Contents/header.xml' in zf.namelist():
            try:
                bf_colors, cp_bold = _parse_header_styles(zf.read('Contents/header.xml'))
            except Exception:
                pass

        for fname in sorted(zf.namelist()):
            if not (fname.startswith('Contents/') and fname.endswith('.xml')
                    and fname != 'Contents/header.xml'):
                continue

            try:
                root = etree.fromstring(zf.read(fname))
            except Exception:
                continue

            for tbl_idx, tbl in enumerate(root.findall('.//hp:tbl', _NS)):
                row_cnt = int(tbl.get('rowCnt', '0'))
                col_cnt = int(tbl.get('colCnt', '0'))
                if row_cnt == 0 or col_cnt == 0:
                    continue

                # 물리 셀 목록: (row, col, text, is_header)
                phys_cells = []
                bold_positions: set = set()   # bold 셀 위치 (수직 스캔 경계)
                bg_positions: set = set()     # bg-색상 셀 위치 (빈칸 구분자 판별)
                for tc in tbl.findall('hp:tr/hp:tc', _NS):
                    addr = tc.find('hp:cellAddr', _NS)
                    if addr is None:
                        continue
                    r = int(addr.get('rowAddr', '0'))
                    c = int(addr.get('colAddr', '0'))
                    text = _get_cell_text(tc)
                    bf_id = tc.get('borderFillIDRef', '')
                    has_bg = bf_colors.get(bf_id, False)
                    # bold도 헤더로 인식 (bg 없어도)
                    run = tc.find('.//hp:run', _NS)
                    is_bold = False
                    if run is not None:
                        cp_id = run.get('charPrIDRef', '')
                        is_bold = cp_bold.get(cp_id, False)
                    is_h = has_bg or is_bold
                    phys_cells.append((r, c, text, is_h))
                    if is_bold:
                        bold_positions.add((r, c))
                    if has_bg:
                        bg_positions.add((r, c))

                # 헤더 위치 룩업 (가로 스캔 시 경계 판별용)
                header_positions = {(r, c) for (r, c, t, h) in phys_cells if h}

                # 헤더 셀별 슬롯 탐색
                for hr, hc, ht, is_h in phys_cells:
                    if not (is_h and ht.strip()):
                        continue

                    # ─ 방향 1: 같은 행 오른쪽 빈 셀 탐색 (가로형)
                    # 서브라벨(비헤더 텍스트)은 건너뛰고, 다른 헤더 셀에서만 중단
                    right = [(c, t) for (r, c, t, h) in phys_cells
                             if r == hr and c > hc]
                    right.sort(key=lambda x: x[0])

                    found_right = False
                    for rc, rt in right:
                        if not rt.strip():
                            # 빈 셀 = 슬롯
                            slot = {"file": fname, "tbl": tbl_idx, "row": hr, "col": rc}
                            result.setdefault(ht, [])
                            if slot not in result[ht]:
                                result[ht].append(slot)
                            found_right = True
                        elif (hr, rc) in header_positions:
                            # 다른 헤더 셀 = 경계, 스캔 종료
                            break
                        elif found_right:
                            # 빈 슬롯 발견 후 비헤더 텍스트 = 다른 서브라벨/영역 시작 → 중단
                            # (예: 성명|한글|[empty]|한문|[empty] 에서 한문 이후 슬롯 오염 방지)
                            break
                        # else: 첫 빈 셀 전 서브라벨 → 건너뜀 (H.P 등 그냥 통과)

                    if found_right:
                        continue

                    # ─ 방향 2: 같은 열 아래에서 빈 셀들 탐색 (세로형)
                    below = [(r, t, h) for (r, c, t, h) in phys_cells
                             if c == hc and r > hr]
                    below.sort(key=lambda x: x[0])

                    for br, bt, bh in below:
                        if not bt.strip():
                            # bg 색상 있는 빈 셀 = 구분자(배경 행) → 슬롯 아님
                            if (br, hc) in bg_positions:
                                continue
                            slot = {"file": fname, "tbl": tbl_idx, "row": br, "col": hc}
                            result.setdefault(ht, [])
                            if slot not in result[ht]:
                                result[ht].append(slot)
                        elif bt.strip() in ('~', '∼', '·', '-', '─'):
                            continue  # 구분자 셀은 스킵
                        elif (br, hc) in bold_positions:
                            break  # 굵은 섹션 헤더 → 영역 종료
                        elif bh:
                            continue  # bg-only 라벨(제목 : 등) → 통과, 아래로 계속
                        else:
                            break  # 일반 값 텍스트 → 세로 탐색 종료

                # ─ _FORM_SUB_LABELS 추가 스캔: E-MAIL / H.P 등 서브라벨도
                #   자신의 바로 오른쪽 빈 셀을 슬롯으로 등록 (ai_mapper와 동기화)
                for sr, sc, st, _ in phys_cells:
                    label = st.strip()
                    if label not in _FORM_SUB_LABELS:
                        continue
                    right_sub = [(c, t) for (r, c, t, h) in phys_cells
                                 if r == sr and c > sc]
                    right_sub.sort(key=lambda x: x[0])
                    for rc, rt in right_sub:
                        if not rt.strip():
                            slot = {"file": fname, "tbl": tbl_idx, "row": sr, "col": rc}
                            result.setdefault(label, [])
                            if slot not in result[label]:
                                result[label].append(slot)
                            break  # 서브라벨은 바로 다음 빈 셀 하나만
                        elif (sr, rc) in header_positions:
                            break  # 헤더 경계 = 종료

    return result


def inject_values_by_slot(src_path, dst_path, slot_assignments):
    """슬롯 좌표에 지정된 값을 주입하여 새 HWPX를 생성한다.

    slot_assignments: [
        {"file": "Contents/section0.xml", "tbl": tbl_idx, "row": row_addr, "col": col_addr, "value": "텍스트"},
        ...
    ]
    """
    # 파일별로 그룹핑
    by_file = {}
    for sa in slot_assignments:
        fn = sa["file"]
        by_file.setdefault(fn, []).append(sa)

    tmp_path = dst_path + ".inj.tmp"

    with zipfile.ZipFile(src_path, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            if "mimetype" in zin.namelist():
                info = zin.getinfo("mimetype")
                zout.writestr(info, zin.read("mimetype"), compress_type=zipfile.ZIP_STORED)

            for item in zin.infolist():
                if item.filename == "mimetype":
                    continue
                data = zin.read(item.filename)

                if item.filename in by_file:
                    text = data.decode("utf-8")
                    assignments = by_file[item.filename]

                    # 테이블 인덱스별로 그룹핑
                    by_tbl = {}
                    for sa in assignments:
                        by_tbl.setdefault(sa["tbl"], []).append(sa)

                    # 테이블 블록을 순서대로 분할하여 처리
                    tbl_idx_global = [0]  # 전체 tbl 카운터

                    def _process_tbl(m, _by_tbl=by_tbl, _counter=tbl_idx_global):
                        tbl_text = m.group(0)
                        ti = _counter[0]
                        _counter[0] += 1

                        if ti not in _by_tbl:
                            return tbl_text

                        for sa in _by_tbl[ti]:
                            tbl_text = _inject_into_cell_xml(
                                tbl_text, sa["row"], sa["col"], sa["value"]
                            )
                        return tbl_text

                    text = re.sub(
                        r'<hp:tbl\b[^>]*>.*?</hp:tbl>',
                        _process_tbl,
                        text,
                        flags=re.DOTALL,
                    )
                    # pageBreak="NONE" 표는 페이지 범위를 벗어나면 화면에서 사라짐.
                    # 값 주입 후 CELL 분리 허용으로 변경 (한글뷰어 정상 스크롤 보장)
                    text = text.replace('pageBreak="NONE"', 'pageBreak="CELL"')
                    data = text.encode("utf-8")

                zout.writestr(item, data)

    os.replace(tmp_path, dst_path)


def _expand_cell_height(tc_block, value):
    """주입된 텍스트 길이에 맞게 셀 높이를 확장한다.
    한글 11.5pt 기준 1줄 ≈ 500 HWPUNIT, 여유 포함 600으로 계산.
    """
    # 대략적 줄 수 추정: 한글 기준 1줄에 약 35자
    line_count = max(len(value) // 35, 1) + 1  # 여유 +1줄
    needed_height = line_count * 600  # 1줄당 600 HWPUNIT

    m = re.search(r'(<hp:cellSz\b[^>]*height=")(\d+)(")', tc_block)
    if m:
        current = int(m.group(2))
        if needed_height > current:
            tc_block = tc_block[:m.start(2)] + str(needed_height) + tc_block[m.end(2):]
    return tc_block


def _inject_into_cell_xml(tbl_text, row_addr, col_addr, value):
    """테이블 XML에서 (row_addr, col_addr) 셀을 찾아 텍스트를 주입한다."""
    if not value:
        return tbl_text

    escaped = saxutils.escape(value)

    # cellAddr 패턴 (속성 순서 무관)
    # HWPX는 colAddr 먼저, rowAddr 나중 순서로 생성됨
    cell_addr_patterns = [
        rf'<hp:cellAddr\s+colAddr="{col_addr}"\s+rowAddr="{row_addr}"\s*/>',
        rf'<hp:cellAddr\s+rowAddr="{row_addr}"\s+colAddr="{col_addr}"\s*/>',
    ]

    for pat in cell_addr_patterns:
        m = re.search(pat, tbl_text)
        if not m:
            continue

        # cellAddr 위치 기준으로 앞쪽 <hp:tc> 시작 찾기
        tc_start = tbl_text.rfind('<hp:tc ', 0, m.start())
        if tc_start == -1:
            continue
        tc_end = tbl_text.find('</hp:tc>', m.end())
        if tc_end == -1:
            continue
        tc_end += len('</hp:tc>')

        tc_block = tbl_text[tc_start:tc_end]

        # 이미 텍스트가 있으면 스킵 (값칸이 비어있어야만 주입)
        existing_texts = re.findall(r'<hp:t>(.*?)</hp:t>', tc_block, re.DOTALL)
        existing = ''.join(re.sub(r'<[^>]+>', '', t) for t in existing_texts).strip()
        if existing:
            return tbl_text  # 이미 채워진 셀 → 스킵

        # ① 빈 <hp:t></hp:t> 이 있는 경우: 텍스트 주입
        if '<hp:t></hp:t>' in tc_block:
            new_block = tc_block.replace('<hp:t></hp:t>', f'<hp:t>{escaped}</hp:t>', 1)
            new_block = _expand_cell_height(new_block, value)
            return tbl_text[:tc_start] + new_block + tbl_text[tc_end:]

        # ② self-closing <hp:run ... /> 이 있는 경우: <hp:t> 삽입
        run_sc_pat = r'<hp:run\b[^>]*/>'
        run_m = re.search(run_sc_pat, tc_block)
        if run_m:
            orig_run = run_m.group(0)
            open_run = orig_run[:-2] + '>'
            new_run = f'{open_run}<hp:t>{escaped}</hp:t></hp:run>'
            new_block = tc_block[:run_m.start()] + new_run + tc_block[run_m.end():]
            new_block = _expand_cell_height(new_block, value)
            return tbl_text[:tc_start] + new_block + tbl_text[tc_end:]

        # ③ <hp:run>...</hp:run> 이 있지만 hp:t 없는 경우
        run_open_pat = r'<hp:run\b[^>]*>((?:(?!</hp:run>).)*)</hp:run>'
        run_m = re.search(run_open_pat, tc_block, re.DOTALL)
        if run_m:
            run_inner = run_m.group(1)
            new_run = run_m.group(0).replace(
                '</hp:run>', f'<hp:t>{escaped}</hp:t></hp:run>', 1
            )
            new_block = tc_block[:run_m.start()] + new_run + tc_block[run_m.end():]
            new_block = _expand_cell_height(new_block, value)
            return tbl_text[:tc_start] + new_block + tbl_text[tc_end:]

        break  # cellAddr 찾았지만 주입 패턴 없음 → 중단

    return tbl_text


def main():
    parser = argparse.ArgumentParser(
        description="HWPX 양식 복제 도구 (Workflow F)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 양식 분석
  python clone_form.py --analyze sample.hwpx

  # JSON 맵으로 복제
  python clone_form.py sample.hwpx output.hwpx --map replacements.json

  # 키워드 폴백 추가
  python clone_form.py sample.hwpx output.hwpx --map map.json --keywords kw.json

  # CLI 직접 치환
  python clone_form.py sample.hwpx output.hwpx --replace "원본=대체" "A=B"
""",
    )
    parser.add_argument("source", help="원본 HWPX 파일")
    parser.add_argument("output", nargs="?", help="출력 HWPX 파일")
    parser.add_argument("--analyze", action="store_true", help="양식 분석 모드")
    parser.add_argument("--auto-analyze", metavar="JSON", help="자동 분석 + 치환 맵 템플릿 JSON 출력")
    parser.add_argument("--map", help="구문 치환 JSON 파일 (Phase 1)")
    parser.add_argument("--keywords", help="키워드 치환 JSON 파일 (Phase 2)")
    parser.add_argument("--replace", nargs="*", help="CLI 치환 쌍 (old=new)")
    parser.add_argument("--title", help="문서 제목 메타데이터")
    parser.add_argument("--creator", help="작성자 메타데이터")
    parser.add_argument("--validate", action="store_true", help="치환 후 검증 실행")

    args = parser.parse_args()

    if not os.path.exists(args.source):
        print(f"Error: 파일을 찾을 수 없음: {args.source}")
        sys.exit(1)

    # 분석 모드
    if args.analyze:
        analyze(args.source)
        return

    # 자동 분석 모드
    if args.auto_analyze:
        auto_analyze(args.source, args.auto_analyze)
        return

    # 복제 모드
    if not args.output:
        print("Error: 출력 파일을 지정하세요.")
        sys.exit(1)

    # 치환 맵 구성
    replacements = {}
    if args.map:
        with open(args.map, "r", encoding="utf-8") as f:
            replacements = json.load(f)
        print(f"구문 치환 맵: {len(replacements)}개 항목 ({args.map})")

    if args.replace:
        for pair in args.replace:
            if "=" not in pair:
                print(f"Warning: 잘못된 치환 쌍 무시: {pair}")
                continue
            old, new = pair.split("=", 1)
            replacements[old] = new
        print(f"CLI 치환: {len(args.replace)}개 추가")

    keywords = None
    if args.keywords:
        with open(args.keywords, "r", encoding="utf-8") as f:
            keywords = json.load(f)
        print(f"키워드 폴백 맵: {len(keywords)}개 항목 ({args.keywords})")

    # 복제 실행
    clone(args.source, args.output, replacements, keywords,
          title=args.title, creator=args.creator)
    print(f"복제 완료: {args.output}")

    # 검증
    if args.validate:
        validate_result(args.source, args.output, replacements, keywords)


if __name__ == "__main__":
    main()
