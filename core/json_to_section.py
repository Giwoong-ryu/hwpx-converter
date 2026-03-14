"""
JSON -> HWPX XML 변환 모듈
분석 구조 JSON -> section0.xml + header.xml 생성
"""
import json
import os
import re as re_mod
import shutil

from core.xml_utils import SKILL_DIR, next_id, esc, color_to_charpr, style_to_bf, gen_cell
from core.section_renderers import (
    render_title_area, render_inline_row, render_label_box,
    render_paragraph, render_table, render_section_header
)

# 템플릿별 시각 스타일 정의
# bf6: 중간 배경(일반 회색 셀), bf7: 헤더 배경(연한 색), bf8: 강조 배경(진한 색)
# bf7_border: 헤더 행 테두리 굵기
_TEMPLATE_STYLES = {
    "gonmun": {
        "bf6_color": "#C8C8C8",   # 일반 배경: 중회색 (관공서 스타일)
        "bf7_face":  "#D0D0D0",   # 헤더 배경: 연회색
        "bf7_border": "0.5 mm",   # 테두리: 굵게 (공문 스타일)
        "bf8_face":  "#404040",   # 강조 배경: 진회색 (컬러 없음)
    },
    "report": {
        "bf6_color": "#E0E0E0",
        "bf7_face":  "#D6DCE4",   # 헤더 배경: 파란 회색
        "bf7_border": "0.4 mm",
        "bf8_face":  "#2B4C7E",   # 강조 배경: 진한 파랑
    },
    "minutes": {
        "bf6_color": "#DAECD3",
        "bf7_face":  "#E2EFDA",   # 헤더 배경: 연한 초록
        "bf7_border": "0.3 mm",
        "bf8_face":  "#375623",   # 강조 배경: 진한 초록
    },
    "proposal": {
        "bf6_color": "#C5D9F1",
        "bf7_face":  "#BDD7EE",   # 헤더 배경: 연한 파랑
        "bf7_border": "0.4 mm",
        "bf8_face":  "#1F3864",   # 강조 배경: 진한 네이비
    },
}


