#!/usr/bin/env python3
"""
AI 매핑 품질 자동 검증 스크립트

사용법:
    python run_tests.py                     # 7개 TC 전부 실행
    python run_tests.py --tc TC-01          # 특정 TC만
    python run_tests.py --tc TC-01 TC-02    # 복수 선택
    python run_tests.py --dry-run           # A10 무결성 체크만 수행 (AI 호출 X)

결과 저장 위치:
    test-forms/results/YYYYMMDD_HHMMSS/
    ├── metadata.json          # A6: git hash, 날짜, 모델 등
    ├── summary.json           # 전체 TC 종합 결과
    ├── TC-01/
    │   ├── ai_response.json   # AI 원본 응답
    │   ├── mapping_result.json # 파싱 후 매핑
    │   ├── output.hwpx        # 최종 양식
    │   └── score.json         # 필드별 정답/오답 + 등급
    └── ...

체크 항목 (A-시리즈 적용):
    A1  Cross-check: test_spec.json 작성 시점에 이미 완료
    A2  필드 수 규칙: expected_only (test_spec.json)
    A4  Critical 필드: 하나라도 틀리면 D 강등
    A6  메타데이터: metadata.json 자동 기록
    A10 무결성 체크: --dry-run 또는 본 실행 전 사전 검증
    A13 JSON화 자동 채점: 이 스크립트 자체
"""

import sys
import os
import json
import re
import argparse
import subprocess
import tempfile
import shutil
import traceback
import time
from pathlib import Path
from datetime import datetime

# hwpx-converter 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

TEST_FORMS_DIR = PROJECT_ROOT / "test-forms"
SPEC_PATH = TEST_FORMS_DIR / "test_spec.json"
RESULTS_DIR = TEST_FORMS_DIR / "results"


# ─────────────────────────────────────────────────────────
# A10: 무결성 사전 체크
# ─────────────────────────────────────────────────────────

def check_integrity(spec):
    """테스트 실행 전 필수 파일/모듈 존재 확인.
    실패 항목은 리스트로 반환. 빈 리스트면 통과.
    """
    problems = []

    # 1. 필수 모듈 import 가능?
    try:
        from clone_form import extract_structured_fields, clone, build_header_slot_map, inject_values_by_slot  # noqa
    except ImportError as e:
        problems.append(f"[CRITICAL] clone_form import 실패: {e}")

    try:
        from ai_mapper import map_content  # noqa
    except ImportError as e:
        problems.append(f"[CRITICAL] ai_mapper import 실패: {e}")

    # 2. Gemini API 키 확인
    if not os.environ.get("GEMINI_API_KEY"):
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            content = env_path.read_text(encoding="utf-8")
            if "GEMINI_API_KEY" not in content:
                problems.append("[CRITICAL] GEMINI_API_KEY 미설정 (환경변수, .env 모두)")
        else:
            problems.append("[CRITICAL] GEMINI_API_KEY 미설정 + .env 없음")

    # 3. TC별 양식/입력 파일 존재 확인
    for tc in spec["test_cases"]:
        form_path = TEST_FORMS_DIR / tc["form_file"]
        input_path = TEST_FORMS_DIR / tc["input_file"]

        if not form_path.exists():
            problems.append(f"[{tc['id']}] 양식 파일 없음: {form_path}")
        if not input_path.exists():
            problems.append(f"[{tc['id']}] 입력 파일 없음: {input_path}")

    # 4. 양식이 열리는지 (파싱 가능?)
    try:
        from clone_form import extract_structured_fields
        for tc in spec["test_cases"]:
            form_path = TEST_FORMS_DIR / tc["form_file"]
            if not form_path.exists():
                continue
            # .hwp는 스킵 (로컬 COM 변환 필요 — 빠른 무결성 체크에선 생략)
            if form_path.suffix.lower() == ".hwp":
                continue
            try:
                s = extract_structured_fields(str(form_path))
                if not s.get("tables"):
                    problems.append(f"[{tc['id']}] 양식 파싱 OK지만 테이블 0개 (slot 매핑 불가)")
            except Exception as e:
                problems.append(f"[{tc['id']}] 양식 파싱 실패: {e}")
    except ImportError:
        pass  # 앞서 보고됨

    return problems


# ─────────────────────────────────────────────────────────
# A6: 메타데이터 수집
# ─────────────────────────────────────────────────────────

