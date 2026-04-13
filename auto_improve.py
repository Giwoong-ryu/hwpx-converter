"""
4일 반자동 개선 시스템 — AI 프롬프트 규칙 자동 생성/검증/적용

사용법:
    python auto_improve.py --baseline     # 기준선 확립 (3회 실행)
    python auto_improve.py --once         # 1회 iteration (테스트용)
    python auto_improve.py                # 전체 루프 (4일 자동)

안전장치:
    - 수정 대상: ai_mapper.py SYSTEM_PROMPT Rule만
    - 3회 실행으로 AI 변동성 흡수
    - 회귀 시 자동 revert (git stash)
    - max_new_rules=4 (4일간 최대 4개)
"""

import sys
import os
import json
import re
import time
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from copy import deepcopy

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

CONFIG_PATH = PROJECT_ROOT / "auto_improve_config.json"
BASELINE_PATH = PROJECT_ROOT / "auto_improve_baseline.json"
LOG_PATH = PROJECT_ROOT / "auto_improve_log.json"
MAPPER_PATH = PROJECT_ROOT / "ai_mapper.py"

# run_tests.py 함수 import
sys.path.insert(0, str(PROJECT_ROOT / "test-forms"))
from run_tests import (
    run_ai_mapping, extract_hwpx_text, score_tc,
    check_integrity, collect_metadata, SPEC_PATH, TEST_FORMS_DIR, RESULTS_DIR,
)


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_spec():
    with open(SPEC_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_log():
    if LOG_PATH.exists():
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"iterations": [], "rules_added": 0}


def save_log(log):
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


# ── 7TC 1회 실행 ──

