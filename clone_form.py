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


def detect_labels(hwpx_path):
    """HWPX 표 구조에서 라벨(헤더) 텍스트를 탐지한다.

    표의 첫 열에 있는 짧은 텍스트(20자 이하)를 라벨로 간주.
    이 목록은 AI에게 "이건 치환하지 마세요"라고 알려주는 용도.

    Returns:
        set[str]: 라벨로 판별된 텍스트 집합
    """
    labels = set()

    with zipfile.ZipFile(hwpx_path, "r") as zf:
        for name in zf.namelist():
            if not (name.startswith("Contents/section") and name.endswith(".xml")):
                continue
            data = zf.read(name).decode("utf-8")

            for tbl in re.finditer(r"<hp:tbl\b[^>]*>(.*?)</hp:tbl>", data, re.DOTALL):
                for row in re.finditer(r"<hp:tr\b[^>]*>(.*?)</hp:tr>", tbl.group(1), re.DOTALL):
                    cells = list(re.finditer(
                        r"<hp:tc\b[^>]*>(.*?)</hp:tc>", row.group(1), re.DOTALL
                    ))
                    if len(cells) < 2:
                        continue

                    # 첫 셀 텍스트 추출
                    first_cell = cells[0].group(1)
                    hpts = re.findall(r"<hp:t>(.*?)</hp:t>", first_cell, re.DOTALL)
                    first_text = "".join(
                        re.sub(r"<[^>]+>", "", h).strip() for h in hpts
                    ).strip()

                    # 라벨 조건: 2~20자, 두 번째 셀보다 짧음
                    if not first_text or len(first_text) > 20:
                        continue

                    second_cell = cells[1].group(1) if len(cells) > 1 else ""
                    second_hpts = re.findall(r"<hp:t>(.*?)</hp:t>", second_cell, re.DOTALL)
                    second_text = "".join(
                        re.sub(r"<[^>]+>", "", h).strip() for h in second_hpts
                    ).strip()

                    if len(first_text) <= len(second_text) or not second_text:
                        labels.add(first_text)

    return labels


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

        # 위치 기반 교체: 뒤에서부터 교체하여 offset 밀림 방지
        result = para
        for i in range(len(t_matches) - 1, -1, -1):
            m = t_matches[i]
            start, end = m.start(), m.end()
            if i == 0:
                new_tag = "<hp:t>" + replaced_combined + "</hp:t>"
            else:
                new_tag = "<hp:t></hp:t>"
            result = result[:start] + new_tag + result[end:]

        return result

    return re.sub(r"<hp:p\b[^>]*>.*?</hp:p>", _replace_para, xml_text, flags=re.DOTALL)


def clone(src_path, dst_path, replacements=None, keywords=None,
          title=None, creator=None, strip_images=False):
    """HWPX 양식을 복제하고 텍스트를 치환한다.

    Args:
        src_path: 원본 .hwpx 파일 경로
        dst_path: 출력 .hwpx 파일 경로
        replacements: Phase 1 구문 치환 dict (old → new)
        keywords: Phase 2 키워드 치환 dict (old → new), <hp:t> 내부에서만 적용
        title: 문서 제목 (메타데이터)
        creator: 작성자 (메타데이터)
    """
    # 긴 키 우선 정렬: "중소벤처기업부 장관"이 "중소벤처기업부"보다 먼저 매칭되어야 함
    replacements = dict(sorted((replacements or {}).items(), key=lambda x: len(x[0]), reverse=True))
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
                    import uuid as _uuid
                    _field_marker = f"__FP_{_uuid.uuid4().hex[:12]}_"
                    _field_regions = []
                    def _protect_field(m):
                        _field_regions.append(m.group(0))
                        return f"{_field_marker}{len(_field_regions) - 1}__"
                    text = re.sub(
                        r"<hp:fieldBegin\b[^>]*>.*?<hp:fieldEnd\b[^>]*/>",
                        _protect_field, text, flags=re.DOTALL,
                    )

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
                        text = text.replace(f"{_field_marker}{idx}__", region)

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
