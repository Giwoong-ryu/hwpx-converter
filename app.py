"""
HWPX Converter - Gradio Web App
Excel/CSV, JSON, 이미지 -> HWPX 문서 변환

HuggingFace Spaces 배포용
"""
import json
import os
import re
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

import gradio as gr

_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_DIR not in sys.path:
    sys.path.insert(0, _PROJECT_DIR)

from core.xml_utils import reset_id_counter
from core.json_to_section import generate_section_xml, create_header
from core.build_hwpx import build, AVAILABLE_TEMPLATES
from excel_parser import parse_file


# CSS는 style.css 파일 참조
_CSS_PATH = os.path.join(_PROJECT_DIR, "style.css")


# === 히어로 HTML ===

HERO_HTML = """
<div class="hero-section">
    <h1 class="hero-title">HWPX Converter</h1>
    <p class="hero-sub">
        Excel, CSV, JSON, 이미지 파일을 한글 문서(HWPX)로 변환합니다<br>
        API 키 없이 브라우저에서 바로 사용하세요
    </p>
    <div class="hero-badges">
        <span class="badge">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            .xlsx
        </span>
        <span class="badge">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            .csv
        </span>
        <span class="badge">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#0891b2" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            .json
        </span>
        <span class="badge">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
            Image
        </span>
        <span class="badge">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            No API Key
        </span>
    </div>
    <p style="margin: 20px 0 0; font-size: 13px; color: #94a3b8;">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" style="vertical-align: -1px; margin-right: 4px;"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        업로드된 파일은 서버에 저장되지 않으며, 어떠한 데이터도 수집하지 않습니다
    </p>
</div>
"""


# === 공통 빌드 함수 ===

def build_hwpx_from_structure(
    doc_structure: dict,
    template: str = "report",
    title: str = "",
    creator: str = "",
    progress=gr.Progress(),
) -> tuple[str | None, str]:
    """구조 JSON -> HWPX 파일 생성"""
    reset_id_counter()
    progress(0.1, desc="XML 구조 생성 중...")

    with tempfile.TemporaryDirectory() as tmpdir:
        xml_dir = os.path.join(tmpdir, "xml")
        os.makedirs(xml_dir, exist_ok=True)

        template_name = template if template else "report"
        generate_section_xml(doc_structure, xml_dir)
        create_header(xml_dir, template=template_name)
        progress(0.5, desc="HWPX 빌드 중...")

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
            raise gr.Error("빌드 오류: " + ", ".join(errors))

        progress(0.9, desc="파일 준비 중...")
        final_path = os.path.join(tempfile.gettempdir(), output_name)
        shutil.copy2(output_path, final_path)

        sections = doc_structure.get("sections", [])
        table_count = sum(1 for s in sections if s.get("type") == "table")
        para_count = sum(1 for s in sections if s.get("type") == "paragraph")

        progress(1.0, desc="완료!")
        log = f"변환 완료\n"
        log += f"  제목: {doc_title}\n"
        log += f"  템플릿: {template_name}\n"
        log += f"  내용: 테이블 {table_count}개, 문단 {para_count}개\n"
        log += f"  파일: {output_name}"

        gr.Info("HWPX 변환이 완료되었습니다")
        return final_path, log


# === 모드별 처리 함수 ===

def process_excel(file, template, title, creator, progress=gr.Progress()):
    if file is None:
        raise gr.Error("파일을 업로드해주세요")
    try:
        progress(0.05, desc="파일 분석 중...")
        doc_structure = parse_file(file.name)
        return build_hwpx_from_structure(doc_structure, template, title, creator, progress)
    except gr.Error:
        raise
    except Exception as e:
        raise gr.Error(f"Excel 파싱 오류: {e}")