def run_all_tcs(spec, target_tcs=None):
    """7TC 실행 후 TC별 점수 반환. target_tcs=None이면 전체."""
    import tempfile
    tcs = spec["test_cases"]
    if target_tcs:
        tc_ids = set(target_tcs)
        tcs = [tc for tc in spec["test_cases"] if tc["id"] in tc_ids]

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RESULTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    for tc in tcs:
        form_path = TEST_FORMS_DIR / tc["form_file"]
        input_path = TEST_FORMS_DIR / tc["input_file"]
        tc_dir = run_dir / tc["id"]
        tc_dir.mkdir(exist_ok=True)
        output_hwpx = tc_dir / "output.hwpx"

        try:
            mapping, meta_info, err = run_ai_mapping(form_path, input_path, output_hwpx)
        except Exception as e:
            err = str(e)
            mapping = None

        if mapping is None:
            results[tc["id"]] = {
                "score": 0, "grade": "ERROR", "error": err,
                "fields": {},
            }
            with open(tc_dir / "error.txt", "w", encoding="utf-8") as f:
                f.write(err or "unknown")
            time.sleep(2)
            continue

        with open(tc_dir / "mapping_result.json", "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)

        try:
            hwpx_text = extract_hwpx_text(output_hwpx)
        except Exception:
            results[tc["id"]] = {"score": 0, "grade": "ERROR", "fields": {}}
            time.sleep(2)
            continue

        score = score_tc(tc, hwpx_text)
        with open(tc_dir / "score.json", "w", encoding="utf-8") as f:
            json.dump(score, f, ensure_ascii=False, indent=2)

        field_map = {}
        for fr in score["field_results"]:
            field_map[fr["id"]] = fr["found_in_output"]

        results[tc["id"]] = {
            "score": score["correct_fields"],
            "total": score["total_fields"],
            "grade": score["grade"],
            "fields": field_map,
        }

        print(f"  {tc['id']}: {score['correct_fields']}/{score['total_fields']} {score['grade']}")
        time.sleep(2)

    return results, run_id


# ── 기준선 확립 ──

def build_baseline(spec, config):
    """N회 실행으로 TC별 min/max/field_pass_rate 확보."""
    n = config["baseline_runs"]
    print(f"\n[BASELINE] {n}회 실행 시작")

    all_runs = []
    for i in range(n):
        print(f"\n--- Baseline Run {i+1}/{n} ---")
        results, run_id = run_all_tcs(spec)
        all_runs.append(results)

    baseline = {}
    for tc in spec["test_cases"]:
        tid = tc["id"]
        scores = [r.get(tid, {}).get("score", 0) for r in all_runs]
        grades = [r.get(tid, {}).get("grade", "ERROR") for r in all_runs]

        field_pass = {}
        for field in tc["fields"]:
            fid = field["id"]
            passes = sum(1 for r in all_runs if r.get(tid, {}).get("fields", {}).get(fid, False))
            field_pass[str(fid)] = {"passes": passes, "total": n, "rate": passes / n}

        baseline[tid] = {
            "scores": scores,
            "min": min(scores),
            "max": max(scores),
            "avg": sum(scores) / len(scores),
            "grades": grades,
            "field_pass_rate": field_pass,
        }

        print(f"  {tid}: scores={scores} min={min(scores)} max={max(scores)}")

    baseline["_meta"] = {
        "created": datetime.now().isoformat(),
        "runs": n,
        "config": config,
    }

    with open(BASELINE_PATH, "w", encoding="utf-8") as f:
        json.dump(baseline, f, ensure_ascii=False, indent=2)

    print(f"\n[BASELINE] 저장 완료: {BASELINE_PATH}")
    return baseline


def load_baseline():
    if not BASELINE_PATH.exists():
        return None
    with open(BASELINE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ── 실패 분석 ──

def analyze_failures(baseline, config, log):
    """안정적으로 실패하는 필드 1개 반환. 없으면 None."""
    spec = load_spec()
    exclude_tcs = set(config.get("exclude_tcs", {}).keys())
    target_tcs = set(config.get("target_tcs", []))
    exclude_fields = config.get("exclude_fields", {})
    already_tried = {(it["tc"], it["field_id"]) for it in log.get("iterations", [])}

    candidates = []
    for tc in spec["test_cases"]:
        tid = tc["id"]
        if tid in exclude_tcs or tid not in target_tcs:
            continue
        bl = baseline.get(tid)
        if not bl:
            continue

        tc_excludes = set(exclude_fields.get(tid, []))
        for field in tc["fields"]:
            fid = field["id"]
            if fid in tc_excludes:
                continue
            if (tid, fid) in already_tried:
                continue

            fpr = bl["field_pass_rate"].get(str(fid), {})
            rate = fpr.get("rate", 1.0)
            if rate < 0.67:  # 3회 중 2회 이상 실패
                candidates.append({
                    "tc": tid,
                    "tc_name": tc["name"],
                    "field_id": fid,
                    "label": field["label"],
                    "expected": field["expected"],
                    "critical": field.get("critical", False),
                    "pass_rate": rate,
                    "notes": field.get("notes", ""),
                })

    if not candidates:
        return None

    # critical 우선, pass_rate 낮은 순
    candidates.sort(key=lambda x: (not x["critical"], x["pass_rate"]))
    return candidates[0]


# ── Rule 생성 (Gemini) ──

def generate_rule(failure, config):
    """Gemini에게 Rule 1개 생성 요청."""
    from google import genai
    from google.genai import types

    # .env 로드
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None, "GEMINI_API_KEY 없음"

    # 현재 Rules 추출
    mapper_text = MAPPER_PATH.read_text(encoding="utf-8")
    rules_match = re.search(r'(1\. .*?)"""', mapper_text, re.DOTALL)
    current_rules = rules_match.group(1).strip() if rules_match else "Rules 추출 실패"

    # 마지막 Rule 번호
    rule_nums = [int(m) for m in re.findall(r'^\s*(\d+)\.', current_rules, re.MULTILINE)]
    next_num = max(rule_nums) + 1 if rule_nums else 15

    # 입력 데이터
    input_path = TEST_FORMS_DIR / "test-inputs"
    input_file = None
    spec = load_spec()
    for tc in spec["test_cases"]:
        if tc["id"] == failure["tc"]:
            input_file = TEST_FORMS_DIR / tc["input_file"]
            break
    input_data = input_file.read_text(encoding="utf-8") if input_file and input_file.exists() else ""

    prompt = f"""DocFlow AI 매핑 시스템의 SYSTEM_PROMPT에 추가할 규칙 1개를 작성해줘.

[현재 규칙]
{current_rules}

[문제]
양식: {failure['tc']} ({failure['tc_name']})
실패 필드: {failure['label']}
기대값: {failure['expected']}
실패 패턴: {failure.get('notes', '알 수 없음')}
pass rate: {failure['pass_rate']:.0%} (3회 중 {int(failure['pass_rate']*3)}회 성공)

[입력 자료 일부]
{input_data[:2000]}

[요청]
규칙 번호 {next_num}번으로, 위 실패를 방지하는 규칙 1개만 작성.
형식: "{next_num}. 규칙 내용"

조건:
- 기존 규칙과 충돌 금지
- 특정 값(이름, 금액 등) 하드코딩 금지
- 이 양식뿐 아니라 유사 양식 전체에 적용 가능한 일반 원칙
- 한국어로 작성
- 1-3줄 이내"""

    client = genai.Client(api_key=api_key)
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=config.get("model", "gemini-2.5-flash"),
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1, max_output_tokens=500),
            )
            rule_text = response.text.strip()
            # Rule 번호로 시작하는 줄만 추출
            for line in rule_text.split("\n"):
                if line.strip().startswith(f"{next_num}."):
                    return line.strip(), None
            return rule_text.split("\n")[0].strip(), None
        except Exception as e:
            print(f"[WARN] Gemini 호출 실패 (시도 {attempt+1}/3): {e}")
            if attempt < 2:
                time.sleep(10)
    return None, "Gemini 3회 시도 실패"


