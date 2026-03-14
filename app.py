"""
HWPX Converter - Gradio Web App
Excel/CSV, JSON, 이미지 -> HWPX 문서 변환

HuggingFace Spaces 배포용
"""
import json
import os
import re
import sys
import tempfile
import uuid
from pathlib import Path

import gradio as gr

# 프로젝트 루트를 sys.path에 1회만 추가 (HF Spaces 호환)
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_DIR not in sys.path:
    sys.path.insert(0, _PROJECT_DIR)

from core.xml_utils import reset_id_counter
from core.json_to_section import generate_section_xml, create_header
from core.build_hwpx import build, AVAILABLE_TEMPLATES
from excel_parser import parse_file


# === 공통 빌드 함수 ===

def build_hwpx_from_structure(
    doc_structure: dict,
    template: str = "report",
    title: str = "",
    creator: str = "",
) -> tuple[str | None, str]:
    """구조 JSON -> HWPX 파일 생성. (파일경로, 로그메시지) 반환"""
    reset_id_counter()

    with tempfile.TemporaryDirectory() as tmpdir:
        xml_dir = os.path.join(tmpdir, "xml")
        os.makedirs(xml_dir, exist_ok=True)

        # section0.xml + header.xml 생성
        template_name = template if template else "report"
        generate_section_xml(doc_structure, xml_dir)
        create_header(xml_dir, template=template_name)

        # HWPX 빌드
        doc_title = title or doc_structure.get("document", {}).get("title", "문서")
        safe_title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', doc_title[:30])
        unique_suffix = uuid.uuid4().hex[:8]
        output_name = f"{safe_title}_{unique_suffix}.hwpx"
        output_path = Path(tmpdir) / output_name

        header_path = Path(xml_dir) / "header.xml"
        section_path = Path(xml_dir) / "section0.xml"

        errors = build(
            template=template_name,
            header_override=header_path,
            section_override=section_path,
            title=doc_title,
            creator=creator or "HWPX Converter",
            output=output_path,
        )

        if errors:
            return None, f"[FAIL] 빌드 오류:\n" + "\n".join(f"  - {e}" for e in errors)

        # 임시 파일을 영구 경로로 복사 (UUID로 충돌 방지)
        import shutil
        final_path = os.path.join(tempfile.gettempdir(), output_name)
        shutil.copy2(output_path, final_path)

        sections = doc_structure.get("sections", [])
        table_count = sum(1 for s in sections if s.get("type") == "table")
        para_count = sum(1 for s in sections if s.get("type") == "paragraph")

        log = f"[OK] HWPX 생성 완료\n"
        log += f"  - 제목: {doc_title}\n"
        log += f"  - 템플릿: {template}\n"
        log += f"  - 섹션: 테이블 {table_count}개, 문단 {para_count}개\n"
        log += f"  - 파일: {output_name}"

        return final_path, log


# === 모드별 처리 함수 ===

def process_excel(file, template, title, creator):
    """Excel/CSV 파일 -> HWPX"""
    if file is None:
        return None, "[FAIL] 파일을 업로드해주세요"

    try:
        doc_structure = parse_file(file.name)
        return build_hwpx_from_structure(doc_structure, template, title, creator)
    except Exception as e:
        return None, f"[FAIL] Excel 파싱 오류: {e}"


def process_json(json_text, template, title, creator):
    """JSON 텍스트 -> HWPX"""
    if not json_text or not json_text.strip():
        return None, "[FAIL] JSON을 입력해주세요"

    try:
        doc_structure = json.loads(json_text)
    except json.JSONDecodeError as e:
        return None, f"[FAIL] JSON 파싱 오류: {e}"

    if "sections" not in doc_structure:
        return None, "[FAIL] JSON에 'sections' 키가 필요합니다"

    return build_hwpx_from_structure(doc_structure, template, title, creator)


def process_image(image, template, title, creator, ocr_engine, gemini_key):
    """이미지 -> HWPX"""
    if image is None:
        return None, "[FAIL] 이미지를 업로드해주세요"

    try:
        from ocr_engine import process_image as run_ocr
        doc_structure = run_ocr(image, engine=ocr_engine, api_key=gemini_key or "")
        return build_hwpx_from_structure(doc_structure, template, title, creator)
    except ImportError as e:
        return None, f"[FAIL] OCR 모듈 로드 실패: {e}\nPaddleOCR가 설치되어 있는지 확인하세요."
    except Exception as e:
        return None, f"[FAIL] 이미지 처리 오류: {e}"


# === JSON 예제 ===