def collect_metadata():
    """환경 + 코드 버전 메타데이터. 결과와 함께 저장."""
    meta = {
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version.split()[0],
        "project_root": str(PROJECT_ROOT),
    }

    # git 상태
    try:
        git_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT,
            stderr=subprocess.DEVNULL, text=True
        ).strip()
        meta["git_commit"] = git_hash
    except Exception:
        meta["git_commit"] = "unknown"

    try:
        git_dirty = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=PROJECT_ROOT,
            stderr=subprocess.DEVNULL, text=True
        ).strip()
        meta["git_dirty"] = bool(git_dirty)
        meta["git_dirty_files"] = git_dirty.split("\n") if git_dirty else []
    except Exception:
        meta["git_dirty"] = None

    try:
        git_branch = subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=PROJECT_ROOT,
            stderr=subprocess.DEVNULL, text=True
        ).strip()
        meta["git_branch"] = git_branch
    except Exception:
        meta["git_branch"] = "unknown"

    # AI 모델 정보 (ai_mapper에서)
    try:
        from ai_mapper import MODEL_NAME  # type: ignore
        meta["ai_model"] = MODEL_NAME
    except Exception:
        meta["ai_model"] = os.environ.get("DOCFLOW_MODEL", "gemini-2.5-flash (default)")

    return meta


# ─────────────────────────────────────────────────────────
# AI 매핑 로컬 실행
# ─────────────────────────────────────────────────────────

