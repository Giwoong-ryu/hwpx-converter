"""변환 메트릭 수집 — 성공/실패 기록 + 통계"""

import json
import os
import time
from datetime import datetime
from threading import Lock

_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "conversion_log.jsonl")
_lock = Lock()


def log(operation: str, *, success: bool, input_format: str = "", output_format: str = "",
        field_count: int = 0, duration_ms: int = 0, error: str = "", detail: str = ""):
    """변환 결과 1건 기록"""
    entry = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "op": operation,
        "ok": success,
        "in_fmt": input_format,
        "out_fmt": output_format,
        "fields": field_count,
        "ms": duration_ms,
        "err": error[:200] if error else "",
        "detail": detail[:100] if detail else "",
    }
    with _lock:
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def get_stats() -> dict:
    """누적 통계 계산"""
    if not os.path.exists(_LOG_PATH):
        return {"total": 0, "message": "아직 기록이 없습니다"}

    ops = {}
    total, ok, fail = 0, 0, 0

    with open(_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue

            total += 1
            op = e.get("op", "unknown")
            success = e.get("ok", False)

            if op not in ops:
                ops[op] = {"total": 0, "ok": 0, "fail": 0, "avg_ms": 0, "total_ms": 0,
                           "errors": {}, "coverages": []}

            ops[op]["total"] += 1
            if success:
                ops[op]["ok"] += 1
                ok += 1
            else:
                ops[op]["fail"] += 1
                fail += 1
                err = e.get("err", "unknown")
                if err:
                    ops[op]["errors"][err] = ops[op]["errors"].get(err, 0) + 1

            ops[op]["total_ms"] += e.get("ms", 0)
            ops[op]["avg_ms"] = ops[op]["total_ms"] // max(ops[op]["total"], 1)

            # coverage 파싱 (detail에서 추출)
            detail = e.get("detail", "")
            if "coverage=" in detail:
                try:
                    cov = float(detail.split("coverage=")[1].split("%")[0])
                    ops[op]["coverages"].append(cov)
                except (ValueError, IndexError):
                    pass

    # 최종 정리
    for op_data in ops.values():
        del op_data["total_ms"]
        # 에러 빈도 상위 3개만
        if op_data["errors"]:
            sorted_errs = sorted(op_data["errors"].items(), key=lambda x: -x[1])[:3]
            op_data["errors"] = dict(sorted_errs)
        # coverage 평균
        covs = op_data.pop("coverages")
        if covs:
            op_data["avg_coverage"] = f"{sum(covs) / len(covs):.1f}%"
            op_data["min_coverage"] = f"{min(covs):.1f}%"
            op_data["coverage_count"] = len(covs)

    return {
        "total": total,
        "success": ok,
        "fail": fail,
        "success_rate": f"{ok / total * 100:.1f}%" if total > 0 else "N/A",
        "by_operation": ops,
    }


class Timer:
    """with Timer() as t: ... t.ms"""
    def __init__(self):
        self.ms = 0
    def __enter__(self):
        self._start = time.perf_counter()
        return self
    def __exit__(self, *args):
        self.ms = int((time.perf_counter() - self._start) * 1000)