# ── Rule 적용/복원 ──

def apply_rule(rule_text):
    """ai_mapper.py SYSTEM_PROMPT 마지막에 Rule 추가. 성공 시 True."""
    text = MAPPER_PATH.read_text(encoding="utf-8")

    sp_start = text.find('SYSTEM_PROMPT = ')
    if sp_start < 0:
        return False
    open_q = text.find('"""', sp_start)
    if open_q < 0:
        return False
    close_q = text.find('"""', open_q + 3)
    if close_q < 0:
        return False

    # Rule 텍스트에서 triple quote 제거 (Python 구문 깨짐 방지)
    safe_rule = rule_text.replace('"""', '').replace("'''", "")

    # 닫는 """ 직전에 Rule 삽입 (개행 + Rule + 개행)
    new_text = text[:close_q] + "\n" + safe_rule + "\n" + text[close_q:]
    MAPPER_PATH.write_text(new_text, encoding="utf-8")

    # 구문 검증: import 가능한지 확인
    try:
        compile(new_text, "ai_mapper.py", "exec")
    except SyntaxError as e:
        print(f"[FAIL] Rule 삽입 후 구문 오류: {e}")
        revert_rule()
        return False
    return True


def revert_rule():
    """ai_mapper.py를 마지막 커밋 상태로 원복."""
    subprocess.run(
        ["git", "checkout", "--", "ai_mapper.py"],
        cwd=PROJECT_ROOT, capture_output=True,
    )


def commit_rule(rule_text):
    """수정된 ai_mapper.py를 커밋."""
    subprocess.run(["git", "add", "ai_mapper.py"], cwd=PROJECT_ROOT, capture_output=True)
    msg = f"[auto] {rule_text[:80]}"
    subprocess.run(["git", "commit", "-m", msg], cwd=PROJECT_ROOT, capture_output=True)


# ── 회귀 검증 ──

def verify_no_regression(baseline, spec, config):
    """N회 실행 후 모든 TC min >= baseline min 확인."""
    n = config["verify_runs"]
    print(f"\n[VERIFY] {n}회 검증 실행")

    all_runs = []
    for i in range(n):
        print(f"  Verify Run {i+1}/{n}")
        results, _ = run_all_tcs(spec)
        all_runs.append(results)

    verify = {}
    regression = False
    for tc in spec["test_cases"]:
        tid = tc["id"]
        bl_min = baseline.get(tid, {}).get("min", 0)
        scores = [r.get(tid, {}).get("score", 0) for r in all_runs]
        v_min = min(scores) if scores else 0

        passed = v_min >= bl_min
        if not passed:
            regression = True

        verify[tid] = {
            "baseline_min": bl_min,
            "verify_scores": scores,
            "verify_min": v_min,
            "passed": passed,
        }
        status = "OK" if passed else "REGRESSION"
        print(f"    {tid}: baseline_min={bl_min} verify={scores} min={v_min} [{status}]")

    return verify, not regression


# ── 메인 루프 ──

