"""Eazy HWPX 전체 기능 테스트"""
import requests, zipfile, re, os, sys

BASE = "http://localhost:8000"
RESULTS = []
OUTPUT_FILES = []


def test(name, fn):
    try:
        result = fn()
        RESULTS.append((name, "OK", result))
        print(f"[OK] {name}: {result}")
    except Exception as e:
        RESULTS.append((name, "FAIL", str(e)[:150]))
        print(f"[FAIL] {name}: {str(e)[:150]}")


def check_hwpx(path, label):
    issues = []
    try:
        with zipfile.ZipFile(path, "r") as zf:
            bad = zf.testzip()
            if bad:
                issues.append(f"ZIP 손상: {bad}")
            if zf.namelist()[0] != "mimetype":
                issues.append(f"mimetype 순서: {zf.namelist()[0]}")
            for name in zf.namelist():
                if "section" in name and name.endswith(".xml"):
                    data = zf.read(name).decode("utf-8")
                    cnt = data.count("linesegarray")
                    if cnt > 0:
                        issues.append(f"{name}: linesegarray {cnt}")
    except Exception as e:
        issues.append(f"열기 실패: {e}")
    ok = len(issues) == 0
    print(f"  [{'OK' if ok else 'FAIL'}] {label}" + (f": {issues}" if issues else ""))
    return ok


# 0. 서버
def t0():
    r = requests.get(f"{BASE}/api/health")
    assert r.json()["status"] == "ok"
    try:
        rn = requests.get("https://quintin-noncommittal-nondetractively.ngrok-free.dev/api/health", timeout=5)
        ng = "OK" if rn.status_code == 200 else str(rn.status_code)
    except:
        ng = "FAIL"
    return f"local OK, ngrok {ng}"

test("0. 서버 상태", t0)

# 1. HWP 분석
def t1():
    with open("test/test_form.hwp", "rb") as f:
        r = requests.post(f"{BASE}/api/form/analyze", files={"file": ("t.hwp", f)})
    assert r.status_code == 200, f"HTTP {r.status_code}"
    return f"{r.json()['field_count']}개 필드"

test("1. HWP 분석 (COM 변환)", t1)

# 2. HWPX 분석
def t2():
    with open("test/test_form.hwpx", "rb") as f:
        r = requests.post(f"{BASE}/api/form/analyze", files={"file": ("t.hwpx", f)})
    assert r.status_code == 200
    return f"{r.json()['field_count']}개 필드"

test("2. HWPX 분석", t2)

# 3. 문서 생성
def t3():
    with open("test/test_form.hwpx", "rb") as f:
        r = requests.post(f"{BASE}/api/form/analyze", files={"file": ("t.hwpx", f)})
    d = r.json()
    repl = {d["fields"][0]: "Eazy_테스트", d["fields"][5]: "검증완료"}
    r = requests.post(f"{BASE}/api/form/generate", json={"file_id": d["file_id"], "replacements": repl})
    assert r.status_code == 200
    out = "test/final_generate.hwpx"
    with open(out, "wb") as f:
        f.write(r.content)
    OUTPUT_FILES.append((out, "문서생성"))
    return f"{len(r.content):,}bytes"

test("3. 문서 생성 (치환)", t3)

# 4. 이미지 제거
def t4():
    with open("test/test_form.hwp", "rb") as f:
        r = requests.post(f"{BASE}/api/form/analyze", files={"file": ("t.hwp", f)})
    d = r.json()
    repl = {d["fields"][0]: "이미지제거"}
    r = requests.post(f"{BASE}/api/form/generate", json={"file_id": d["file_id"], "replacements": repl, "strip_images": True})
    assert r.status_code == 200
    out = "test/final_strip.hwpx"
    with open(out, "wb") as f:
        f.write(r.content)
    OUTPUT_FILES.append((out, "이미지제거"))
    with zipfile.ZipFile(out) as zf:
        bins = [n for n in zf.namelist() if n.startswith("BinData/")]
    return f"{len(r.content):,}bytes, BinData {len(bins)}개"

test("4. 이미지 제거", t4)

# 5. 문서→엑셀
def t5():
    with open("test/test_form.hwpx", "rb") as f:
        r = requests.post(f"{BASE}/api/extract/", files={"files": ("t.hwpx", f)})
    assert r.status_code == 200
    out = "test/final_extract.xlsx"
    with open(out, "wb") as f:
        f.write(r.content)
    return f"{len(r.content):,}bytes"

