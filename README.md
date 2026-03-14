---
title: HWPX Converter
emoji: 📄
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 5.34.2
app_file: app.py
pinned: false
license: mit
---

# HWPX Converter

Excel, CSV, JSON, 이미지 파일을 한글 문서(HWPX)로 변환하는 웹 앱입니다.
API 키 없이 바로 사용할 수 있습니다.

## 사용법

### 1. Excel / CSV
- `.xlsx`, `.xls`, `.csv` 파일을 업로드하면 테이블 구조를 자동으로 파싱합니다.
- 병합 셀, 굵기, 색상, 정렬 등 스타일이 그대로 반영됩니다.

### 2. JSON
- HWPX 구조 JSON을 직접 입력하여 문서를 생성합니다.
- "예제 불러오기" 버튼으로 샘플 구조를 확인할 수 있습니다.
- 프로그래밍 방식으로 문서를 대량 생성할 때 유용합니다.

### 3. 이미지 (OCR)
- 문서 이미지를 업로드하면 OCR로 텍스트를 인식하여 HWPX로 변환합니다.
- **PaddleOCR** (기본): 서버에서 처리, API 키 불필요
- **Gemini Vision** (선택): 더 정확한 레이아웃 분석, 본인의 Gemini API Key 입력 필요

## 입력 모드 비교

| 모드 | 설명 | API 필요 |
|------|------|----------|
| Excel/CSV | 병합 셀, 스타일 자동 파싱 | X |
| JSON | HWPX 구조 JSON 직접 입력 | X |
| 이미지 (PaddleOCR) | OCR로 문서 인식 | X |
| 이미지 (Gemini) | 고정밀 레이아웃 분석 | O (본인 API Key) |

## 문서 템플릿

| 템플릿 | 용도 |
|--------|------|
| report | 보고서 |
| gonmun | 공문 |
| minutes | 회의록 |
| proposal | 제안서 |

## HWPX란?

HWPX는 한컴오피스 한글의 개방형 문서 포맷(OWPML 표준)입니다.
ZIP 기반 XML 컨테이너로, `.hwpx` 확장자를 사용합니다.
한글 2014 이상에서 열 수 있습니다.

## 로컬 실행

```bash
pip install -r requirements.txt
python app.py
```

브라우저에서 `http://localhost:7860` 접속

## 기술 스택

- **UI**: Gradio
- **XML 생성**: lxml
- **Excel 파싱**: openpyxl
- **OCR**: PaddleOCR (기본) / Gemini Vision API (선택)

## 라이선스

MIT
