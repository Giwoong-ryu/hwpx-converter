# DocFlow AI 파이프라인 테스트 리포트

**최종 갱신**: 2026-04-12
**환경**: Windows 11 / FastAPI (8000) + Next.js
**테스트 범위**: 7TC E2E (AI 매핑 → 슬롯 주입 → 텍스트 치환 → HWPX 출력)

---

## 7TC 기준선 (2026-04-12 기준)

| TC | 양식 | 정확도 | 등급 | 상태 |
|----|------|--------|------|------|
| TC-01 | 세금계산서 | 3-4/10 | D | 구조적 한계 (병합 셀) |
| TC-02 | 견적서 | 8/10 | B | 안정 |
| TC-03 | 정부공문 | ERROR | - | COM 환경 필요 (한컴 설치 시만 동작) |
| TC-04 | 사업제안서 | 7/10 | C | 안정 |
| TC-05 | 표준근로계약서 | 2/10 | D | 구조적 한계 (단락 빈칸) |
| TC-06 | 납품확인서 | 2/10 | D | 구조적 한계 (양식 필드 부재) |
| TC-07 | 상담일지 | 5-6/10 | C | 안정 (AI 변동성 있음) |

### 등급 기준

| 등급 | 기준 |
|------|------|
| A | 90%+ |
| B | 80-89% |
| C | 50-79% |
| D | 50% 미만 또는 critical 필드 실패 |

### 구조적 D — 코드 버그 아님

TC-01, TC-03, TC-05, TC-06은 양식 자체의 구조적 제약으로 현재 파이프라인으로 해결 불가:

| TC | 원인 |
|----|------|
| TC-01 | 공급자/공급받는자 정보가 병합 셀 내부에 있어 빈 셀 슬롯을 만들 수 없음 |
| TC-03 | .hwp 파일 → HWPX 변환에 Windows COM + 한컴오피스 필요 |
| TC-05 | 서명란, 날짜란이 표 셀이 아닌 단락 빈칸 형식 |
| TC-06 | 검수확인서 구조 — 기대하는 필드(발주처, 수량 합계 등)가 양식에 없음 |

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
| 4 | invoice_style 라벨 손상 (P1): InvoiceProcessor slot_map 누락 시 라벨 셀 교체 | P1 | InvoiceProcessor 보강 후 |
| 5 | TC-07 상담일지: AI 변동성으로 5-6/10 편차 | AI 특성 | 프롬프트 개선 |

### P1 상세 (invoice_style 라벨 손상)

```
재현: AI가 "합계금액__1": "값" 반환 → InvoiceProcessor slot_map에 없음
    → normal_repl 경로 → clone_form이 "합계금액" 라벨 셀 텍스트를 값으로 교체
    → 라벨 사라지고 값은 들어감 (기능은 되지만 문서 구조 손상)

수정 순서:
  1. InvoiceProcessor.build_slot_map()에 합계 라벨 + 인접 빈 셀 슬롯 추가
  2. TC-02 슬롯 주입 경로 확인
  3. form.py normal_repl INVOICE_LABELS 차단 적용
```

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-12 | processors/ 패키지 추가 (form_classifier, invoice_processor), TC 간 2s sleep, test_spec 불가 critical 수정 |
| 2026-03-23 | 초기 API 테스트 리포트 (사업계획서 단일 양식, 100% 통과) |
