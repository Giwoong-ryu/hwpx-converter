# DocFlow HWPX 테스트 방법론

> 적용 범위: **hwpx-converter 프로젝트 전용**
> 트리거: 이 프로젝트에서 "테스트", "QA", "검증", "회귀 체크", "test_spec", "run_tests" 감지 시 로드
> 관련 파일: `test-forms/test_spec.json`, `test-forms/run_tests.py`, `test-forms/results/`

---

## 배경

DocFlow는 사용자가 업로드한 HWP/HWPX 양식의 빈칸을 AI로 채우는 시스템이다. 품질 검증은 다음 3가지 경로가 모두 맞아야 한다:

1. **AI 매핑 정확도** — Gemini가 양식 헤더를 보고 자료를 올바른 필드에 배치
2. **슬롯 주입 정확도** — `clone_form.py`의 `inject_values_by_slot`이 빈 셀을 정확히 채움
3. **텍스트 치환 정확도** — `clone_form.py`의 `clone`이 기존 텍스트를 덮어씀

이 3개는 독립적으로 고장 날 수 있다. 어느 한 단계만 테스트하면 나머지에서 터지는 걸 못 잡는다. 따라서 **반드시 end-to-end**(AI → slot 주입 → clone → 최종 hwpx)로 테스트해야 한다.

---

## 실전에서 반복 경험한 실패 패턴

### 1. 기대값이 입력 txt에 없는데 AI 탓
자기소개서 기대값 "현장 실무 역량"이 입력 txt에 "현장 실무 경험"으로 있어서 substring 매칭 실패 → AI가 정확히 한 건데 틀렸다고 오판. **cross-check 없이는 테스트 자체가 거짓말**.

### 2. `map_content`만 호출하고 `clone`은 생략
AI 응답에 `상호__1: 인테리어 하우스`가 있으면 "됐다"고 판정했는데, 실제로는 `clone_form.clone()`이 "상호" 텍스트를 "인테리어 하우스"로 바꾸면서 **라벨이 사라지는** 문제 있음. 중간 API만 테스트하면 이런 거 못 잡음.

### 3. 한글 2022에서 열었을 때만 보이는 렌더링 오류
- 셀 높이 부족으로 본문이 페이지 배경에 깔림
- 폰트 크기 제약으로 긴 값이 잘림
- `<hp:linesegarray>` 캐시 불일치로 텍스트 표시 안 됨
**XML이 정상이어도 한글에서 열면 깨질 수 있다.** 텍스트 매칭만으론 못 잡음.

### 4. slot_map이 비어있는 양식
견적서처럼 [H] 헤더가 거의 없는 양식은 `build_header_slot_map`이 빈 결과 반환 → 전체가 `normal_repl` 경로로 흘러 `clone` 함수 텍스트 치환만 수행. AI 응답 형태가 이 경로에 맞아야 함.

### 5. Critical 오류가 점수로 가려짐
TC-01 세금계산서에서 "공급자↔공급받는자" 뒤바뀜은 법적 무효 수준인데, 10개 중 9개 정답(90%)으로 A등급 나올 수 있음. 치명 필드 별도 처리 필수.

### 6. AI 응답 변동성
같은 입력으로 run_tests.py 2회 실행 시: 첫 실행 40개 키, 두 번째 8개 키 (편차 큼). **1회 실행으로 판정 금지.**

### 7. 테스트 스펙의 label과 AI 응답 키 불일치
스펙에 "고객명", "업체명"이라 썼는데 양식 실제 헤더는 "귀하", "상호". AI는 양식 헤더를 키로 쓰므로 스펙 기준 매칭은 전부 실패.
→ **채점은 최종 hwpx 본문 기준 substring**으로 해야 함 (run_tests.py가 이 방식 채택).

### 8. 양식 구조 한계를 AI 탓으로 오인
일부 TC는 아무리 AI를 개선해도 D를 벗어날 수 없는 구조적 한계가 있다.

| TC | 양식 | 한계 유형 | 증상 |
|----|------|----------|------|
| TC-01 | 세금계산서 | 병합 셀 2중 구조 | 슬롯 주입 도달 불가, 값 삽입 경로 없음 |
| TC-03 | 정부공문 | HWP→HWPX COM 의존 | COM 없는 환경에서 ERROR |
| TC-05 | 근로계약서 | 단락 빈칸 (표 아님) | `build_header_slot_map` 동작 안 함 |
| TC-06 | 납품확인서 | 검수확인서 구조 | 필드 자체가 양식에 없음 |

→ **이 TC는 D가 정상**. 코드 버그 아님. `test_spec.json`의 해당 필드에 `critical: false`.