def run_iteration(baseline, spec, config, log):
    """1회 iteration: 분석 → 생성 → 적용 → 검증 → commit/revert."""
    iteration = {
        "timestamp": datetime.now().isoformat(),
        "tc": None, "field_id": None, "rule": None,
        "result": None, "details": {},
    }

    # 1. 실패 분석
    failure = analyze_failures(baseline, config, log)
    if not failure:
        print("[SKIP] 개선 가능한 안정 실패 필드 없음")
        iteration["result"] = "no_target"
        return iteration

    print(f"\n[TARGET] {failure['tc']} field {failure['field_id']}: {failure['label']}")
    print(f"  기대: {failure['expected']}, pass_rate: {failure['pass_rate']:.0%}")
    iteration["tc"] = failure["tc"]
    iteration["field_id"] = failure["field_id"]
    iteration["details"]["failure"] = failure

    # 2. Rule 생성
    rule_text, err = generate_rule(failure, config)
    if not rule_text:
        print(f"[FAIL] Rule 생성 실패: {err}")
        iteration["result"] = "gen_failed"
        return iteration

    print(f"[RULE] {rule_text}")
    iteration["rule"] = rule_text

    # 3. 적용
    if not apply_rule(rule_text):
        print("[FAIL] Rule 적용 실패 (SYSTEM_PROMPT 패턴 미매칭)")
        iteration["result"] = "apply_failed"
        return iteration

    # 4. 검증
    verify, no_regression = verify_no_regression(baseline, spec, config)
    iteration["details"]["verify"] = verify

    if no_regression:
        commit_rule(rule_text)
        print(f"[OK] COMMIT: {rule_text[:60]}")
        iteration["result"] = "committed"
        log["rules_added"] = log.get("rules_added", 0) + 1
    else:
        revert_rule()
        print("[REVERT] 회귀 감지 -> 원복")
        iteration["result"] = "reverted"

    return iteration


def main():
    parser = argparse.ArgumentParser(description="DocFlow 반자동 개선 시스템")
    parser.add_argument("--baseline", action="store_true", help="기준선 확립 (3회 실행)")
    parser.add_argument("--once", action="store_true", help="1회 iteration만")
    args = parser.parse_args()

    config = load_config()
    spec = load_spec()

    # 무결성 체크
    problems = check_integrity(spec)
    critical = [p for p in problems if "CRITICAL" in p]
    if critical:
        print(f"[STOP] {len(critical)}개 CRITICAL 문제")
        for p in critical:
            print(f"  {p}")
        return 1

    # 기준선 모드
    if args.baseline:
        build_baseline(spec, config)
        return 0

    # 기준선 로드
    baseline = load_baseline()
    if not baseline:
        print("[INFO] 기준선 없음 -> 자동 생성")
        baseline = build_baseline(spec, config)

    log = load_log()

    if args.once:
        iteration = run_iteration(baseline, spec, config, log)
        log["iterations"].append(iteration)
        save_log(log)
        print(f"\n[DONE] 결과: {iteration['result']}")
        return 0

    # 전체 루프
    max_iter = config.get("max_iterations", 16)
    max_rules = config.get("max_new_rules", 4)
    interval = config.get("interval_hours", 6) * 3600

    for i in range(max_iter):
        print(f"\n{'='*60}")
        print(f"[AUTO] Iteration {i+1}/{max_iter} (추가된 Rule: {log.get('rules_added', 0)}/{max_rules})")
        print(f"{'='*60}")

        if log.get("rules_added", 0) >= max_rules:
            print(f"[STOP] max_new_rules={max_rules} 도달")
            break

        try:
            iteration = run_iteration(baseline, spec, config, log)
        except Exception as e:
            print(f"\n[ERROR] Iteration 예외: {e}")
            iteration = {
                "timestamp": datetime.now().isoformat(),
                "tc": None, "field_id": None, "rule": None,
                "result": "exception", "details": {"error": str(e)},
            }
            # 안전 복원 (Rule이 적용된 상태일 수 있으므로)
            revert_rule()

        log["iterations"].append(iteration)
        save_log(log)

        result = iteration["result"]
        print(f"\n[ITERATION {i+1}] 결과: {result}")

        if result == "no_target":
            print("[STOP] 더 이상 개선 대상 없음")
            break

        if i < max_iter - 1:
            next_time = datetime.now().timestamp() + interval
            next_str = datetime.fromtimestamp(next_time).strftime("%Y-%m-%d %H:%M")
            print(f"\n[SLEEP] 다음 실행: {next_str} ({config['interval_hours']}시간 후)")
            time.sleep(interval)

    print(f"\n[COMPLETE] 총 {len(log['iterations'])}회 iteration, {log.get('rules_added', 0)}개 Rule 추가")
    return 0


if __name__ == "__main__":
    sys.exit(main())