def run_ai_mapping(form_path, input_path, output_hwpx):
    """로컬에서 AI 매핑 + 치환 전체 파이프라인 호출. form.py 경로 재현.

    Returns: (mapping_dict, meta_info, error_msg)
    """
    from clone_form import (
        extract_structured_fields, build_header_slot_map,
        inject_values_by_slot, clone,
    )
    from ai_mapper import map_content
    try:
        from kr_formatter import KrFormatter
    except ImportError:
        KrFormatter = None

    # .hwp인 경우 COM 변환 필요 — 로컬 Windows에선 file_manager 사용
    if form_path.suffix.lower() == ".hwp":
        try:
            from api.services.file_manager import FileManager
            fm = FileManager()
            fid = fm.save(str(form_path), form_path.name)
            fid2 = fm.convert_hwp(fid)
            hwpx_path = Path(fm.get_path(fid2))
        except Exception as e:
            return None, None, f"HWP→HWPX 변환 실패 (COM 필요): {e}"
    else:
        hwpx_path = form_path

    # 양식 구조 추출
    structured = extract_structured_fields(str(hwpx_path))
    form_texts = structured.get("flat_texts", [])

    # 입력 텍스트 읽기
    with open(input_path, "r", encoding="utf-8") as f:
        user_content = f.read()

    # 양식 타입 분류 (AI에 전달할 extra_labels 결정용)
    ai_extra_labels = None
    try:
        from processors.form_classifier import classify_form
        form_type_early = classify_form(structured)
        if form_type_early == "invoice_style":
            from processors.invoice_processor import INVOICE_LABELS
            ai_extra_labels = INVOICE_LABELS
        elif form_type_early == "government":
            from processors.government_processor import GOVERNMENT_LABELS
            ai_extra_labels = GOVERNMENT_LABELS
        elif form_type_early == "contract":
            from processors.contract_processor import CONTRACT_LABELS
            ai_extra_labels = CONTRACT_LABELS
        elif form_type_early == "proposal":
            from processors.proposal_processor import PROPOSAL_LABELS
            ai_extra_labels = PROPOSAL_LABELS
        elif form_type_early == "resume":
            from processors.resume_processor import RESUME_LABELS
            ai_extra_labels = RESUME_LABELS
    except Exception:
        pass

    # AI 매핑
    mapping, err = map_content(
        form_texts=form_texts,
        user_content=user_content,
        structured=structured,
        extra_labels=ai_extra_labels,
    )
    if err or mapping is None:
        return None, None, err or "매핑 결과 None"

    # form.py의 generate 엔드포인트 Phase 1/2 재현
    # label_counts 계산
    label_counts = {}
    seen_cell_ids = set()
    for table in structured.get("tables", []):
        for row in table["rows"]:
            for cell in row:
                cid = id(cell)
                if cid in seen_cell_ids:
                    continue
                seen_cell_ids.add(cid)
                if (cell.get("bold") or cell.get("bg")) and cell.get("text", "").strip():
                    t = cell["text"].strip()
                    label_counts[t] = label_counts.get(t, 0) + 1

    # 양식 타입 분류 + 슬롯 맵 빌드 (form.py와 동일)
    form_type = "legacy"
    try:
        from processors.form_classifier import classify_form
        form_type = classify_form(structured)
        print(f"[classify] form_type={form_type}")
    except Exception as cls_e:
        print(f"[classify] 분류 실패 (legacy 폴백): {cls_e}")

    slot_map = {}
    try:
        if form_type == "invoice_style":
            from processors.invoice_processor import InvoiceProcessor
            proc = InvoiceProcessor(str(hwpx_path), structured)
            slot_map = proc.build_slot_map()
            print(f"[generate] invoice 슬롯 맵: {len(slot_map)}개 라벨")
        elif form_type == "government":
            from processors.government_processor import GovernmentProcessor
            proc = GovernmentProcessor(str(hwpx_path), structured)
            slot_map = proc.build_slot_map()
            print(f"[generate] government 슬롯 맵: {len(slot_map)}개 라벨")
        elif form_type == "contract":
            from processors.contract_processor import ContractProcessor
            proc = ContractProcessor(str(hwpx_path), structured)
            slot_map = proc.build_slot_map()
            print(f"[generate] contract (단락 기반, slot_map 빈값)")
        elif form_type == "proposal":
            # proposal은 build_header_slot_map 폴백
            slot_map = build_header_slot_map(str(hwpx_path))
            print(f"[generate] proposal: {len(slot_map)}개 헤더 탐지")
        elif form_type == "resume":
            slot_map = build_header_slot_map(str(hwpx_path))
            print(f"[generate] resume: {len(slot_map)}개 헤더 탐지")
        else:
            slot_map = build_header_slot_map(str(hwpx_path))
    except Exception as slot_e:
        print(f"[generate] 슬롯 맵 실패: {slot_e}")

    # 한국 포맷터
    formatted = dict(mapping)
    if KrFormatter is not None:
        try:
            fmt_result = KrFormatter.auto_detect_and_format(formatted)
            formatted = fmt_result["formatted"]
        except Exception:
            pass

    # 슬롯 주입용 vs 일반 치환 분리
    # __N__M (더블언더스코어 복수) 또는 __N_M (2D 인덱스) 접미사 제거
    _base_re = re.compile(r"(?:__\d+)+$|__\d+(?:_\d+)+$")
    _ws_re = re.compile(r"\s+")
    slot_map_norm = {_ws_re.sub("", k): k for k in slot_map}

    slot_assignments = []
    normal_repl = {}
    for key, value in formatted.items():
        base = _base_re.sub("", key)  # __N 또는 __N_M 접미사 제거
        suffix_match = _base_re.search(key)
        # suffix에서 모든 숫자 그룹 추출 (구형 __1__2, 신형 __1_2 모두 지원)
        indices = [int(x) for x in re.findall(r"\d+", suffix_match.group(0))] if suffix_match else []
        base_norm = _ws_re.sub("", base)
        real_key = slot_map_norm.get(base_norm)
        # 복합 키 폴백 1: "__" 세그먼트 마지막 부분
        if real_key is None and "__" in base:
            last_seg = base.split("__")[-1]
            if last_seg:
                real_key = slot_map_norm.get(_ws_re.sub("", last_seg))
        # 복합 키 폴백 2: base_norm이 슬롯키를 포함 → 슬롯 수 가장 적은 키 선택
        if real_key is None and slot_map_norm:
            candidates = [(snk, sk) for snk, sk in slot_map_norm.items()
                          if len(snk) >= 2 and snk in base_norm]
            if candidates:
                best = min(candidates, key=lambda x: len(slot_map[x[1]]))
                real_key = best[1]
        if real_key is not None and slot_map[real_key]:
            slots = slot_map[real_key]
            if indices:
                # 복수 인덱스 [a, b] → 평탄화 슬롯 인덱스로 변환
                # 단일 인덱스: idx = a - 1
                # 복수: 평탄화 공식 사용 (좌 양식 count만큼 건너뜀)
                if len(indices) == 1:
                    flat_idx = indices[0] - 1
                else:
                    # 좌(idx=1)는 0~n-1, 우(idx=2)는 n~2n-1 가정 (2분할 양식)
                    n = len(slots) // max(indices[0], 2)
                    flat_idx = (indices[0] - 1) * n + (indices[-1] - 1)
                if 0 <= flat_idx < len(slots):
                    sa = dict(slots[flat_idx])
                    sa["value"] = value
                    slot_assignments.append(sa)
            else:
                for slot in slots:
                    sa = dict(slot)
                    sa["value"] = value
                    slot_assignments.append(sa)
        else:
            normal_repl[key] = value

    # Phase 1: 슬롯 주입
    src_for_clone = str(hwpx_path)
    if slot_assignments:
        injected = tempfile.NamedTemporaryFile(suffix=".hwpx", delete=False).name
        inject_values_by_slot(str(hwpx_path), injected, slot_assignments)
        src_for_clone = injected

    # Phase 2: 일반 치환
    clone(src_for_clone, str(output_hwpx), replacements=normal_repl,
          label_counts=label_counts or None)

    return mapping, {
        "hwpx_path": str(hwpx_path),
        "output_hwpx": str(output_hwpx),
        "slot_count": len(slot_assignments),
        "normal_count": len(normal_repl),
    }, None