### 9. TC 간 COM 서버 충돌 (병렬 실행 금지)
전체 7TC 실행 중 개별 TC를 병렬로 돌리면 HWP→HWPX COM 변환이 동시에 실행되어 충돌한다.

```
[증상] TC-03 ERROR: "HWP→HWPX 변환 실패 (COM 필요)"
[원인] 두 Python 프로세스가 동시에 win32com을 열어 서버 충돌
[해결] run_tests.py TC 간 2초 sleep + 동시 실행 금지
```

`run_tests.py`는 이미 TC 사이에 `time.sleep(2)` 적용되어 있음.

### 10. test_spec.json에 양식에 없는 필드를 critical:true로 지정
양식 자체에 없는 필드를 critical:true로 놓으면 코드가 완벽해도 자동 D 강등.

**검증 절차**: critical=true 필드마다 "이 텍스트가 양식 XML에 존재하는가?" 실측 확인.

```bash
python -c "
from processors.invoice_processor import InvoiceProcessor
from clone_form import extract_structured_fields
s = extract_structured_fields('test-forms/{양식}.hwpx')
# 모든 셀 텍스트 출력 후 기대값 검색
for t in s['tables']:
    for row in t['rows']:
        for cell in row:
            if cell['text'].strip():
                print(repr(cell['text'].strip()))
" | grep -i "찾는 텍스트"
```

### 11. invoice_style 라벨 손상 (P1 — Step 1+2 완료, Step 3 보류)
invoice_style 양식에서 InvoiceProcessor가 일부 라벨을 slot_map에 포함하지 못하면, AI 반환 키가 normal_repl 경로로 흘러 라벨 셀을 값으로 교체한다.

```
재현 경로:
  AI 반환: "합계금액__1": "3,536,500"
  slot_map 누락 → normal_repl["합계금액__1"] = "3,536,500"
  clone_form: "합계금액" 라벨 셀 → "3,536,500"으로 교체 (라벨 사라짐)
```

**현재 상태 (2026-04-13)**:
- Step 1 완료 (e4f6b21): _is_total_label() + Phase 1+2 2단계 스캔 — 비표준 합계 라벨 slot_map 포함
- Step 2 완료: TC-02 slot injection 경로 정상 확인
- Step 3 보류: form.py normal_repl INVOICE_LABELS 차단 — InvoiceProcessor가 모든 케이스 커버 후 적용

### 12. AI 섹션 접두사 할루시네이션 (2026-04-13 발견, 해결됨)
두 벌 양식(공급받는자용/공급자용)에서 AI가 섹션 이름을 키 접두사로 붙이는 버그.

```
증상: AI 반환 키 = '공급받는자용_귀하', '공급자용_품 목'
원인: AI가 양식의 두 사본(공급받는자용/공급자용)을 구분하려다 섹션 접두사 생성
결과: slot_map_norm에서 키 매칭 실패 → 전체 slot injection 실패
영향: TC-02가 7-8/10에서 5/10으로 급락
```

**Fix**: SYSTEM_PROMPT Rule 12 — 섹션 접두사 절대 금지. `라벨명__N` 형식만 허용.
`commit 55f4fef`

### 13. AI 라벨 의미론적 재명명 (2026-04-13 발견, 해결됨)
AI가 [H] 라벨의 의미를 해석해서 존재하지 않는 새 키를 생성하는 버그.

```
증상 1: [H]합  계 → AI 키 = '총 견적 금액', '공급가액합계'
  원인: AI가 합계 셀의 의미를 파악하고 더 "정확한" 이름으로 재명명
  결과: slot_map에 '총 견적 금액' 없음 → normal_repl → 양식에 없는 라벨 치환 실패

증상 2: [H]귀하 앞 빈 셀 → AI가 귀하__N 키를 생성하지 않음
  원인: AI가 귀하를 fillable 필드가 아닌 존칭어/데코레이터로 인식
  결과: 수신인 이름(홍길동) 미주입
```

**Fix**: SYSTEM_PROMPT Rule 13 — [H] 라벨 텍스트 그대로 키 사용. 귀하 슬롯 수신인 명시.
`commit b1625ac`

### 14. 합  계 셀에 소계/총계 혼용 (2026-04-13 발견, 해결됨)
양식에 합  계 셀이 1개인데, 입력 데이터에 공급가액합계(소계)와 총견적금액(VAT포함)이 둘 다 있으면 AI가 임의로 선택한다.

```
증상: 합  계 셀에 실행마다 3,215,000(소계) 또는 3,536,500(총액) 혼재
영향: critical 필드(총 견적 금액)가 AI 실행마다 PASS/FAIL 뒤바뀜
```

**Fix**: USER_PROMPT rule 6 — "합  계/합계 셀에는 VAT 포함 최종 총액을 넣으세요."
`commit b1625ac`

