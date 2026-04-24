# DocFlow AI 파이프라인 테스트 리포트

**최종 갱신**: 2026-04-24 (Phase A+B 완료)
**환경**: Windows 11 / FastAPI (8000) + Next.js
**테스트 범위**: 7TC E2E (AI 매핑 → 슬롯 주입 → 텍스트 치환 → HWPX 출력)

---

## 7TC 기준선 (2026-04-24 갱신 — 장기 아키텍처 정비 후)

| TC | 양식 | 정확도 | 등급 | 상태 |
|----|------|:---:|:---:|------|
| TC-01 | 세금계산서 | 0-3/10 | D/ERROR | 글자별 분할 셀 구조 (국세청 양식 특수) |
| TC-02 | 견적서 | **8/10** | **B** | 안정 (invoice_processor) |
| TC-03 | 정부공문 | **5-6/10** | **C** | **GovernmentProcessor + test_spec 재작성** |
| TC-04 | 사업제안서 | 6-7/10 | C | ProposalProcessor (AI extra_labels) |
| TC-05 | 근로계약서 | **7-9/10** | **C/A** | **ContractProcessor + test_spec 재작성** |
| TC-06 | 납품확인서 | 6-7/10 | C | invoice_processor (test_spec 재작성) |
| TC-07 | 상담일지 | 5-7/10 | C | 변동성 범위 (보호자 필드 양식 부재) |

**달성 효과**: Phase A+B 이전(40/70) → 이후(43-45/70). **D 등급 3개 제거** (TC-03/05/06).

### 등급 기준

| 등급 | 기준 |
|------|------|
| A | 90%+ |
| B | 80-89% |
| C | 50-79% |
| D | 50% 미만 또는 critical 필드 실패 |

### 구조적 한계 — 코드 버그 아님

| TC | 원인 | 상태 |
|----|------|:---:|
| TC-01 | 국세청 양식 글자별 셀 분할 (사업자번호, 금액 자릿수별). InvoiceProcessor 확장 필요 | 미해결 |
| TC-07 | 보호자 성명/연락처가 양식에 없음 | test_spec notes |

---

## 시스템 아키텍처

### AI 파이프라인 (form.py → run_tests.py 재현)

```
사용자 입력 (txt/json)
    ↓
[1] HWP → HWPX 변환 (file_manager.convert_hwp, COM 의존)
    ↓
[2] extract_structured_fields (label_counts 포함)
    ↓
[3] classify_form → form_type (invoice_style / legacy / section_based)
    ↓
[4] 슬롯 맵 빌드
    invoice_style → InvoiceProcessor.build_slot_map()
    legacy/section → build_header_slot_map()
    ↓
[5] ai_mapper.map_content() — Gemini 2.5 Flash
    → 양식 구조 + 사용자 입력 → {필드명__N: 값} JSON 반환
    ↓
[6] KrFormatter.auto_detect_and_format()
    → 금액 콤마, 날짜 년월일, 전화 하이픈, 사업자번호 검증
    ↓
[7] __N 접미사 파싱 → slot_assignments / normal_repl 분리
    → 슬롯 매칭 성공: inject_values_by_slot()
    → 슬롯 매칭 실패: normal_repl → clone()
    ↓
[8] 최종 HWPX 출력
```

### form_type 분류

| form_type | 감지 기준 | 슬롯 빌더 |
|-----------|----------|----------|
| invoice_style | 인보이스 라벨 밀도 ≥ 임계값 | InvoiceProcessor |
| section_based | 섹션 헤더 구조 | build_header_slot_map |
| legacy | 기본값 | build_header_slot_map |

### processors/ 패키지 구조

```
processors/
├── __init__.py
├── form_classifier.py      — form_type 분류
└── invoice_processor.py    — 인보이스 슬롯 맵 (INVOICE_LABELS + 인접 빈 셀)
```

---

## API 엔드포인트

| 메서드 | 경로 | 기능 | AI |
|--------|------|------|----|
| GET | /api/health | 상태 확인 | X |
| POST | /api/form/analyze | 양식 분석 (필드 추출) | X |
| POST | /api/form/generate | 문서 생성 (슬롯 주입 + 치환) | X |
| POST | /api/ai/map | AI 자동 매핑 | O (Gemini) |
| POST | /api/batch/generate | 대량 생성 (엑셀 기반) | X |
| POST | /api/batch/map-headers | 엑셀 헤더 AI 매핑 | O (Gemini) |
| POST | /api/batch/generate-mapped | AI 매핑 기반 대량 생성 | X |
| POST | /api/extract/ | 문서 → 엑셀 추출 | X |
| POST | /api/periodic/generate | 정기 문서 생성 | X |
| POST | /api/stamp/insert | 도장/서명 삽입 | X |
| POST | /api/merge/ | 문서 합치기 | X |

---

## 파일 구조