test("5. 문서→엑셀", t5)

# 6. 엑셀 분석
def t6():
    with open("test/test_data.xlsx", "rb") as f:
        r = requests.post(f"{BASE}/api/excel/analyze", files={"file": ("d.xlsx", f)})
    assert r.status_code == 200
    return f"fields={r.json().get('field_count', '?')}"

test("6. 엑셀 분석", t6)

# 7. 엑셀 채우기
def t7():
    with open("test/test_data.xlsx", "rb") as f:
        r = requests.post(f"{BASE}/api/excel/analyze", files={"file": ("d.xlsx", f)})
    d = r.json()
    repl = {}
    for i, field in enumerate(d.get("fields", [])[:3]):
        repl[field] = f"FILL_{i}"
    r = requests.post(f"{BASE}/api/excel/fill", json={"file_id": d["file_id"], "replacements": repl})
    assert r.status_code == 200
    out = "test/final_excel_fill.xlsx"
    with open(out, "wb") as f:
        f.write(r.content)
    return f"{len(r.content):,}bytes"

test("7. 엑셀 채우기", t7)

# 8. 합치기
def t8():
    f1 = open("test/test_form.hwpx", "rb")
    f2 = open("test/test_form.hwpx", "rb")
    r = requests.post(f"{BASE}/api/merge/", files=[("files", ("a.hwpx", f1)), ("files", ("b.hwpx", f2))])
    f1.close(); f2.close()
    assert r.status_code == 200
    out = "test/final_merge.hwpx"
    with open(out, "wb") as f:
        f.write(r.content)
    OUTPUT_FILES.append((out, "합치기"))
    return f"{len(r.content):,}bytes"

test("8. 문서 합치기", t8)

# 9. 정기문서
def t9():
    with open("test/test_form.hwpx", "rb") as f:
        r = requests.post(f"{BASE}/api/form/analyze", files={"file": ("t.hwpx", f)})
    fid = r.json()["file_id"]
    r = requests.post(f"{BASE}/api/periodic/generate", json={
        "file_id": fid, "date_text": "2026", "start": "2026-04-01", "end": "2026-06-01", "interval": "monthly"
    })
    assert r.status_code == 200
    out = "test/final_periodic.zip"
    with open(out, "wb") as f:
        f.write(r.content)
    with zipfile.ZipFile(out) as zf:
        for hf in zf.namelist():
            if hf.endswith(".hwpx"):
                tmp = f"test/periodic_{hf}"
                with open(tmp, "wb") as tf:
                    tf.write(zf.read(hf))
                OUTPUT_FILES.append((tmp, f"정기_{hf}"))
    return f"{len([n for n in zf.namelist() if n.endswith('.hwpx')])}개 문서"

test("9. 정기문서", t9)

# 10. 배치
def t10():
    with open("test/test_form.hwpx", "rb") as f:
        r = requests.post(f"{BASE}/api/form/analyze", files={"file": ("t.hwpx", f)})
    fid = r.json()["file_id"]
    with open("test/test_data.xlsx", "rb") as ef:
        r = requests.post(f"{BASE}/api/batch/generate", data={"file_id": fid}, files={"excel": ("d.xlsx", ef)})
    assert r.status_code == 200
    out = "test/final_batch.zip"
    with open(out, "wb") as f:
        f.write(r.content)
    with zipfile.ZipFile(out) as zf:
        cnt = len([n for n in zf.namelist() if n.endswith(".hwpx")])
    return f"{cnt}개 문서"

test("10. 엑셀→문서 배치", t10)

# 11. 프론트엔드
def t11():
    r = requests.get(f"{BASE}/")
    assert r.status_code == 200
    assert "Eazy HWPX" in r.text, "타이틀 없음"
    return f"HTML {len(r.text):,}bytes"

test("11. 프론트엔드", t11)

# HWPX 무결성 검증
print(f"\n--- HWPX 무결성 검증 ({len(OUTPUT_FILES)}개) ---")
verify_ok = sum(1 for p, l in OUTPUT_FILES if os.path.exists(p) and check_hwpx(p, l))

# 최종
ok = sum(1 for _, s, _ in RESULTS if s == "OK")
fail = sum(1 for _, s, _ in RESULTS if s == "FAIL")
print(f"\n{'='*50}")
print(f"API 테스트: {ok}/{len(RESULTS)} 통과, {fail} 실패")
print(f"무결성 검증: {verify_ok}/{len(OUTPUT_FILES)} 통과")
print(f"{'='*50}")