**구조적 한계**: 슬롯이 1개이므로 field 9(공급가액합계)는 항상 실패. 8/10 B가 최대치.

---

## Pre-Flight 체크리스트 (테스트 시작 전 필수)

### 1. Cross-check: 기대값 ↔ 입력 txt 대조

- `test-forms/test-inputs/{케이스}.txt` 전부 Read
- `test_spec.json` 각 field의 `expected`가 txt에 substring으로 존재하는지 대조
- 부분 매치는 `notes` 필드에 "substring" 명시
- 포맷 차이는 기대값을 txt 원문 포맷으로 수정 (TC-05#8 근무요일 교훈)

**결과 기록**: `test_spec.json._meta.cross_check_status = "all_N_verified"`

### 2. 양식 실측 (스펙 label 정하기 전)

```bash
python -c "
from clone_form import extract_structured_fields
s = extract_structured_fields('test-forms/{양식}.hwpx')
for ti, t in enumerate(s['tables']):
    for ri, row in enumerate(t['rows']):
        for ci, cell in enumerate(row):
            if cell['text'].strip():
                flag = '[H]' if (cell['bold'] or cell['bg']) else '   '
                print(f'r{ri}c{ci} {flag} \"{cell[\"text\"][:40]}\"')
"
```

확인 사항:
- [H] 헤더 셀 목록 (AI가 키로 인식할 라벨)
- `build_header_slot_map` 결과의 헤더/슬롯 짝
- "X :" 콜론 라벨 (append 슬롯 대상)
- 본문 전용 큰 셀 (max_chars 제약 대상)

**이 결과를 바탕으로 test_spec.json의 field label 결정.**

### 3. Critical 필드 플래그

각 TC에서 다음은 `critical: true` 필수:

| 양식 | 치명 필드 |
|------|----------|
| 세금계산서 | 공급자/공급받는자 사업자번호/상호, 합계 공급가액, 세액 |
| 견적서 | 공급가액 합계, 총 견적 금액 |
| 정부공문 | 결재선 3필드 (기안/검토/결재) |
| 사업제안서 | 제안사 회사명, 사업자등록번호, 제안 금액, 회사명 반복 일관성 |
| 근로계약서 | 갑/을 구분 필드 전부, 계약 시작/종료일, 기본급/총급여 |
| 납품확인서 | 납품처/공급자 식별, 합계 금액, 청구 총액 |
| 상담일지 | 학생/교사/학부모 구분 (인물 혼동 금지) |

Critical 규칙: **하나라도 틀리면 등급 자동 D로 강등** (`run_tests.py`의 `score_tc` 구현).

### 4. 무결성 체크 (`--dry-run`)

```bash
python test-forms/run_tests.py --dry-run
```

확인되는 것:
- `clone_form`, `ai_mapper` import 가능
- `GEMINI_API_KEY` 환경변수 또는 `.env` 존재
- 7개 양식 파일 전부 존재
- 7개 입력 txt 파일 전부 존재
- HWPX 파싱이 에러 없이 되고 테이블 개수 ≥ 1

실패 항목 있으면 **테스트 시작 금지**.

### 5. End-to-End 재현 (run_tests.py의 파이프라인)

`run_tests.py`의 `run_ai_mapping` 함수는 `api/routes/form.py`의 `generate` 엔드포인트를 그대로 재현:
1. HWP → HWPX 변환 (`file_manager.convert_hwp`)
2. `extract_structured_fields` (label_counts 포함)
3. `build_header_slot_map`
4. `map_content` (AI 호출)
5. `KrFormatter.auto_detect_and_format` (포맷터)
6. `__N` 접미사 기반 slot_assignments / normal_repl 분리
7. `inject_values_by_slot` (mode=append 지원)
8. `clone` (텍스트 치환)
9. 최종 hwpx 파일 생성

**채점은 최종 hwpx 본문에서 `extract_hwpx_text`로 텍스트 뽑아서 기대값 substring 검색**. AI 응답 키 기준 아님.

### 6. 부분 매칭 규칙

- 공백 정규화 (`re.sub(r'\s+', ' ', ...)`)
- 소문자화 (영문만)
- 양방향 substring: `expected in actual` 또는 `actual in expected` 중 하나라도 true면 정답

**예외 — 완전 일치 강제**:
- 사업자등록번호 (XXX-XX-XXXXX 포맷)
- 합계 금액 (자릿수 하나만 틀려도 회계 오류)
- 계약 시작/종료일 (하루 차이로 법적 효력 다름)

이 예외들은 `test_spec.json`에서 `match_mode: exact`로 명시.

### 7. 한국어 포맷 tolerance

시스템에 `kr_formatter.py`가 있어 자동 변환:
- 사업자번호: `1234567890` → `123-45-67890`
- 금액: `1500000` → `1,500,000`
- 날짜: `20260412` → `2026년 4월 12일`
- 전화: `01012345678` → `010-1234-5678`

**기대값은 입력 txt 원문 포맷 그대로** 쓰기. 시스템이 자동 변환한 결과가 최종 파일에 들어가므로, substring 매칭이 양쪽 포맷 중 하나라도 매치되면 OK.

### 8. 시험 운전 먼저 (1개 TC)

전체 7개 돌리기 전에 **가장 단순한 TC 1개** 먼저:

```bash
python test-forms/run_tests.py --tc TC-02
```

**우선순위**:
1. **TC-02 견적서** — 슬롯 맵 거의 빈 상태 → 텍스트 치환 경로 검증
2. **TC-01 세금계산서** — 공급자/공급받는자 혼동 리스크
3. **TC-05 근로계약서** — 갑/을 혼동 리스크

시험운전에서 스펙 버그 발견되면 본 테스트 전에 수정.

### 9. 반복 실행 (2회 이상)

AI 응답 변동성이 크므로 본 테스트는 **최소 2회**:

```bash
python test-forms/run_tests.py       # 1차
python test-forms/run_tests.py       # 2차 (다른 run_id 생성)
```

편차가 크면 `results/{run_id1}/summary.json`과 `results/{run_id2}/summary.json` 비교.
두 번 다 PASS여야 진짜 통과.

### 10. 한글 2022에서 실제 렌더링 확인

run_tests.py가 텍스트 매칭 통과해도, 한글에서 열어보면 렌더링 문제 있을 수 있음.

**확인 필수**:
- 셀 넘침 (본문이 페이지 배경에 깔림)
- 글꼴/크기 깨짐
- 셀 정렬 어긋남
- 빈 페이지 생성
- 표 구조 붕괴

결과 hwpx는 `test-forms/results/{run_id}/TC-XX/output.hwpx`에 저장되므로 사용자가 직접 열어봐야 함. **AI가 이걸 자동으로 확인할 방법 없음**.

---

## 체크리스트 요약

- [ ] 1. 기대값 ↔ 입력 txt cross-check
- [ ] 2. 양식 실측 (헤더 목록 + slot_map 확인)
- [ ] 3. Critical 필드 플래그 (위 표 참조)
- [ ] 4. `--dry-run`으로 무결성 체크
- [ ] 5. End-to-end 파이프라인 재현 (`run_tests.py`)
- [ ] 6. 부분 매칭 + 예외 완전일치 필드 명시
- [ ] 7. 한국어 포맷 tolerance 이해
- [ ] 8. 시험운전 1개 TC 먼저
- [ ] 9. 본 테스트 2회 이상
- [ ] 10. 한글에서 실제 렌더링 확인 (사용자 수작업)

---

## 메타데이터 수집 (자동)

`run_tests.py`가 각 실행마다 `results/{run_id}/metadata.json`에 저장:

```json
{
  "timestamp": "2026-04-12T01:21:21",
  "git_commit": "e7b9ff0...",
  "git_branch": "main",
  "git_dirty": false,
  "git_dirty_files": [],
  "ai_model": "gemini-2.5-flash",
  "python_version": "3.11.x",
  "project_root": "c:/Users/user/Desktop/gpt/hwpx-converter"
}
```

**용도**: 회귀 발견 시 `git bisect`로 원인 커밋 추적 가능.

---

## 결과 저장 구조

```
test-forms/results/YYYYMMDD_HHMMSS/
├── metadata.json              # 위 메타
├── summary.json               # 전체 TC 종합 결과
├── TC-01/
│   ├── mapping_result.json    # AI 원본 응답
│   ├── output.hwpx            # 최종 파일 (한글에서 열어볼 것)
│   ├── output_text.txt        # 최종 파일 plain text (채점 기준)
│   └── score.json             # 필드별 정답/오답 + 등급
├── TC-02/
│   └── ...
└── TC-07/
    └── ...
```

**보관 정책**: `.gitignore`에 `test-forms/results/` 추가. 로컬 영구 보관, 저장소엔 스펙과 스크립트만.

---

## 업데이트 규칙

- 새 양식 추가 시: `test_spec.json`에 TC 추가 + Cross-check 수행 + critical 플래그 지정
- 새 실패 패턴 발견 시: 이 문서의 "실전에서 반복 경험한 실패 패턴" 섹션에 케이스 추가
- `clone_form.py`/`ai_mapper.py` 주요 변경 시: 관련 TC 재실행 + 회귀 확인
- 이 방법론은 **hwpx-converter 프로젝트 내에서만 적용**. 다른 프로젝트는 자체 testing doc 별도 작성.