def generate_section_xml(doc_structure, output_dir):
    """분석 결과 JSON -> section0.xml 생성"""
    W = 42520  # A4 본문 폭

    parts = []

    parts.append('''<?xml version='1.0' encoding='UTF-8'?>
<hs:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"
        xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"
        xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app"
        xmlns:hp10="http://www.hancom.co.kr/hwpml/2016/paragraph"
        xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core"
        xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head"
        xmlns:hhs="http://www.hancom.co.kr/hwpml/2011/history"
        xmlns:hm="http://www.hancom.co.kr/hwpml/2011/master-page"
        xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf"
        xmlns:dc="http://purl.org/dc/elements/1.1/"
        xmlns:opf="http://www.idpf.org/2007/opf/"
        xmlns:ooxmlchart="http://www.hancom.co.kr/hwpml/2016/ooxmlchart"
        xmlns:hwpunitchar="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar"
        xmlns:epub="http://www.idpf.org/2007/ops"
        xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0">''')

    parts.append(f'''  <hp:p id="{next_id()}" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
    <hp:run charPrIDRef="0">
      <hp:secPr id="" textDirection="HORIZONTAL" spaceColumns="1134" tabStop="8000" tabStopVal="4000" tabStopUnit="HWPUNIT" outlineShapeIDRef="1" memoShapeIDRef="0" textVerticalWidthHead="0" masterPageCnt="0">
        <hp:grid lineGrid="0" charGrid="0" wonggojiFormat="0"/>
        <hp:startNum pageStartsOn="BOTH" page="0" pic="0" tbl="0" equation="0"/>
        <hp:visibility hideFirstHeader="0" hideFirstFooter="0" hideFirstMasterPage="0" border="SHOW_ALL" fill="SHOW_ALL" hideFirstPageNum="0" hideFirstEmptyLine="0" showLineNumber="0"/>
        <hp:lineNumberShape restartType="0" countBy="0" distance="0" startNumber="0"/>
        <hp:pagePr landscape="WIDELY" width="59528" height="84186" gutterType="LEFT_ONLY">
          <hp:margin header="4252" footer="4252" gutter="0" left="8504" right="8504" top="5668" bottom="4252"/>
        </hp:pagePr>
        <hp:footNotePr>
          <hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/>
          <hp:noteLine length="-1" type="SOLID" width="0.12 mm" color="#000000"/>
          <hp:noteSpacing betweenNotes="283" belowLine="567" aboveLine="850"/>
          <hp:numbering type="CONTINUOUS" newNum="1"/>
          <hp:placement place="EACH_COLUMN" beneathText="0"/>
        </hp:footNotePr>
        <hp:endNotePr>
          <hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/>
          <hp:noteLine length="14692344" type="SOLID" width="0.12 mm" color="#000000"/>
          <hp:noteSpacing betweenNotes="0" belowLine="567" aboveLine="850"/>
          <hp:numbering type="CONTINUOUS" newNum="1"/>
          <hp:placement place="END_OF_DOCUMENT" beneathText="0"/>
        </hp:endNotePr>
        <hp:pageBorderFill type="BOTH" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER">
          <hp:offset left="1417" right="1417" top="1417" bottom="1417"/>
        </hp:pageBorderFill>
        <hp:pageBorderFill type="EVEN" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER">
          <hp:offset left="1417" right="1417" top="1417" bottom="1417"/>
        </hp:pageBorderFill>
        <hp:pageBorderFill type="ODD" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER">
          <hp:offset left="1417" right="1417" top="1417" bottom="1417"/>
        </hp:pageBorderFill>
      </hp:secPr>
      <hp:ctrl>
        <hp:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="1" sameSz="1" sameGap="0"/>
      </hp:ctrl>
    </hp:run>
    <hp:run charPrIDRef="0"><hp:t/></hp:run>
  </hp:p>''')

    sections = doc_structure.get("sections", [])
    for sec in sections:
        sec_type = sec.get("type", "paragraph")

        if sec_type == "title_area":
            render_title_area(parts, sec, W)
        elif sec_type == "inline_row":
            render_inline_row(parts, sec, W)
        elif sec_type == "label_box":
            render_label_box(parts, sec, W)
        elif sec_type == "paragraph":
            render_paragraph(parts, sec)
        elif sec_type == "table":
            render_table(parts, sec, W)
        elif sec_type == "section_header":
            render_section_header(parts, sec, W)

    parts.append("</hs:sec>")

    section_path = os.path.join(output_dir, "section0.xml")
    with open(section_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(parts))
    return section_path


