"""
HWPX 섹션 렌더링 함수 모듈
각 섹션 타입(title_area, inline_row, label_box, paragraph, table, section_header)의
XML 렌더링을 담당한다.

json_to_section.py에서 import하여 사용.
"""
from core.xml_utils import next_id, esc, color_to_charpr, style_to_bf, gen_cell


def render_title_area(parts, sec, W):
    """제목부 영역 렌더링"""
    title_rows = sec.get("rows", [])
    row_cnt = len(title_rows)
    BF_NONE = 9

    has_inline = any(r.get("type") == "inline_row" for r in title_rows)
    col_cnt = 2 if has_inline else 1

    parts.append(f'''  <hp:p id="{next_id()}" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
    <hp:run charPrIDRef="0">
      <hp:tbl id="{next_id()}" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM"
              textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL"
              repeatHeader="0" rowCnt="{row_cnt}" colCnt="{col_cnt}" cellSpacing="0"
              borderFillIDRef="{BF_NONE}" noAdjust="0">
        <hp:sz width="{W}" widthRelTo="ABSOLUTE" height="{1600 * row_cnt}" heightRelTo="ABSOLUTE" protect="0"/>
        <hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0"
                holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP"
                horzAlign="LEFT" vertOffset="0" horzOffset="0"/>
        <hp:outMargin left="0" right="0" top="0" bottom="0"/>
        <hp:inMargin left="0" right="0" top="0" bottom="0"/>''')

    for ri, trow in enumerate(title_rows):
        rtype = trow.get("type", "paragraph")

        if rtype == "inline_row":
            elements = trow.get("elements", [])
            parts.append("      <hp:tr>")
            for elem in elements:
                etype = elem.get("type", "text")
                wr = elem.get("width_ratio", 50)
                cw = int(W * wr / 100)

                if etype == "label_box":
                    lb_text = elem.get("text", "")
                    lb_bg = elem.get("bg_color", "#2B4C7E")
                    bf = style_to_bf(lb_bg)
                    cpr = 16 if elem.get("text_color", "").upper() == "#FFFFFF" else 9
                    parts.append(f'''        <hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="1" borderFillIDRef="{bf}">
          <hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER"
                     linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0"
                     hasTextRef="0" hasNumRef="0">
            <hp:p paraPrIDRef="22" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0" id="{next_id()}">
              <hp:run charPrIDRef="{cpr}"><hp:t>{esc(lb_text)}</hp:t></hp:run>
            </hp:p>
          </hp:subList>
          <hp:cellAddr colAddr="0" rowAddr="{ri}"/>
          <hp:cellSpan colSpan="1" rowSpan="1"/>
          <hp:cellSz width="{cw}" height="1400"/>
          <hp:cellMargin left="142" right="142" top="71" bottom="71"/>
        </hp:tc>''')
                else:
                    t_text = elem.get("content", "")
                    t_style = elem.get("style", {})
                    t_bold = t_style.get("bold", False)
                    t_size = t_style.get("font_size_pt", 10)
                    t_color = t_style.get("text_color", "#000000")
                    cpr = color_to_charpr(t_color, t_bold, t_size)
                    parts.append(f'''        <hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="1" borderFillIDRef="{BF_NONE}">
          <hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER"
                     linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0"
                     hasTextRef="0" hasNumRef="0">
            <hp:p paraPrIDRef="22" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0" id="{next_id()}">
              <hp:run charPrIDRef="{cpr}"><hp:t>{esc(t_text)}</hp:t></hp:run>
            </hp:p>
          </hp:subList>
          <hp:cellAddr colAddr="1" rowAddr="{ri}"/>
          <hp:cellSpan colSpan="1" rowSpan="1"/>
          <hp:cellSz width="{cw}" height="1400"/>
          <hp:cellMargin left="142" right="142" top="71" bottom="71"/>
        </hp:tc>''')
            parts.append("      </hp:tr>")

        else:
            content = trow.get("content", "")
            align = trow.get("align", "CENTER")
            style = trow.get("style", {})
            bold = style.get("bold", False)
            size = style.get("font_size_pt", 10)
            color = style.get("text_color", "#000000")
            cpr = color_to_charpr(color, bold, size)
            para_map = {"CENTER": 21, "LEFT": 22, "RIGHT": 23}
            ppr = para_map.get(align, 21)
            row_h = max(1200, int(size * 90))

            parts.append(f'''      <hp:tr>
        <hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="1" borderFillIDRef="{BF_NONE}">
          <hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER"
                     linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0"
                     hasTextRef="0" hasNumRef="0">
            <hp:p paraPrIDRef="{ppr}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0" id="{next_id()}">
              <hp:run charPrIDRef="{cpr}"><hp:t>{esc(content)}</hp:t></hp:run>
            </hp:p>
          </hp:subList>
          <hp:cellAddr colAddr="0" rowAddr="{ri}"/>
          <hp:cellSpan colSpan="{col_cnt}" rowSpan="1"/>
          <hp:cellSz width="{W}" height="{row_h}"/>
          <hp:cellMargin left="142" right="142" top="71" bottom="71"/>
        </hp:tc>
      </hp:tr>''')

    parts.append('''      </hp:tbl>
    </hp:run>
  </hp:p>''')