def extract_hwpx_text(hwpx_path):
    """완성된 hwpx에서 모든 <hp:t> 텍스트를 추출해 하나의 문자열로 반환."""
    import zipfile
    texts = []
    with zipfile.ZipFile(hwpx_path, "r") as zf:
        for name in zf.namelist():
            if name.startswith("Contents/") and name.endswith(".xml") and name != "Contents/header.xml":
                data = zf.read(name).decode("utf-8", errors="replace")
                for m in re.finditer(r"<hp:t>(.*?)</hp:t>", data, re.DOTALL):
                    clean = re.sub(r"<[^>]+>", "", m.group(1))
                    texts.append(clean)
    return "\n".join(texts)


# ─────────────────────────────────────────────────────────
# A2/A4: 채점
# ─────────────────────────────────────────────────────────

_WS = re.compile(r"\s+")


def normalize(s):
    """공백 정규화 + 소문자화."""
    return _WS.sub(" ", str(s)).strip().lower()


def match_substring_bi(expected, actual):
    """양방향 substring 매치. expected⊆actual 또는 actual⊆expected."""
    if not actual:
        return False
    e_norm = normalize(expected)
    a_norm = normalize(actual)
    if not e_norm:
        return False
    return e_norm in a_norm or a_norm in e_norm


def check_value_in_text(expected, hwpx_text):
    """기대값이 hwpx 본문 텍스트에 들어있는지 검사.
    공백/줄바꿈 정규화 후 substring 매치.
    """
    if not expected:
        return False
    e_norm = normalize(expected)
    t_norm = normalize(hwpx_text)
    return e_norm in t_norm


def score_tc(tc, hwpx_text):
    """최종 hwpx 본문에서 기대값 substring을 찾아 채점."""
    fields = tc["fields"]
    total = len(fields)
    correct = 0
    critical_failed = False
    field_results = []

    for field in fields:
        expected = field["expected"]
        critical = field.get("critical", False)

        is_correct = check_value_in_text(expected, hwpx_text)
        if is_correct:
            correct += 1
        elif critical:
            critical_failed = True

        field_results.append({
            "id": field["id"],
            "label": field["label"],
            "expected": expected,
            "critical": critical,
            "found_in_output": is_correct,
        })

    accuracy = (correct / total * 100) if total > 0 else 0

    if critical_failed:
        grade = "D"
        grade_reason = "critical_field_failed"
    elif accuracy >= 90:
        grade = "A"
        grade_reason = f"accuracy={accuracy:.1f}%"
    elif accuracy >= 75:
        grade = "B"
        grade_reason = f"accuracy={accuracy:.1f}%"
    elif accuracy >= 50:
        grade = "C"
        grade_reason = f"accuracy={accuracy:.1f}%"
    else:
        grade = "D"
        grade_reason = f"accuracy={accuracy:.1f}%"

    return {
        "tc_id": tc["id"],
        "name": tc["name"],
        "total_fields": total,
        "correct_fields": correct,
        "accuracy": accuracy,
        "grade": grade,
        "grade_reason": grade_reason,
        "critical_failed": critical_failed,
        "field_results": field_results,
    }


