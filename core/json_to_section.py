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
    """템플릿 header.xml 복사 + 커스텀 스타일 추가"""
    src = os.path.join(SKILL_DIR, f"templates/{template}/header.xml")
    if not os.path.isfile(src):
        src = os.path.join(SKILL_DIR, "templates/report/header.xml")
    dst = os.path.join(output_dir, "header.xml")
    shutil.copy2(src, dst)

    with open(dst, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('itemCnt="6"', 'itemCnt="10"', 1)
    content = content.replace('itemCnt="7"', 'itemCnt="10"', 1)

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

    content = re_mod.sub(
        r'(<hh:borderFill id="6".*?faceColor=")[^"]*(")',
        r'\g<1>#E0E0E0\2',
        content, count=1, flags=re_mod.DOTALL
    )

    bf_789 = '''      <hh:borderFill id="7" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">
        <hh:slash type="NONE" Crooked="0" isCounter="0"/>
        <hh:backSlash type="NONE" Crooked="0" isCounter="0"/>
        <hh:leftBorder type="SOLID" width="0.4 mm" color="#000000"/>
        <hh:rightBorder type="SOLID" width="0.4 mm" color="#000000"/>
        <hh:topBorder type="SOLID" width="0.4 mm" color="#000000"/>
        <hh:bottomBorder type="SOLID" width="0.4 mm" color="#000000"/>
        <hh:diagonal type="SOLID" width="0.12 mm" color="#000000"/>
        <hc:fillBrush>
          <hc:winBrush faceColor="#E0E0E0" hatchColor="#999999" alpha="0"/>
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
          <hc:winBrush faceColor="#2B4C7E" hatchColor="#999999" alpha="0"/>
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

    with open(dst, 'w', encoding='utf-8') as f:
        f.write(content)
    return dst