def render_inline_row(parts, sec, W):
    """인라인 행 렌더링"""
    elements = sec.get("elements", [])
    p_parts = []
    p_parts.append(f'  <hp:p id="{next_id()}" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">')

    for elem in elements:
        etype = elem.get("type", "text")

        if etype == "label_box":
            lb_text = elem.get("text", "")
            lb_bg = elem.get("bg_color", "#2B4C7E")
            bf = style_to_bf(lb_bg)
            char_pr = 16 if elem.get("text_color", "").upper() == "#FFFFFF" else 9
            wr = elem.get("width_ratio", 15)
            box_w = int(W * wr / 100)
            p_parts.append(f'''    <hp:run charPrIDRef="0">
      <hp:tbl id="{next_id()}" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM"
              textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL"
              repeatHeader="0" rowCnt="1" colCnt="1" cellSpacing="0"
              borderFillIDRef="{bf}" noAdjust="0">
        <hp:sz width="{box_w}" widthRelTo="ABSOLUTE" height="1200" heightRelTo="ABSOLUTE" protect="0"/>
        <hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0"
                holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP"
                horzAlign="LEFT" vertOffset="0" horzOffset="0"/>
        <hp:outMargin left="0" right="0" top="0" bottom="0"/>
        <hp:inMargin left="0" right="0" top="0" bottom="0"/>
      <hp:tr>
        <hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="1" borderFillIDRef="{bf}">
          <hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER"
                     linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0"
                     hasTextRef="0" hasNumRef="0">
            <hp:p paraPrIDRef="21" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0" id="{next_id()}">
              <hp:run charPrIDRef="{char_pr}"><hp:t>{esc(lb_text)}</hp:t></hp:run>
            </hp:p>
          </hp:subList>
          <hp:cellAddr colAddr="0" rowAddr="0"/>
          <hp:cellSpan colSpan="1" rowSpan="1"/>
          <hp:cellSz width="{box_w}" height="1200"/>
          <hp:cellMargin left="142" right="142" top="71" bottom="71"/>
        </hp:tc>
      </hp:tr>
      </hp:tbl>
    </hp:run>''')

        elif etype == "text":
            t_text = elem.get("content", "")
            t_style = elem.get("style", {})
            t_bold = t_style.get("bold", False)
            t_size = t_style.get("font_size_pt", 10)
            t_color = t_style.get("text_color", "#000000")
            t_char_pr = color_to_charpr(t_color, t_bold, t_size)
            p_parts.append(f'    <hp:run charPrIDRef="{t_char_pr}"><hp:t> {esc(t_text)}</hp:t></hp:run>')

    p_parts.append('  </hp:p>')
    parts.append('\n'.join(p_parts))