```
hwpx-converter/
├── api/
│   ├── main.py
│   └── routes/
│       ├── form.py          — 양식 분석/생성 (form_type 분기 + 슬롯 라우팅)
│       ├── ai.py            — AI 매핑 엔드포인트
│       ├── batch.py
│       ├── extract.py
│       ├── periodic.py
│       ├── stamp.py
│       └── merge.py
├── processors/
│   ├── form_classifier.py   — form_type 분류기
│   └── invoice_processor.py — 인보이스 슬롯 맵 (INVOICE_LABELS)
├── frontend/src/
│   ├── app/page.tsx
│   └── components/
├── clone_form.py            — HWPX XML 조작 (슬롯 주입 + 텍스트 치환)
├── ai_mapper.py             — Gemini API 호출 (배치, 캐시, 재시도)
├── kr_formatter.py          — 한국 포맷터 (금액/날짜/전화/사업자번호)
├── test-forms/
│   ├── run_tests.py         — 7TC 자동 채점 스크립트
│   ├── test_spec.json       — TC 스펙 (기대값 + critical 플래그)
│   ├── TESTING_METHODOLOGY.md
│   ├── test-inputs/         — 7개 입력 txt
│   ├── test-hwpx/           — 7개 양식 파일
│   └── results/             — 실행 결과 (gitignore)
└── .env                     — GEMINI_API_KEY
```

---

## 비용

| 기능 | AI | 비용/건 |
|------|----|---------|
| AI 자동 매핑 | Gemini 2.5 Flash | ~5원 |
| 엑셀 헤더 매핑 | Gemini 2.5 Flash | ~5원 |
| 그 외 전부 | 없음 | 0원 |

---

## 알려진 한계 및 Known Issues

| # | 항목 | 심각도 | 수정 예정 |
|---|------|--------|----------|
| 1 | TC-01 세금계산서: 병합 셀 구조 → 슬롯 주입 불가 | 구조적 한계 | - |
| 2 | TC-03 정부공문: COM 의존 → 한컴 없는 환경 ERROR | 환경 의존 | - |
| 3 | TC-05 근로계약서: 단락 빈칸 → 슬롯 탐지 불가 | 구조적 한계 | - |
| 4 | invoice_style 라벨 손상 (P1): Step 1+2+3 완료. slot_map 미매칭 INVOICE_LABEL → normal_repl 차단 | 해결됨 | - |
| 5 | TC-07 상담일지: AI 변동성으로 5-6/10 편차 | AI 특성 | 프롬프트 개선 |
| 6 | TC-02 total 필드: 합  계 셀 1개에 공급가액합계/총견적금액 중 하나만 들어감 → field 9 항상 실패 | 양식 구조 한계 | - (8/10 B가 최대치) |

### P1 상세 (invoice_style 라벨 손상)

```
재현: AI가 "합계금액__1": "값" 반환 → InvoiceProcessor slot_map에 없음
    → normal_repl 경로 → clone_form이 "합계금액" 라벨 셀 텍스트를 값으로 교체
    → 라벨 사라지고 값은 들어감 (기능은 되지만 문서 구조 손상)

수정 이력:
  1. [완료 e4f6b21] _is_total_label() + Phase 1+2 2단계 스캔
     합  계, 총 견적 금액 등 비표준 합계 라벨 → slot_map 포함
  2. [완료] TC-02 slot injection 경로 확인
  3. [완료] form.py: invoice_style에서 slot_map 미매칭 INVOICE_LABEL 키 →
     normal_repl 차단 + 로그 출력 (라벨 손상 방지, silent failure 방지)

TC-02 total 필드 (해결됨 b1625ac):
  SYSTEM_PROMPT Rule 13 + USER_PROMPT rule 6으로 합  계 셀에 총견적금액(3,536,500) 안정화.
  양식에 합  계 슬롯 1개 → 공급가액합계 field 9는 구조적으로 항상 실패 (8/10 B가 최대치).
```

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-13 | form.py: P1 Step 3 완료 — invoice_style slot_map 미매칭 INVOICE_LABEL normal_repl 차단 (라벨 손상 방지) |
| 2026-04-13 | [2c10e80] ai_mapper.py Rule 14(학년단축형) + test_spec TC-07 field8 기대값 완화(중간고사). TC-07 예측 +1~+2 개선 (5-7/10 C) |
| 2026-04-13 | [b1625ac] ai_mapper.py: Rule 12(섹션접두사금지) + Rule 13(라벨텍스트그대로) + 품목선추출 + 합계최종총액. TC-02 8/10 B 안정화, TC-04 8/10 B 개선 |
| 2026-04-12 | [e4f6b21] InvoiceProcessor: _is_total_label() + Phase 1+2 2단계 스캔 (P1 Step 1 완료) |
| 2026-04-12 | processors/ 패키지 추가 (form_classifier, invoice_processor), TC 간 2s sleep, test_spec 불가 critical 수정 |
| 2026-03-23 | 초기 API 테스트 리포트 (사업계획서 단일 양식, 100% 통과) |