# ─────────────────────────────────────────────────────────
# 실행
# ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI 매핑 품질 자동 검증")
    parser.add_argument("--tc", nargs="+", default=None, help="실행할 TC ID")
    parser.add_argument("--dry-run", action="store_true", help="무결성 체크만")
    parser.add_argument("--spec", default=str(SPEC_PATH), help="스펙 JSON 경로")
    args = parser.parse_args()

    # 스펙 로드
    with open(args.spec, "r", encoding="utf-8") as f:
        spec = json.load(f)

    # A10: 무결성 체크
    print("=" * 60)
    print("[A10] 무결성 체크")
    print("=" * 60)
    problems = check_integrity(spec)
    if problems:
        print(f"[FAIL] {len(problems)}개 문제 발견:")
        for p in problems:
            print(f"  - {p}")
        if any("CRITICAL" in p for p in problems):
            print("\n[STOP] CRITICAL 문제로 실행 중단")
            return 1
        print("\n[WARN] CRITICAL 아닌 문제 — 계속 진행")
    else:
        print("[OK] 모든 항목 통과")
    print()

    if args.dry_run:
        print("[DRY RUN] 무결성 체크만 수행. 종료.")
        return 0

    # A6: 메타데이터
    print("=" * 60)
    print("[A6] 메타데이터 수집")
    print("=" * 60)
    meta = collect_metadata()
    for k, v in meta.items():
        if isinstance(v, list) and len(v) > 3:
            print(f"  {k}: {v[:3]} ... (+{len(v)-3}개)")
        else:
            print(f"  {k}: {v}")
    print()

    # 결과 디렉토리 생성
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RESULTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    with open(run_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # 필터링
    tcs = spec["test_cases"]
    if args.tc:
        tc_ids = set(args.tc)
        tcs = [tc for tc in tcs if tc["id"] in tc_ids]
        if not tcs:
            print(f"[ERROR] 매칭되는 TC 없음: {args.tc}")
            return 1

    # 각 TC 실행
    tc_results = []
    for tc in tcs:
        print("=" * 60)
        print(f"[{tc['id']}] {tc['name']}")
        print("=" * 60)

        form_path = TEST_FORMS_DIR / tc["form_file"]
        input_path = TEST_FORMS_DIR / tc["input_file"]

        tc_dir = run_dir / tc["id"]
        tc_dir.mkdir(exist_ok=True)
        output_hwpx = tc_dir / "output.hwpx"

        try:
            mapping, meta_info, err = run_ai_mapping(form_path, input_path, output_hwpx)
        except Exception as e:
            err = f"예외: {e}\n{traceback.format_exc()}"
            mapping = None

        if mapping is None:
            print(f"[FAIL] AI 매핑 실패: {err}")
            tc_results.append({
                "tc_id": tc["id"],
                "name": tc["name"],
                "error": err,
                "grade": "ERROR",
            })
            with open(tc_dir / "error.txt", "w", encoding="utf-8") as f:
                f.write(err)
            if len(tcs) > 1:
                time.sleep(2)
            continue

        # AI 매핑 원본 저장
        with open(tc_dir / "mapping_result.json", "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)

        # 최종 hwpx 본문 추출
        try:
            hwpx_text = extract_hwpx_text(output_hwpx)
            with open(tc_dir / "output_text.txt", "w", encoding="utf-8") as f:
                f.write(hwpx_text)
        except Exception as e:
            print(f"[FAIL] 본문 추출 실패: {e}")
            tc_results.append({
                "tc_id": tc["id"],
                "name": tc["name"],
                "error": f"본문 추출 실패: {e}",
                "grade": "ERROR",
            })
            if len(tcs) > 1:
                time.sleep(2)
            continue

        # 채점
        score = score_tc(tc, hwpx_text)
        with open(tc_dir / "score.json", "w", encoding="utf-8") as f:
            json.dump(score, f, ensure_ascii=False, indent=2)

        print(f"  정확도: {score['correct_fields']}/{score['total_fields']} ({score['accuracy']:.1f}%)")
        print(f"  등급: {score['grade']} ({score['grade_reason']})")
        if score["critical_failed"]:
            print(f"  [!] critical 필드 실패로 D 강등")
            failed = [fr for fr in score["field_results"]
                      if not fr["found_in_output"] and fr["critical"]]
            for fr in failed:
                print(f"      - {fr['label']}: 기대={fr['expected']!r} (출력물에 없음)")

        tc_results.append(score)
        print()
        # TC 간 API 부하 완화 (연속 실행 시 rate limit / 불량 응답 방지)
        if len(tcs) > 1:
            time.sleep(2)

    # 종합 결과
    print("=" * 60)
    print("[종합 결과]")
    print("=" * 60)
    summary = {
        "run_id": run_id,
        "metadata": meta,
        "tc_count": len(tc_results),
        "results": tc_results,
    }
    with open(run_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"| {'TC':<6} | {'양식':<15} | {'정확도':<12} | {'등급':<4} | 특이사항 |")
    print(f"| {'-'*6} | {'-'*15} | {'-'*12} | {'-'*4} | {'-'*20} |")
    for r in tc_results:
        if r.get("error"):
            print(f"| {r['tc_id']:<6} | {r['name']:<15} | {'ERROR':<12} | {r['grade']:<4} | {r['error'][:30]} |")
        else:
            acc_str = f"{r['correct_fields']}/{r['total_fields']} ({r['accuracy']:.0f}%)"
            note = "critical 실패" if r.get("critical_failed") else ""
            print(f"| {r['tc_id']:<6} | {r['name']:<15} | {acc_str:<12} | {r['grade']:<4} | {note:<20} |")

    print(f"\n[OK] 결과 저장: {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