def process_json(json_text, template, title, creator, progress=gr.Progress()):
    if not json_text or not json_text.strip():
        raise gr.Error("JSON을 입력해주세요")
    try:
        doc_structure = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise gr.Error(f"JSON 파싱 오류: {e}")
    if "sections" not in doc_structure:
        raise gr.Error("JSON에 'sections' 키가 필요합니다")
    return build_hwpx_from_structure(doc_structure, template, title, creator, progress)


def process_image(image, template, title, creator, ocr_engine, gemini_key, progress=gr.Progress()):
    if image is None:
        raise gr.Error("이미지를 업로드해주세요")
    try:
        progress(0.05, desc="OCR 분석 중...")
        from ocr_engine import process_image as run_ocr
        doc_structure = run_ocr(image, engine=ocr_engine, api_key=gemini_key or "")
        return build_hwpx_from_structure(doc_structure, template, title, creator, progress)
    except gr.Error:
        raise
    except ImportError as e:
        raise gr.Error(f"OCR 모듈 로드 실패: {e}")
    except Exception as e:
        raise gr.Error(f"이미지 처리 오류: {e}")


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
        {"type": "paragraph", "content": ""},
        {
            "type": "table",
            "table": {
                "rows": 4, "cols": 3,
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


# === 푸터 HTML ===

FOOTER_HTML = """
<div class="footer-section">
    <div class="footer-links">
        <a href="https://github.com/Giwoong-ryu/hwpx-converter" target="_blank">GitHub</a>
        <a href="https://en.wikipedia.org/wiki/OWPML" target="_blank">OWPML 표준</a>
    </div>
    <p class="footer-copy">
        HWPX (OWPML) 표준 기반 &middot; API 키 없이 사용 가능 &middot; MIT License
    </p>
</div>
"""


# === Gradio UI ===

def create_app():
    theme = gr.themes.Soft(
        primary_hue=gr.themes.colors.purple,
        secondary_hue=gr.themes.colors.blue,
        neutral_hue=gr.themes.colors.slate,
        radius_size=gr.themes.sizes.radius_lg,
        spacing_size=gr.themes.sizes.spacing_md,
        font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
    ).set(
        body_background_fill="transparent",
        block_background_fill="rgba(255,255,255,0.5)",
        block_border_width="1px",
        block_border_color="rgba(124,58,237,0.08)",
        block_shadow="0 1px 3px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.02)",
        block_radius="12px",
        button_primary_background_fill="linear-gradient(135deg, #7c3aed, #6d28d9)",
        button_primary_text_color="white",
        button_primary_border_color="transparent",
        input_radius="10px",
        input_border_color="rgba(124,58,237,0.15)",
    )

    with gr.Blocks(title="HWPX Converter", theme=theme, css_paths=[_CSS_PATH]) as app:

        # 히어로
        gr.HTML(HERO_HTML)

        # 메인 컨테이너
        with gr.Column(elem_classes="glass-card"):

            # 문서 스타일 (항상 표시)
            template = gr.Radio(
                choices=[
                    ("입력 형식 유지", "auto"),
                    ("보고서", "report"),
                    ("공문", "gonmun"),
                    ("회의록", "minutes"),
                    ("제안서", "proposal"),
                ],
                value="auto",
                label="문서 스타일",
                info="입력 형식 유지: 원본 색상 그대로 | 보고서: 파란 회색 | 공문: 굵은 테두리 | 회의록: 초록 | 제안서: 네이비",
            )

            # 추가 설정 (접힘)
            with gr.Accordion("추가 설정", open=False):
                with gr.Row():
                    title_input = gr.Textbox(
                        label="문서 제목",
                        placeholder="비워두면 자동 추출",
                    )
                    creator_input = gr.Textbox(
                        label="작성자",
                        placeholder="HWPX Converter",
                    )

            # 탭
            with gr.Tabs():

                # Excel/CSV
                with gr.TabItem("Excel / CSV"):
                    gr.HTML("""<div class="mode-desc">
                        <span class="mode-icon">&#x1F4CA;</span>
                        <div class="mode-text">
                            <h4>스프레드시트 변환</h4>
                            <p>.xlsx, .xls, .csv 파일을 업로드하면 테이블 구조를 자동 파싱합니다. 병합 셀, 굵기, 색상, 정렬이 그대로 반영됩니다.</p>
                        </div>
                    </div>""")
                    excel_file = gr.File(
                        label="파일 업로드",
                        file_types=[".xlsx", ".xls", ".csv"],
                        elem_classes="file-upload",
                    )
                    excel_btn = gr.Button(
                        "HWPX 변환",
                        variant="primary",
                        elem_classes="primary-btn",
                    )
                    excel_output = gr.File(label="변환된 파일", elem_classes="result-box")
                    excel_log = gr.Textbox(label="결과", lines=4, interactive=False)

                    excel_btn.click(
                        fn=process_excel,
                        inputs=[excel_file, template, title_input, creator_input],
                        outputs=[excel_output, excel_log],
                    )

                # JSON
                with gr.TabItem("JSON"):
                    gr.HTML("""<div class="mode-desc">
                        <span class="mode-icon">&#x1F4DD;</span>
                        <div class="mode-text">
                            <h4>구조 JSON 직접 입력</h4>
                            <p>HWPX 구조 JSON을 입력하여 문서를 생성합니다. 프로그래밍 방식으로 대량의 문서를 자동 생성할 때 유용합니다.</p>
                        </div>
                    </div>""")
                    json_input = gr.Textbox(
                        label="구조 JSON",
                        lines=16,
                        placeholder='{"document": {"title": "..."}, "sections": [...]}',
                    )
                    with gr.Row():
                        json_example_btn = gr.Button(
                            "예제 불러오기",
                            variant="secondary",
                            elem_classes="secondary-btn",
                        )
                        json_btn = gr.Button(
                            "HWPX 변환",
                            variant="primary",
                            elem_classes="primary-btn",
                        )
                    json_output = gr.File(label="변환된 파일", elem_classes="result-box")
                    json_log = gr.Textbox(label="결과", lines=4, interactive=False)

                    json_example_btn.click(fn=lambda: EXAMPLE_JSON, outputs=[json_input])
                    json_btn.click(
                        fn=process_json,
                        inputs=[json_input, template, title_input, creator_input],
                        outputs=[json_output, json_log],
                    )

                # 이미지 (OCR)
                with gr.TabItem("이미지 (OCR)"):
                    gr.HTML("""<div class="mode-desc">
                        <span class="mode-icon">&#x1F5BC;</span>
                        <div class="mode-text">
                            <h4>이미지 OCR 변환</h4>
                            <p>문서 이미지를 OCR로 분석하여 HWPX로 변환합니다. PaddleOCR(기본)은 API 키 없이 사용 가능합니다.</p>
                        </div>
                    </div>""")
                    image_input = gr.Image(label="문서 이미지", type="filepath")
                    with gr.Row():
                        ocr_engine = gr.Radio(
                            choices=["paddle", "gemini"],
                            value="paddle",
                            label="OCR 엔진",
                            info="PaddleOCR: 무료 | Gemini: 고정밀 (API Key 필요)",
                        )
                        gemini_key = gr.Textbox(
                            label="Gemini API Key",
                            type="password",
                            placeholder="Gemini 선택 시 입력",
                        )
                    image_btn = gr.Button(
                        "HWPX 변환",
                        variant="primary",
                        elem_classes="primary-btn",
                    )
                    image_output = gr.File(label="변환된 파일", elem_classes="result-box")
                    image_log = gr.Textbox(label="결과", lines=4, interactive=False)

                    image_btn.click(
                        fn=process_image,
                        inputs=[image_input, template, title_input, creator_input, ocr_engine, gemini_key],
                        outputs=[image_output, image_log],
                    )

        # 푸터
        gr.HTML(FOOTER_HTML)

    return app


if __name__ == "__main__":
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860)
