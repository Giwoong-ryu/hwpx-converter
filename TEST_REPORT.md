# DocFlow API 테스트 리포트

**테스트 일시**: 2026-03-23
**환경**: Windows 11 / FastAPI (localhost:8000) + Next.js (localhost:3000)
**테스트 양식**: 사업계획서_양식.hwpx (409개 필드)

## 테스트 결과 요약

| 결과 | 건수 |
|------|------|
| OK | 10 |
| SKIP | 1 (양식에 해당 텍스트 없음) |
| FAIL | 0 |
| **총 통과율** | **100%** |

## 상세 결과

| # | 기능 | API | 결과 | 상세 |
|---|------|-----|------|------|
| 1 | Health Check | GET /api/health | OK | {"status": "ok"} |
| 2 | 양식 분석 | POST /api/form/analyze | OK | 409개 필드 추출 |
| 3 | AI 자동 매핑 | POST /api/ai/map | OK | 2개 매핑 (회사명, 설립일) |
| 4 | 문서 생성 | POST /api/form/generate | OK | 3,781,149 bytes |
| 5 | 내용 뽑기 | POST /api/extract/ | OK | 27,088 bytes xlsx |
| 6 | 도장 삽입 | POST /api/stamp/insert | SKIP | 양식에 "(인)" 텍스트 없음 |
| 7 | 문서 합치기 | POST /api/merge/ | OK | 3,806,910 bytes |
| 8 | 정기 문서 | POST /api/periodic/generate | OK | 11,263,497 bytes (3개월분 zip) |
| 9 | 대량 생성 (기존) | POST /api/batch/generate | OK | 7,508,982 bytes (2건 zip) |
| 10 | 대량 생성 AI 매핑 | POST /api/batch/map-headers | OK | 3개 헤더 매핑, 2행 데이터 |

## API 엔드포인트 목록

| 메서드 | 경로 | 기능 | AI 사용 |
|--------|------|------|---------|
| GET | /api/health | 상태 확인 | X |
| POST | /api/form/analyze | 양식 파일 분석 (HWP/HWPX) | X |
| POST | /api/form/generate | 매핑 결과로 문서 생성 | X |
| POST | /api/ai/map | AI 자동 매핑 | O (Gemini) |
| POST | /api/batch/generate | 대량 생성 (엑셀 1행=원본) | X |
| POST | /api/batch/map-headers | 엑셀 헤더 AI 매핑 | O (Gemini) |
| POST | /api/batch/generate-mapped | AI 매핑 기반 대량 생성 | X |
| POST | /api/extract/ | 문서 -> 엑셀 추출 | X |
| POST | /api/periodic/generate | 정기 문서 생성 | X |
| POST | /api/stamp/insert | 도장/서명 삽입 | X |
| POST | /api/merge/ | 문서 합치기 | X |

## 파일 구조

```
hwpx-converter/
├── api/                    # FastAPI 백엔드
│   ├── main.py
│   ├── routes/
│   │   ├── form.py         # 양식 분석/생성
│   │   ├── ai.py           # AI 매핑
│   │   ├── batch.py        # 대량 생성
│   │   ├── extract.py      # 내용 뽑기
│   │   ├── periodic.py     # 정기 문서
│   │   ├── stamp.py        # 도장 삽입
│   │   └── merge.py        # 문서 합치기
│   └── services/
│       └── file_manager.py # 파일 관리
├── frontend/               # Next.js 프론트엔드
│   └── src/
│       ├── app/page.tsx    # 메인 페이지
│       ├── components/     # UI 컴포넌트
│       ├── lib/api.ts      # API 클라이언트
│       └── context/        # 상태 관리
├── clone_form.py           # 양식 복제 (기존)
├── ai_mapper.py            # AI 매핑 (기존)
├── features.py             # 확장 기능 (기존)
└── .env                    # API 키
```

## 비용

| 기능 | AI 사용 | 비용/건 |
|------|---------|---------|
| AI 자동 매핑 | Gemini 2.5 Flash | ~5원 |
| 엑셀 헤더 AI 매핑 | Gemini 2.5 Flash | ~5원 |
| 그 외 전부 | 없음 | 0원 |

## 보안

| 기능 | 데이터 전송 |
|------|-----------|
| AI 매핑 (2건) | Google Gemini API (유료, 학습 미사용, 55일 로그 후 삭제) |
| 그 외 (9건) | 로컬 PC에서만 처리, 외부 전송 없음 |

## 추가 테스트

| # | 기능 | 결과 | 상세 |
|---|------|------|------|
| 11 | HWP -> HWPX 변환 | OK | win32com 자동 변환, 409개 필드 추출 성공 |

### 엑셀 채우기 테스트

| # | 기능 | 결과 | 상세 |
|---|------|------|------|
| 12 | 엑셀 양식 분석 | OK | 11개 셀 발견 |
| 13 | 엑셀 대량 생성 (2건) | OK | 9,212 bytes zip (김철수.xlsx, 박영희.xlsx) |
| 14 | 엑셀 단건 채우기 | OK | 5,043 bytes |

## 미구현/제한사항

- 도장 삽입: 양식에 "(인)" 텍스트가 있어야 동작 (SKIP)
- HWP -> HWPX 변환: Windows + 한컴오피스 필요 (설치되어 있으면 자동 변환 OK)
- 엑셀 양식 채우기: 구현 완료 (분석/단건/대량 전부 OK)