def create_header(output_dir, template="report"):
    """템플릿 header.xml 복사 + 템플릿별 스타일 주입.

    어떤 템플릿이든 기존 borderFill 7/8/9를 제거한 뒤 템플릿 스타일로 교체한다.
    """
    src = os.path.join(SKILL_DIR, f"templates/{template}/header.xml")
    if not os.path.isfile(src):
        src = os.path.join(SKILL_DIR, "templates/report/header.xml")
    dst = os.path.join(output_dir, "header.xml")
    shutil.copy2(src, dst)

    with open(dst, 'r', encoding='utf-8') as f:
        content = f.read()

    s = _TEMPLATE_STYLES.get(template, _TEMPLATE_STYLES["report"])

    # --- borderFill 7/8/9 기존 정의 제거 (템플릿마다 이미 정의되어 있을 수 있음) ---
    bf_removed = 0
    for bf_id in (7, 8, 9):
        content, n = re_mod.subn(
            rf'\s*<!--[^<]*-->\s*<hh:borderFill id="{bf_id}"[\s>].*?</hh:borderFill>',
            '',
            content,
            count=1,
            flags=re_mod.DOTALL,
        )
        if n == 0:
            content, n = re_mod.subn(
                rf'\s*<hh:borderFill id="{bf_id}"[\s>].*?</hh:borderFill>',
                '',
                content,
                count=1,
                flags=re_mod.DOTALL,
            )
        bf_removed += n

    # borderFills itemCnt 정확히 업데이트 (제거분 빼고 3개 추가)
    def _update_bf_cnt(m):
        new_cnt = int(m.group(1)) - bf_removed + 3
        return f'<hh:borderFills itemCnt="{new_cnt}"'
    content = re_mod.sub(r'<hh:borderFills itemCnt="(\d+)"', _update_bf_cnt, content, count=1)

    # --- borderFill 6 배경색 교체 ---
    content = re_mod.sub(
        r'(<hh:borderFill id="6".*?faceColor=")[^"]*(")',
        r'\g<1>' + s["bf6_color"] + r'\2',
        content, count=1, flags=re_mod.DOTALL,
    )

    # --- 템플릿별 borderFill 7/8/9 주입 ---
    bw = s["bf7_border"]
    bf7 = s["bf7_face"]
    bf8 = s["bf8_face"]

    bf_789 = f'''      <hh:borderFill id="7" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">
        <hh:slash type="NONE" Crooked="0" isCounter="0"/>
        <hh:backSlash type="NONE" Crooked="0" isCounter="0"/>
        <hh:leftBorder type="SOLID" width="{bw}" color="#000000"/>
        <hh:rightBorder type="SOLID" width="{bw}" color="#000000"/>
        <hh:topBorder type="SOLID" width="{bw}" color="#000000"/>
        <hh:bottomBorder type="SOLID" width="{bw}" color="#000000"/>
        <hh:diagonal type="SOLID" width="0.12 mm" color="#000000"/>
        <hc:fillBrush>
          <hc:winBrush faceColor="{bf7}" hatchColor="#999999" alpha="0"/>
        </hc:fillBrush>
      </hh:borderFill>
      <hh:borderFill id="8" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">
        <hh:slash type="NONE" Crooked="0" isCounter="0"/>
        <hh:backSlash type="NONE" Crooked="0" isCounter="0"/>
        <hh:leftBorder type="NONE" width="0.12 mm" color="#000000"/>
        <hh:rightBorder type="NONE" width="0.12 mm" color="#000000"/>
        <hh:topBorder type="NONE" width="0.12 mm" color="#000000"/>
        <hh:bottomBorder type="NONE" width="0.12 mm" color="#000000"/>
        <hh:diagonal type="SOLID" width="0.12 mm" color="#000000"/>
        <hc:fillBrush>
          <hc:winBrush faceColor="{bf8}" hatchColor="#999999" alpha="0"/>
        </hc:fillBrush>
      </hh:borderFill>
      <hh:borderFill id="9" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">
        <hh:slash type="NONE" Crooked="0" isCounter="0"/>
        <hh:backSlash type="NONE" Crooked="0" isCounter="0"/>
        <hh:leftBorder type="NONE" width="0.12 mm" color="#000000"/>
        <hh:rightBorder type="NONE" width="0.12 mm" color="#000000"/>
        <hh:topBorder type="NONE" width="0.12 mm" color="#000000"/>
        <hh:bottomBorder type="NONE" width="0.12 mm" color="#000000"/>
        <hh:diagonal type="NONE" width="0.12 mm" color="#000000"/>
      </hh:borderFill>
    </hh:borderFills>'''
    content = content.replace('</hh:borderFills>', bf_789, 1)

    # --- charPr 16 (흰색 텍스트) 추가 - 중복 방지 ---
    if 'id="16"' not in content:
        def _update_char_cnt(m):
            return f'<hh:charProperties itemCnt="{int(m.group(1)) + 1}"'
        content = re_mod.sub(
            r'<hh:charProperties itemCnt="(\d+)"', _update_char_cnt, content, count=1,
        )
        charpr_16 = '''      <hh:charPr id="16" height="1200" textColor="#FFFFFF" shadeColor="none" useFontSpace="0" useKerning="0" symMark="NONE" borderFillIDRef="2">
        <hh:fontRef hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>
        <hh:ratio hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>
        <hh:spacing hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>
        <hh:relSz hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>
        <hh:offset hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>
        <hh:bold/>
        <hh:underline type="NONE" shape="SOLID" color="#000000"/>
        <hh:strikeout shape="NONE" color="#000000"/>
        <hh:outline type="NONE"/>
        <hh:shadow type="NONE" color="#C0C0C0" offsetX="10" offsetY="10"/>
      </hh:charPr>
    </hh:charProperties>'''
        content = content.replace('</hh:charProperties>', charpr_16, 1)

    with open(dst, 'w', encoding='utf-8') as f:
        f.write(content)
    return dst
