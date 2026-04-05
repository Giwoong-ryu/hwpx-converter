"""
DocFlow - 한글 양식 문서 도구
AI 매핑 | 대량 생성 | 양식 추출 | 정기 문서 | 도장 삽입 | 문서 병합
"""
import os
import sys
import tempfile
from datetime import datetime

import gradio as gr

_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

from clone_form import extract_texts, clone as clone_hwpx
from ai_mapper import map_content
from features import (
    batch_generate, extract_to_excel, generate_periodic,
    insert_stamp, merge_documents,
)


# ── 공통 유틸 ──

def _convert_hwp(path, progress=None):
    if not path.lower().endswith(".hwp"):
        return path
    try:
        if progress:
            progress(0.2, desc="HWP -> HWPX 변환 중...")
        import win32com.client
        hwp = win32com.client.gencache.EnsureDispatch("HWPFrame.HwpObject")
        hwp.RegisterModule("FilePathCheckDLL", "SecurityModule")
        hwp.Open(path, "HWP", "forceopen:true")
        hwpx_path = os.path.join(tempfile.mkdtemp(), "converted.hwpx")
        hwp.SaveAs(hwpx_path, "HWPX")
        hwp.Clear(1)
        hwp.Quit()
        return hwpx_path
    except Exception as e:
        raise gr.Error(f"HWP 변환 실패: {e}")


def _msg(text, style="ok"):
    if style == "ok":
        return f'<div class="msg msg-ok">{text}</div>'
    if style == "final":
        return f'<div class="msg msg-final">{text}</div>'
    return f'<div class="msg msg-info">{text}</div>'


# ── Tab 1: AI 매핑 ──

def analyze(file, progress=gr.Progress()):
    if file is None:
        raise gr.Error("양식 파일을 먼저 업로드해주세요.")
    path = file.name if hasattr(file, "name") else str(file)
    progress(0.1, desc="파일 확인 중...")
    path = _convert_hwp(path, progress)
    progress(0.5, desc="텍스트 추출 중...")
    texts = extract_texts(path)
    if not texts:
        raise gr.Error("텍스트를 추출할 수 없습니다.")
    progress(0.9, desc="완료!")
    fname = os.path.basename(path)
    info = _msg(f"<strong>{fname}</strong>에서 {len(texts)}개 필드를 찾았습니다. 아래에서 채울 내용을 입력해주세요.")
    return info, texts, path, gr.update(visible=True), gr.update(visible=True)


def do_mapping(form_path, form_texts, user_text, content_file, progress=gr.Progress()):
    if not form_path:
        raise gr.Error("먼저 양식을 업로드해주세요.")
    if not user_text and not content_file:
        raise gr.Error("내용을 입력하거나 파일을 업로드해주세요.")
    progress(0.3, desc="AI가 내용을 분석하고 있습니다...")
    file_path = None
    if content_file is not None:
        file_path = content_file.name if hasattr(content_file, "name") else str(content_file)
    result, error = map_content(form_texts, user_text, file_path)
    if error:
        raise gr.Error(error)
    progress(0.9, desc="매핑 완료!")
    table_data = [[old, new] for old, new in result.items()]
    info = _msg(f"<strong>{len(result)}개 항목</strong>을 자동으로 매핑했습니다. 아래 표에서 확인 후 수정할 수 있습니다.")
    return info, table_data, gr.update(visible=True)


def do_generate(form_path, table_data, progress=gr.Progress()):
    if not form_path:
        raise gr.Error("먼저 양식을 분석해주세요.")
    progress(0.2, desc="문서 생성 준비 중...")
    replacements = {}
    for row in table_data:
        if len(row) >= 2 and row[1] and str(row[1]).strip():
            old, new = str(row[0]).strip(), str(row[1]).strip()
            if old and old != new:
                replacements[old] = new
    if not replacements:
        raise gr.Error("변경할 항목이 없습니다.")
    progress(0.5, desc="양식에 내용을 채우는 중...")
    out_path = os.path.join(tempfile.mkdtemp(), "DocFlow_result.hwpx")
    clone_hwpx(form_path, out_path, replacements=replacements)
    progress(1.0, desc="완료!")
    size = os.path.getsize(out_path)
    info = _msg(f"{len(replacements)}개 항목이 반영된 문서가 준비되었습니다. ({size:,} bytes)", "final")
    return out_path, info


