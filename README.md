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

Excel/CSV, JSON, 이미지를 한글(HWPX) 문서로 변환하는 웹 앱입니다.

## 입력 모드

| 모드 | 설명 | API 필요 |
|------|------|----------|
| Excel/CSV | 병합 셀, 스타일 자동 파싱 | X |
| JSON | HWPX 구조 JSON 직접 입력 | X |
| 이미지 (PaddleOCR) | OCR로 문서 인식 | X |
| 이미지 (Gemini) | 고정밀 레이아웃 분석 | O (API Key) |

## 템플릿

- report (보고서)
- gonmun (공문)
- minutes (회의록)
- proposal (제안서)