def render_label_box(parts, sec, W):
    """단독 라벨박스 렌더링"""
    lb_text = sec.get("text", "")
    lb_bg = sec.get("bg_color", "#2B4C7E")
    bf = style_to_bf(lb_bg)
    char_pr = 16 if sec.get("text_color", "").upper() == "#FFFFFF" else 9
    box_w = min(6000, W // 4)
    parts.append(f'''  <hp:p id="{next_id()}" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
    <hp:run charPrIDRef="0">
      <hp:tbl id="{next_id()}" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM"
              textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL"
              repeatHeader="0" rowCnt="1" colCnt="1" cellSpacing="0"
              borderFillIDRef="{bf}" noAdjust="0">
        <hp:sz width="{box_w}" widthRelTo="ABSOLUTE" height="1200" heightRelTo="ABSOLUTE" protect="0"/>
        <hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0"
                holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP"
                horzAlign="LEFT" vertOffset="0" horzOffset="0"/>
        <hp:outMargin left="0" right="0" top="0" bottom="0"/>
        <hp:inMargin left="0" right="0" top="0" bottom="0"/>
      <hp:tr>
        <hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="1" borderFillIDRef="{bf}">
          <hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER"
                     linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0"
                     hasTextRef="0" hasNumRef="0">
            <hp:p paraPrIDRef="21" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0" id="{next_id()}">
              <hp:run charPrIDRef="{char_pr}"><hp:t>{esc(lb_text)}</hp:t></hp:run>
            </hp:p>
          </hp:subList>
          <hp:cellAddr colAddr="0" rowAddr="0"/>
          <hp:cellSpan colSpan="1" rowSpan="1"/>
          <hp:cellSz width="{box_w}" height="1200"/>
          <hp:cellMargin left="142" right="142" top="71" bottom="71"/>
        </hp:tc>
      </hp:tr>
      </hp:tbl>
    </hp:run>
  </hp:p>''')


def render_paragraph(parts, sec):
    """문단 렌더링"""
    text = sec.get("content", "")
    lines = sec.get("lines", [])
    style = sec.get("style", {})
    align = sec.get("align", "LEFT")
    bold = style.get("bold", False)
    size = style.get("font_size_pt", 10)
    color = style.get("text_color", "#000000")

    char_pr = color_to_charpr(color, bold, size)
    para_map = {"CENTER": 20, "LEFT": 0, "RIGHT": 23}
    para_pr = para_map.get(align, 0)

    if lines and len(lines) > 1:
        for line in lines:
            parts.append(f'''  <hp:p id="{next_id()}" paraPrIDRef="{para_pr}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
    <hp:run charPrIDRef="{char_pr}"><hp:t>{esc(line)}</hp:t></hp:run>
  </hp:p>''')
    elif not text:
        parts.append(f'''  <hp:p id="{next_id()}" paraPrIDRef="{para_pr}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
    <hp:run charPrIDRef="0"><hp:t/></hp:run>
  </hp:p>''')
    else:
        parts.append(f'''  <hp:p id="{next_id()}" paraPrIDRef="{para_pr}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
    <hp:run charPrIDRef="{char_pr}"><hp:t>{esc(text)}</hp:t></hp:run>
  </hp:p>''')


def render_table(parts, sec, W):
    """테이블 렌더링"""
    tbl = sec.get("table", {})
    row_cnt = tbl.get("rows", 1)
    col_cnt = tbl.get("cols", 1)
    cells = tbl.get("cells", [])

    # 빈 테이블 가드: 행/열/셀이 없으면 빈 문단으로 폴백
    if row_cnt < 1 or col_cnt < 1 or not cells:
        parts.append(f'''  <hp:p id="{next_id()}" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
    <hp:run charPrIDRef="0"><hp:t/></hp:run>
  </hp:p>''')
        return

    ratios = tbl.get("col_widths_ratio", [100 // col_cnt] * col_cnt)

    total_ratio = sum(ratios)
    col_widths = [int(W * r / total_ratio) for r in ratios]
    diff = W - sum(col_widths)
    if diff != 0:
        col_widths[-1] += diff

    height = 1800 * row_cnt

    parts.append(f'''  <hp:p id="{next_id()}" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
    <hp:run charPrIDRef="0">
      <hp:tbl id="{next_id()}" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM"
              textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL"
              repeatHeader="0" rowCnt="{row_cnt}" colCnt="{col_cnt}" cellSpacing="0"
              borderFillIDRef="3" noAdjust="0">
        <hp:sz width="{W}" widthRelTo="ABSOLUTE" height="{height}" heightRelTo="ABSOLUTE" protect="0"/>
        <hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0"
                holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP"
                horzAlign="LEFT" vertOffset="0" horzOffset="0"/>
        <hp:outMargin left="0" right="0" top="0" bottom="0"/>
        <hp:inMargin left="0" right="0" top="0" bottom="0"/>''')

    rows_dict = {}
    for c in cells:
        r = c.get("row", 0)
        if r not in rows_dict:
            rows_dict[r] = []
        rows_dict[r].append(c)

    covered_by_rowspan = {}
    for c in cells:
        rs = c.get("rowspan", 1)
        cs = c.get("colspan", 1)
        if rs > 1:
            for dr in range(1, rs):
                rr = c.get("row", 0) + dr
                if rr not in covered_by_rowspan:
                    covered_by_rowspan[rr] = set()
                for dc in range(cs):
                    covered_by_rowspan[rr].add(c.get("col", 0) + dc)

    for r in range(row_cnt):
        parts.append("      <hp:tr>")
        row_cells = rows_dict.get(r, [])
        seen_cols = {}
        for cell_data in row_cells:
            col_key = cell_data.get("col", 0)
            seen_cols[col_key] = cell_data
        row_cells = sorted(seen_cols.values(), key=lambda x: x.get("col", 0))

        covered = set()
        if r in covered_by_rowspan:
            covered = set(covered_by_rowspan[r])  # 복사! 원본 오염 방지
        for cell_data in row_cells:
            cc = cell_data.get("col", 0)
            cs = cell_data.get("colspan", 1)
            for dc in range(cs):
                covered.add(cc + dc)

        final_cells = list(row_cells)
        for ci in range(col_cnt):
            if ci not in covered:
                final_cells.append({
                    "row": r, "col": ci, "text": "",
                    "style": {"align": "CENTER"}
                })
                covered.add(ci)
        final_cells.sort(key=lambda x: x.get("col", 0))

        rowspan_covered = covered_by_rowspan.get(r, set())
        for cell_data in final_cells:
            cc = cell_data.get("col", 0)
            if cc in rowspan_covered:
                continue
            if (cell_data.get("row", 0) == 0
                and cell_data.get("colspan", 1) >= col_cnt
                and cell_data.get("style", {}).get("bold")):
                cell_data.setdefault("style", {})["is_header"] = True
            parts.append(gen_cell(cell_data, W, col_widths))
        parts.append("      </hp:tr>")

    parts.append('''      </hp:tbl>
    </hp:run>
  </hp:p>''')


def render_section_header(parts, sec, W):
    """섹션 헤더 렌더링"""
    header_text = sec.get("header_text", "")
    bg = sec.get("header_bg_color", "#D6DCE4")
    bf = style_to_bf(bg)

    parts.append(f'''  <hp:p id="{next_id()}" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
    <hp:run charPrIDRef="0">
      <hp:tbl id="{next_id()}" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM"
              textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL"
              repeatHeader="0" rowCnt="1" colCnt="1" cellSpacing="0"
              borderFillIDRef="{bf}" noAdjust="0">
        <hp:sz width="{W}" widthRelTo="ABSOLUTE" height="1400" heightRelTo="ABSOLUTE" protect="0"/>
        <hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0"
                holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP"
                horzAlign="LEFT" vertOffset="0" horzOffset="0"/>
        <hp:outMargin left="0" right="0" top="0" bottom="0"/>
        <hp:inMargin left="0" right="0" top="0" bottom="0"/>
      <hp:tr>
        <hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="1" borderFillIDRef="{bf}">
          <hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER"
                     linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0"
                     hasTextRef="0" hasNumRef="0">
            <hp:p paraPrIDRef="21" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0" id="{next_id()}">
              <hp:run charPrIDRef="9"><hp:t>{esc(header_text)}</hp:t></hp:run>
            </hp:p>
          </hp:subList>
          <hp:cellAddr colAddr="0" rowAddr="0"/>
          <hp:cellSpan colSpan="1" rowSpan="1"/>
          <hp:cellSz width="{W}" height="1400"/>
          <hp:cellMargin left="142" right="142" top="71" bottom="71"/>
        </hp:tc>
      </hp:tr>
      </hp:tbl>
    </hp:run>
  </hp:p>''')