# ── CSS ──

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Pretendard+Variable:wght@300;400;500;600;700&display=swap');
.gradio-container {
    font-family: 'Pretendard Variable', -apple-system, 'Segoe UI', sans-serif !important;
    max-width: 1200px !important; margin: 0 auto !important;
    background: #fff !important; padding-top: 0 !important;
}
.gradio-container * { font-family: inherit !important; }
footer, .built-with, .svelte-1rjryqp { display: none !important; }
.gradio-container .row { flex-wrap: nowrap !important; }
.gradio-container .contain { flex-wrap: nowrap !important; }

.app-top { padding: 32px 0 12px; text-align: center; border-bottom: 1px solid #f0f0f0; margin-bottom: 20px; }
.app-top h1 { font-size: 22px; font-weight: 700; color: #111; margin: 0 0 4px; }
.app-top p { font-size: 13px; color: #999; margin: 2px 0 0; line-height: 1.5; }

.sec { background: #fff; border: 1px solid #eee; border-radius: 14px; padding: 22px 26px; margin-bottom: 14px; }
.sec:hover { border-color: #ddd; box-shadow: 0 2px 12px rgba(0,0,0,0.03); }
.sec-title { font-size: 15px; font-weight: 600; color: #222; margin: 0 0 4px; }
.sec-desc { font-size: 13px; color: #999; margin: 0 0 14px; line-height: 1.4; }

.msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; line-height: 1.5; margin: 10px 0 0; }
.msg strong { font-weight: 600; color: #222; }
.msg-ok { background: #f8faf8; border: 1px solid #e6efe6; color: #333; }
.msg-final { background: #f0f7ff; border: 1px solid #d0e3ff; color: #111; text-align: center; padding: 20px; font-size: 14px; }
.msg-info { background: #fffbf0; border: 1px solid #f0e6c8; color: #6b5a30; }

.file-area { border: 1.5px solid #ddd !important; border-radius: 10px !important; background: #fff !important; box-shadow: 0 2px 6px rgba(0,0,0,0.05) !important; }
.file-area:hover { border-color: #aaa !important; box-shadow: 0 3px 10px rgba(0,0,0,0.08) !important; }
.file-area .wrap, .file-area .container { min-height: 50px !important; padding: 10px 8px !important; }
.file-area .icon-wrap svg { width: 18px !important; height: 18px !important; }
.file-area span { font-size: 11px !important; }
.file-area .or { font-size: 10px !important; }

.text-area textarea { min-height: 120px !important; font-size: 13px !important; line-height: 1.6 !important; border: 1.5px solid #e5e5e5 !important; border-radius: 10px !important; padding: 12px 14px !important; background: #fafafa !important; }
.text-area textarea:focus { border-color: #333 !important; background: #fff !important; box-shadow: none !important; }

.or-line { display: flex; align-items: center; gap: 12px; margin: 12px 0; color: #ccc; font-size: 12px; }
.or-line::before, .or-line::after { content: ''; flex: 1; height: 1px; background: #eee; }

.btn-dark { background: #111 !important; border: none !important; color: #fff !important; font-weight: 600 !important; font-size: 14px !important; padding: 11px 28px !important; border-radius: 10px !important; letter-spacing: -0.2px !important; }
.btn-dark:hover { background: #333 !important; transform: translateY(-1px) !important; box-shadow: 0 4px 14px rgba(0,0,0,0.12) !important; }

.tbl { border: 1px solid #eee; border-radius: 10px; overflow: hidden; }
.tbl table { font-size: 13px !important; }
.tbl th { background: #fafafa !important; color: #666 !important; font-weight: 600 !important; font-size: 12px !important; }
.tbl input { border: 1px solid #e5e5e5 !important; border-radius: 6px !important; padding: 5px 8px !important; font-size: 13px !important; }
.tbl input:focus { border-color: #111 !important; box-shadow: none !important; }

.result-dl { margin-top: 12px; }
.app-foot { text-align: center; padding: 20px 16px 28px; font-size: 12px; color: #bbb; line-height: 1.6; }

@media (max-width: 640px) {
    .gradio-container { padding: 0 4px !important; }
    .sec { padding: 16px 16px; }
    .app-top { padding: 24px 0 12px; }
    .app-top h1 { font-size: 19px; }
}
"""

THEME = gr.themes.Base(
    primary_hue=gr.themes.colors.neutral,
    neutral_hue=gr.themes.colors.gray,
    radius_size=gr.themes.sizes.radius_lg,
    font=[gr.themes.GoogleFont("Pretendard Variable"), "system-ui"],
)


# ── 앱 구성 ──

def create_app():
    with gr.Blocks(title="DocFlow") as app:

        gr.HTML("""
        <div class="app-top">
            <h1>DocFlow</h1>
            <p style="font-size:15px; color:#555; margin:6px 0 0;">한글 양식에 내용을 채워 새 문서를 만듭니다</p>
        </div>
        """)

        form_path = gr.State(value=None)
        form_texts = gr.State(value=[])

        with gr.Row():
            # ── 왼쪽: 양식 넣기 ──
            with gr.Column(scale=1, min_width=260):
                with gr.Tabs():
                    with gr.Tab("양식 넣기"):
                        with gr.Group(elem_classes="sec"):
                            gr.HTML('<p class="sec-desc">결과물로 만들 양식을 올리고 분석하세요.</p>')
                            file_input = gr.File(label="양식 파일 (.hwp / .hwpx)", file_types=[".hwp", ".hwpx"], elem_classes="file-area")
                            analyze_btn = gr.Button("양식 분석", variant="primary", elem_classes="btn-dark")
                            status_common = gr.HTML(visible=False)

            # ── 오른쪽: 기능 탭 ──
            with gr.Column(scale=3):
                with gr.Tabs():

                    # ── AI 자동 매핑 ──
                    with gr.Tab("AI 자동 매핑"):
                        with gr.Group(elem_classes="sec"):
                            gr.HTML("""<p class="sec-desc" style="margin-bottom:10px;">
                                채울 내용을 입력하면 AI가 양식에 맞게 자동 매핑합니다.
                                <span style="color:#888; font-size:11px;">(이 기능에서만 Google AI 사용, 학습에 미사용)</span>
                            </p>""")
                            user_text = gr.Textbox(label="텍스트 붙여넣기", placeholder="회사명: 주식회사 OO\n대표자: 홍길동\n설립일: 2025.01.01", lines=3)
                            content_file = gr.File(label="또는 파일 업로드 (txt, xlsx, docx, csv)", file_types=[".txt", ".xlsx", ".xls", ".docx", ".csv", ".json", ".md"], elem_classes="file-area")
                            map_btn = gr.Button("AI 자동 매핑", variant="primary", elem_classes="btn-dark", size="lg")
                            status_map = gr.HTML(visible=False)

                        step_result = gr.Group(visible=False, elem_classes="sec")
                        with step_result:
                            gr.HTML('<p class="sec-title">매핑 결과</p><p class="sec-desc">틀린 부분은 직접 수정할 수 있습니다.</p>')
                            edit_table = gr.Dataframe(headers=["원본 내용", "변경할 내용"], datatype=["str", "str"], column_count=(2, "fixed"), row_count=(1, "dynamic"), interactive=True, wrap=True, elem_classes="tbl")
                            gen_btn = gr.Button("문서 만들기", variant="primary", elem_classes="btn-dark", size="lg")
                            status_gen = gr.HTML(visible=False)
                            result_file = gr.File(label="완성된 파일", elem_classes="result-dl", visible=False)

                    # ── 대량 생성 ──
                    with gr.Tab("대량 생성"):
                        with gr.Group(elem_classes="sec"):
                            gr.HTML("""<p class="sec-desc">
                                같은 양식으로 여러 사람 문서를 한번에 만듭니다.<br>
                                <span style="color:#666;">예: 위촉장 100명분, 계약서 50건, 수료증 200장</span>
                            </p>
                            <div style="background:#f8f9fa; border-radius:8px; padding:10px 14px; margin-bottom:12px; font-size:12px; line-height:1.6; color:#555;">
                                <strong style="color:#333;">엑셀 작성법</strong>
                                <table style="width:100%; border-collapse:collapse; margin-top:4px; font-size:11px;">
                                    <tr style="background:#eee;"><td style="padding:3px 8px; border:1px solid #ddd;">홍길동</td><td style="padding:3px 8px; border:1px solid #ddd;">서울시 강남구</td><td style="padding:3px 8px; border:1px solid #ddd;">팀장</td></tr>
                                    <tr><td style="padding:3px 8px; border:1px solid #ddd;">김철수</td><td style="padding:3px 8px; border:1px solid #ddd;">부산시 해운대구</td><td style="padding:3px 8px; border:1px solid #ddd;">대리</td></tr>
                                </table>
                                <span style="color:#999; font-size:10px;">1행: 양식에 있는 바꿀 텍스트 / 2행부터: 새로 넣을 내용</span>
                            </div>""")
                            batch_excel = gr.File(label="엑셀 데이터 (.xlsx)", file_types=[".xlsx", ".xls"], elem_classes="file-area")
                            batch_btn = gr.Button("대량 생성", variant="primary", elem_classes="btn-dark", size="lg")
                            batch_status = gr.HTML(visible=False)
                            batch_result = gr.File(label="생성된 파일 (ZIP)", visible=False)

                    # ── 내용 뽑기 ──
                    with gr.Tab("내용 뽑기"):
                        with gr.Group(elem_classes="sec"):
                            gr.HTML("""<p class="sec-desc">
                                한글 문서 안의 텍스트를 엑셀로 뽑아줍니다.<br>
                                <span style="color:#666;">예: 접수된 신청서 50건을 엑셀 하나로 정리</span>
                            </p>""")
                            ext_files = gr.File(label="HWPX 파일 (여러 개 가능)", file_types=[".hwpx"], file_count="multiple", elem_classes="file-area")
                            ext_btn = gr.Button("추출하기", variant="primary", elem_classes="btn-dark", size="lg")
                            ext_status = gr.HTML(visible=False)
                            ext_result = gr.File(label="추출 결과 (Excel)", visible=False)

                    # ── 정기 문서 ──
                    with gr.Tab("정기 문서"):
                        with gr.Group(elem_classes="sec"):
                            gr.HTML("""<p class="sec-desc">
                                같은 양식에서 날짜만 바꿔서 여러 달치를 한번에 만듭니다.<br>
                                <span style="color:#666;">예: 1월~12월 월간보고서 12개를 한번에 생성</span>
                            </p>""")
                            per_date_text = gr.Textbox(label="문서에서 바꿀 날짜 (그대로 입력)", placeholder="예: 2025.08.03")
                            with gr.Row():
                                per_start = gr.Textbox(label="시작일", placeholder="2026-01-01")
                                per_end = gr.Textbox(label="종료일", placeholder="2026-12-01")
                            with gr.Row():
                                per_interval = gr.Radio(["monthly", "weekly"], label="간격", value="monthly", info="매월 / 매주")
                                per_format = gr.Textbox(label="날짜 형식", value="%Y.%m.%d", info="%Y.%m.%d = 2026.01.01")
                            per_btn = gr.Button("정기 문서 생성", variant="primary", elem_classes="btn-dark", size="lg")
                            per_status = gr.HTML(visible=False)
                            per_result = gr.File(label="생성된 파일 (ZIP)", visible=False)

                    # ── 도장 삽입 ──
                    with gr.Tab("도장 삽입"):
                        with gr.Group(elem_classes="sec"):
                            gr.HTML("""<p class="sec-desc">
                                문서에서 "(인)" 글자를 찾아 도장 이미지로 바꿔줍니다.<br>
                                <span style="color:#666;">예: 계약서의 (인) 자리에 직인 이미지 삽입</span>
                            </p>""")
                            stm_img = gr.File(label="도장/서명 이미지 (PNG, JPG)", file_types=[".png", ".jpg", ".jpeg", ".gif", ".bmp"], elem_classes="file-area")
                            stm_target = gr.Textbox(label="바꿀 글자", value="(인)", info="문서에서 이 글자를 찾아 도장으로 바꿉니다")
                            stm_btn = gr.Button("도장 삽입", variant="primary", elem_classes="btn-dark", size="lg")
                            stm_status = gr.HTML(visible=False)
                            stm_result = gr.File(label="완성된 파일", visible=False)

                    # ── 문서 합치기 ──
                    with gr.Tab("문서 합치기"):
                        with gr.Group(elem_classes="sec"):
                            gr.HTML("""<p class="sec-desc">
                                여러 한글 파일을 하나의 문서로 합쳐줍니다.<br>
                                <span style="color:#666;">예: 팀원 5명의 보고서를 하나로 합본</span>
                            </p>""")
                            mrg_files = gr.File(label="HWPX 파일들 (2개 이상)", file_types=[".hwpx"], file_count="multiple", elem_classes="file-area")
                            mrg_btn = gr.Button("합치기", variant="primary", elem_classes="btn-dark", size="lg")
                            mrg_status = gr.HTML(visible=False)
                            mrg_result = gr.File(label="합쳐진 파일", visible=False)

        # ── 이벤트 핸들러 ──
        def on_analyze(file, progress=gr.Progress()):
            info, texts, path, _, _ = analyze(file, progress)
            return gr.update(value=info, visible=True), path, texts

        def on_map(path, texts, text, cfile, progress=gr.Progress()):
            info, table, _ = do_mapping(path, texts, text, cfile, progress)
            return gr.update(value=info, visible=True), table, gr.update(visible=True)

        def on_gen(path, table, progress=gr.Progress()):
            out, info = do_generate(path, table, progress)
            return out, gr.update(value=info, visible=True), gr.update(visible=True)

        def on_batch(path, excel, progress=gr.Progress()):
            if not path:
                raise gr.Error("먼저 왼쪽에서 양식 파일을 분석해주세요.")
            if not excel:
                raise gr.Error("엑셀 파일을 업로드해주세요.")
            ep = excel.name if hasattr(excel, "name") else str(excel)
            progress(0.3, desc="대량 생성 중...")
            zp, cnt, err = batch_generate(path, ep)
            if err:
                raise gr.Error(err)
            progress(1.0, desc="완료!")
            return zp, gr.update(value=_msg(f"{cnt}개 문서가 생성되었습니다.", "final"), visible=True), gr.update(visible=True)

        def on_extract(files, progress=gr.Progress()):
            if not files:
                raise gr.Error("파일을 업로드해주세요.")
            paths = [f.name if hasattr(f, "name") else str(f) for f in files]
            progress(0.3, desc="텍스트 추출 중...")
            ep, cnt, err = extract_to_excel(paths)
            if err:
                raise gr.Error(err)
            progress(1.0, desc="완료!")
            return ep, gr.update(value=_msg(f"{cnt}개 텍스트를 추출했습니다.", "final"), visible=True), gr.update(visible=True)

        def on_periodic(path, date_text, start, end, interval, fmt, progress=gr.Progress()):
            if not path:
                raise gr.Error("먼저 왼쪽에서 양식 파일을 분석해주세요.")
            if not date_text or not start or not end:
                raise gr.Error("날짜 텍스트, 시작일, 종료일 모두 필요합니다.")
            try:
                sd = datetime.strptime(start.strip(), "%Y-%m-%d")
                ed = datetime.strptime(end.strip(), "%Y-%m-%d")
            except ValueError:
                raise gr.Error("날짜 형식: YYYY-MM-DD (예: 2026-01-01)")
            progress(0.3, desc="정기 문서 생성 중...")
            zp, cnt, err = generate_periodic(path, date_text.strip(), sd, ed, interval, fmt.strip())
            if err:
                raise gr.Error(err)
            progress(1.0, desc="완료!")
            return zp, gr.update(value=_msg(f"{cnt}개 문서가 생성되었습니다.", "final"), visible=True), gr.update(visible=True)

        def on_stamp(path, img, target, progress=gr.Progress()):
            if not path:
                raise gr.Error("먼저 왼쪽에서 양식 파일을 분석해주세요.")
            if not img:
                raise gr.Error("도장 이미지를 업로드해주세요.")
            ip = img.name if hasattr(img, "name") else str(img)
            progress(0.3, desc="도장 삽입 중...")
            out, err = insert_stamp(path, ip, target.strip() if target else "(인)")
            if err:
                raise gr.Error(err)
            progress(1.0, desc="완료!")
            return out, gr.update(value=_msg("도장이 삽입되었습니다.", "final"), visible=True), gr.update(visible=True)

        def on_merge(files, progress=gr.Progress()):
            if not files or len(files) < 2:
                raise gr.Error("최소 2개 파일이 필요합니다.")
            paths = [f.name if hasattr(f, "name") else str(f) for f in files]
            progress(0.3, desc="문서 병합 중...")
            out, cnt, err = merge_documents(paths)
            if err:
                raise gr.Error(err)
            progress(1.0, desc="완료!")
            return out, gr.update(value=_msg(f"{cnt}개 문서를 하나로 합쳤습니다.", "final"), visible=True), gr.update(visible=True)

        analyze_btn.click(on_analyze, [file_input], [status_common, form_path, form_texts])
        map_btn.click(on_map, [form_path, form_texts, user_text, content_file], [status_map, edit_table, step_result])
        gen_btn.click(on_gen, [form_path, edit_table], [result_file, status_gen, result_file])
        batch_btn.click(on_batch, [form_path, batch_excel], [batch_result, batch_status, batch_result])
        ext_btn.click(on_extract, [ext_files], [ext_result, ext_status, ext_result])
        per_btn.click(on_periodic, [form_path, per_date_text, per_start, per_end, per_interval, per_format], [per_result, per_status, per_result])
        stm_btn.click(on_stamp, [form_path, stm_img, stm_target], [stm_result, stm_status, stm_result])
        mrg_btn.click(on_merge, [mrg_files], [mrg_result, mrg_status, mrg_result])

        # ── 푸터 ──
        gr.HTML("""
        <div class="app-foot">
            <div style="margin-bottom:12px;">원본 양식의 표, 이미지, 서식이 그대로 유지됩니다.</div>
            <details style="text-align:left; max-width:520px; margin:0 auto; cursor:pointer;">
                <summary style="font-weight:600; color:#555; font-size:12px; margin-bottom:8px;">데이터 처리 및 보안 안내</summary>
                <div style="font-size:11px; color:#777; line-height:1.7; padding:12px 16px; background:#f9f9f9; border-radius:8px; border:1px solid #eee;">
                    <p style="margin:0 0 8px;"><strong style="color:#333;">1. 양식 분석 / 대량 생성 / 추출 / 병합</strong><br>
                    모든 처리는 이 서버(로컬 PC)에서만 수행됩니다. 외부 서버로 전송되지 않습니다.</p>
                    <p style="margin:0 0 8px;"><strong style="color:#333;">2. AI 매핑 (문서 생성 탭)</strong><br>
                    양식 텍스트와 입력한 내용이 Google Gemini API(유료)로 전송됩니다.<br>
                    - Google은 유료 API 데이터를 모델 학습에 사용하지 않습니다.<br>
                    - 남용 감지 목적으로 55일간 로그 보관 후 자동 삭제됩니다.<br>
                    - <strong style="color:#c33;">단, 주민번호, 카드번호, 비밀번호 등 민감한 개인정보는 입력하지 마세요.</strong>
                    Google 공식 정책에서도 유료 서비스를 포함하여 민감/기밀 정보를 전송하지 않도록 안내하고 있습니다.
                    (<a href="https://ai.google.dev/gemini-api/docs/logs-policy?hl=ko" target="_blank" style="color:#4a7;">Google 공식 데이터 로깅 정책</a>)</p>
                    <p style="margin:0 0 8px;"><strong style="color:#333;">3. 파일 보관</strong><br>
                    업로드/생성된 파일은 서버의 임시 폴더에 저장되며, 서버 재시작 시 자동 삭제됩니다.</p>
                    <p style="margin:0;"><strong style="color:#333;">4. 네트워크</strong><br>
                    본 서비스는 HTTPS(TLS) 암호화 통신을 사용합니다.</p>
                </div>
            </details>
        </div>
        """)

    return app


if __name__ == "__main__":
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7862, theme=THEME, css=CSS)