EXAMPLE_JSON = json.dumps({
    "document": {"title": "회의록", "page_width_hu": 42520},
    "sections": [
        {
            "type": "paragraph",
            "content": "2026년 3월 정기 회의록",
            "align": "CENTER",
            "style": {"bold": True, "font_size_pt": 18}
        },
        {
            "type": "paragraph",
            "content": "",
        },
        {
            "type": "table",
            "table": {
                "rows": 4,
                "cols": 3,
                "col_widths_ratio": [20, 40, 40],
                "cells": [
                    {"row": 0, "col": 0, "text": "구분", "style": {"bold": True, "align": "CENTER", "is_header": True, "bg_color": "#D6DCE4"}},
                    {"row": 0, "col": 1, "text": "내용", "style": {"bold": True, "align": "CENTER", "is_header": True, "bg_color": "#D6DCE4"}},
                    {"row": 0, "col": 2, "text": "비고", "style": {"bold": True, "align": "CENTER", "is_header": True, "bg_color": "#D6DCE4"}},
                    {"row": 1, "col": 0, "text": "일시", "style": {"bold": True, "align": "CENTER"}},
                    {"row": 1, "col": 1, "text": "2026년 3월 14일 14:00", "style": {"align": "LEFT"}},
                    {"row": 1, "col": 2, "text": "", "style": {"align": "LEFT"}},
                    {"row": 2, "col": 0, "text": "장소", "style": {"bold": True, "align": "CENTER"}},
                    {"row": 2, "col": 1, "text": "본사 3층 회의실", "style": {"align": "LEFT"}},
                    {"row": 2, "col": 2, "text": "", "style": {"align": "LEFT"}},
                    {"row": 3, "col": 0, "text": "참석자", "style": {"bold": True, "align": "CENTER"}},
                    {"row": 3, "col": 1, "text": "홍길동, 김철수, 이영희", "style": {"align": "LEFT"}},
                    {"row": 3, "col": 2, "text": "총 3명", "style": {"align": "LEFT"}},
                ]
            }
        }
    ]
}, ensure_ascii=False, indent=2)


# === Gradio UI ===

def create_app():
    with gr.Blocks(
        title="HWPX Converter",
        theme=gr.themes.Soft(),
    ) as app:
        gr.Markdown("# HWPX Converter")
        gr.Markdown("Excel/CSV, JSON, 이미지를 한글(HWPX) 문서로 변환합니다.")

        with gr.Row():
            template = gr.Dropdown(
                choices=AVAILABLE_TEMPLATES,
                value="report",
                label="문서 템플릿",
            )
            title_input = gr.Textbox(label="문서 제목 (선택)", placeholder="비워두면 자동 추출")
            creator_input = gr.Textbox(label="작성자 (선택)", placeholder="HWPX Converter")

        with gr.Tabs():
            # Tab 1: Excel/CSV
            with gr.TabItem("Excel / CSV"):
                gr.Markdown("`.xlsx`, `.xls`, `.csv` 파일을 업로드하면 테이블 구조를 자동 파싱합니다.")
                gr.Markdown("병합 셀, 스타일(굵기/색상/정렬)도 반영됩니다.")
                excel_file = gr.File(
                    label="파일 업로드",
                    file_types=[".xlsx", ".xls", ".csv"],
                )
                excel_btn = gr.Button("HWPX 변환", variant="primary")
                excel_output = gr.File(label="다운로드")
                excel_log = gr.Textbox(label="변환 로그", lines=5, interactive=False)

                excel_btn.click(
                    fn=process_excel,
                    inputs=[excel_file, template, title_input, creator_input],
                    outputs=[excel_output, excel_log],
                )

            # Tab 2: JSON
            with gr.TabItem("JSON"):
                gr.Markdown("HWPX 구조 JSON을 직접 입력합니다. 프로그래밍 방식으로 문서를 생성할 때 유용합니다.")
                json_input = gr.Textbox(
                    label="구조 JSON",
                    lines=20,
                    placeholder="JSON을 입력하세요...",
                )
                with gr.Row():
                    json_example_btn = gr.Button("예제 불러오기")
                    json_btn = gr.Button("HWPX 변환", variant="primary")
                json_output = gr.File(label="다운로드")
                json_log = gr.Textbox(label="변환 로그", lines=5, interactive=False)

                json_example_btn.click(
                    fn=lambda: EXAMPLE_JSON,
                    outputs=[json_input],
                )
                json_btn.click(
                    fn=process_json,
                    inputs=[json_input, template, title_input, creator_input],
                    outputs=[json_output, json_log],
                )

            # Tab 3: 이미지
            with gr.TabItem("이미지 (OCR)"):
                gr.Markdown("문서 이미지를 OCR로 분석하여 HWPX로 변환합니다.")
                gr.Markdown("- **PaddleOCR** (기본): API 키 불필요, 서버에서 처리")
                gr.Markdown("- **Gemini Vision** (선택): 더 정확한 레이아웃 분석, API 키 필요")
                image_input = gr.Image(label="문서 이미지", type="filepath")
                with gr.Row():
                    ocr_engine = gr.Radio(
                        choices=["paddle", "gemini"],
                        value="paddle",
                        label="OCR 엔진",
                    )
                    gemini_key = gr.Textbox(
                        label="Gemini API Key (Gemini 선택 시)",
                        type="password",
                        placeholder="AIzaSy...",
                    )
                image_btn = gr.Button("HWPX 변환", variant="primary")
                image_output = gr.File(label="다운로드")
                image_log = gr.Textbox(label="변환 로그", lines=5, interactive=False)

                image_btn.click(
                    fn=process_image,
                    inputs=[image_input, template, title_input, creator_input, ocr_engine, gemini_key],
                    outputs=[image_output, image_log],
                )

        gr.Markdown("---")
        gr.Markdown("HWPX (OWPML) 표준 기반 | API 키 없이 사용 가능 | [GitHub](https://github.com)")

    return app


if __name__ == "__main__":
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860)
