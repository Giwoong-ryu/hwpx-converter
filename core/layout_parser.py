"""
레이아웃 파서 모듈
Gemini Vision 좌표 데이터 → HWP 구조 JSON 변환

핵심 알고리즘:
- BFS 기반 테이블 클러스터링 (border_connects_to 그래프)
- Y좌표 행 그룹핑 (Y_TOLERANCE 기반)
- 공간적 포함(Spatial Containment) 감지
- colspan/rowspan 자동 계산

사용법 (단독 실행):
  python layout_parser.py layout.json [-o structure.json]
"""
import json
import os
import sys


Y_TOLERANCE_DEFAULT = 5.0  # mm - Y좌표 행 그룹핑 기본 오차


def _calc_y_tolerance(elements):
    """폰트 크기 비례 Y_TOLERANCE 동적 계산.

    큰 폰트(제목)는 행 간격이 넓어 고정 5mm로는 같은 행을 분리할 수 있고,
    작은 폰트(각주)는 행 간격이 좁아 다른 행을 병합할 수 있다.
    """
    sizes = [e.get("style", {}).get("font_size_pt", 10) for e in elements]
    if not sizes:
        return Y_TOLERANCE_DEFAULT
    avg = sum(sizes) / len(sizes)
    return max(3.0, avg * 0.4)


def layout_to_structure(layout):
    """Pass 2: 레이아웃 좌표 데이터 → HWP 구조 (코드 알고리즘)"""
    elements = layout.get("elements", [])
    if not elements:
        return {"document": {"title": "문서", "page_width_hu": 42520}, "sections": []}

    Y_TOLERANCE = _calc_y_tolerance(elements)

    page_w = layout.get("page", {}).get("width_mm", 210)
    elem_map = {e["id"]: e for e in elements}

    # --- 1) border 그래프로 테이블 클러스터 찾기 (BFS) ---
    visited = set()
    table_clusters = []

    def bfs(start_id):
        cluster = set()
        queue = [start_id]
        while queue:
            eid = queue.pop(0)
            if eid in cluster:
                continue
            cluster.add(eid)
            e = elem_map.get(eid, {})
            for nid in e.get("border_connects_to", []):
                if nid not in cluster and nid in elem_map:
                    queue.append(nid)
        return cluster

    for e in elements:
        if e["id"] not in visited and e.get("has_border") and e.get("border_connects_to"):
            cluster = bfs(e["id"])
            visited |= cluster
            table_clusters.append(cluster)

    # 클러스터에 속하지 않은 has_border 요소
    bordered_not_clustered = set()
    for e in elements:
        if e["id"] not in visited and e.get("has_border") and not e.get("border_connects_to"):
            bordered_not_clustered.add(e["id"])

    # --- 2) 테이블이 아닌 요소 ---
    table_ids = visited
    non_table = [e for e in elements if e["id"] not in table_ids]

    # --- 3) non_table 요소를 Y좌표로 행 그룹핑 ---
    y_rows = []
    if non_table:
        non_table.sort(key=lambda e: (e["bbox"]["y"], e["bbox"]["x"]))
        current_row = [non_table[0]]
        for e in non_table[1:]:
            if abs(e["bbox"]["y"] - current_row[0]["bbox"]["y"]) <= Y_TOLERANCE:
                current_row.append(e)
            else:
                y_rows.append(current_row)
                current_row = [e]
        y_rows.append(current_row)

    # 첫 번째 테이블 이전 = title_area, 이후 = 개별 섹션
    first_table_y = float('inf')
    for cluster in table_clusters:
        min_y = min(elem_map[eid]["bbox"]["y"] for eid in cluster)
        if min_y < first_table_y:
            first_table_y = min_y

    title_rows = []
    post_table_rows = []
    for row in y_rows:
        row_y = min(e["bbox"]["y"] for e in row)
        if row_y < first_table_y:
            title_rows.append(row)
        else:
            post_table_rows.append(row)

    def is_label_box(e):
        bg = (e.get("style", {}).get("bg_color") or "").upper()
        tc = (e.get("style", {}).get("text_color") or "").upper()
        return bg and bg not in ("#FFFFFF", "#F2F2F2", "") and tc == "#FFFFFF"

    def make_title_row(row_elems):
        total_w = sum(e["bbox"]["w"] for e in row_elems)
        if len(row_elems) >= 2:
            elements_out = []
            for e in sorted(row_elems, key=lambda x: x["bbox"]["x"]):
                wr = round(e["bbox"]["w"] / total_w * 100) if total_w else 50
                if is_label_box(e):
                    elements_out.append({
                        "type": "label_box", "text": e["text"],
                        "bg_color": e["style"].get("bg_color", "#2B4C7E"),
                        "text_color": e["style"].get("text_color", "#FFFFFF"),
                        "bold": e["style"].get("bold", True), "width_ratio": wr
                    })
                else:
                    elements_out.append({
                        "type": "text", "content": e["text"],
                        "style": {k: v for k, v in e["style"].items() if k != "bg_color" and k != "align"},
                        "width_ratio": wr
                    })
            return {"type": "inline_row", "elements": elements_out}
        else:
            e = row_elems[0]
            if is_label_box(e):
                return {"type": "inline_row", "elements": [{
                    "type": "label_box", "text": e["text"],
                    "bg_color": e["style"].get("bg_color", "#2B4C7E"),
                    "text_color": e["style"].get("text_color", "#FFFFFF"),
                    "bold": True, "width_ratio": 100
                }]}
            return {
                "type": "paragraph", "content": e["text"],
                "align": e["style"].get("align", "CENTER"),
                "style": {k: v for k, v in e["style"].items() if k != "align" and v is not None}
            }

    # --- 4) 테이블 클러스터 → table 구조 ---
    def cluster_to_table(cluster_ids):
        elems = sorted([elem_map[eid] for eid in cluster_ids],
                       key=lambda e: (e["bbox"]["y"], e["bbox"]["x"]))

        # Y좌표로 행 그룹핑
        rows = []
        current_y = None
        for e in elems:
            if current_y is None or abs(e["bbox"]["y"] - current_y) > Y_TOLERANCE:
                rows.append([])
                current_y = e["bbox"]["y"]
            rows[-1].append(e)

        # X좌표로 열 경계 추출
        all_x = sorted(set(round(e["bbox"]["x"], 0) for e in elems))
        col_boundaries = []
        for x in all_x:
            if not col_boundaries or x - col_boundaries[-1] > 5:
                col_boundaries.append(x)

        n_rows = len(rows)
        n_cols = max(len(col_boundaries), max(len(r) for r in rows))

        # 열 너비 비율 계산
        if len(col_boundaries) >= 2:
            total_span = col_boundaries[-1] + max(e["bbox"]["w"] for e in elems) - col_boundaries[0]
            col_widths = []
            for i, cb in enumerate(col_boundaries):
                if i < len(col_boundaries) - 1:
                    col_widths.append(col_boundaries[i + 1] - cb)
                else:
                    matching = [e["bbox"]["w"] for e in elems if abs(e["bbox"]["x"] - cb) < 8]
                    col_widths.append(max(matching) if matching else (col_widths[-1] if col_widths else 30))
            total_cw = sum(col_widths)
            col_ratios = [round(cw / total_cw * 100, 1) for cw in col_widths]
        else:
            col_ratios = [100]

        # 셀 생성
        cells = []
        for ri, row in enumerate(rows):
            row.sort(key=lambda e: e["bbox"]["x"])
            for e in row:
                ci = 0
                for j, cb in enumerate(col_boundaries):
                    if abs(e["bbox"]["x"] - cb) < 5:
                        ci = j
                        break
                    elif e["bbox"]["x"] < cb:
                        ci = max(0, j - 1)
                        break
                    ci = j

                # colspan 계산
                colspan = 1
                end_x = e["bbox"]["x"] + e["bbox"]["w"]
                for j in range(ci + 1, len(col_boundaries)):
                    if col_boundaries[j] < end_x - 2:
                        colspan += 1
                    else:
                        break

                # rowspan 계산
                rowspan = 1
                end_y = e["bbox"]["y"] + e["bbox"]["h"]
                for j in range(ri + 1, len(rows)):
                    if rows[j] and rows[j][0]["bbox"]["y"] < end_y - 2:
                        rowspan += 1
                    else:
                        break

                text = e.get("text", "")
                lines = text.split("\n") if "\n" in text else []
                style = {}
                if e["style"].get("bold"):
                    style["bold"] = True
                if e["style"].get("bg_color"):
                    style["bg_color"] = e["style"]["bg_color"]
                tc = e["style"].get("text_color", "#000000")
                if tc and tc.upper() != "#000000":
                    style["text_color"] = tc
                style["align"] = e["style"].get("align", "CENTER")
                if e["style"].get("font_size_pt", 10) != 10:
                    style["font_size_pt"] = e["style"]["font_size_pt"]

                cell = {"row": ri, "col": ci, "text": text, "style": style}
                if colspan > 1:
                    cell["colspan"] = colspan
                if rowspan > 1:
                    cell["rowspan"] = rowspan
                if lines:
                    cell["lines"] = lines
                cells.append(cell)

        return {
            "type": "table",
            "table": {
                "rows": n_rows, "cols": len(col_ratios),
                "col_widths_ratio": col_ratios, "cells": cells
            }
        }

    # --- 4.5) 공간적 포함(Spatial Containment) 감지 ---
    CONTAIN_MARGIN = 3  # mm
    contained_elems = {}
    contained_cluster_idx = {}

    for ci_main, main_cluster in enumerate(table_clusters):
        for eid in main_cluster:
            e = elem_map[eid]
            bb = e["bbox"]
            cell_area = bb["w"] * bb["h"]
            if cell_area < 200:
                continue

            for other in elements:
                if other["id"] in main_cluster or other["id"] in contained_elems:
                    continue
                ob = other["bbox"]
                if (ob["x"] >= bb["x"] - CONTAIN_MARGIN and
                    ob["y"] >= bb["y"] - CONTAIN_MARGIN and
                    ob["x"] + ob["w"] <= bb["x"] + bb["w"] + CONTAIN_MARGIN and
                    ob["y"] + ob["h"] <= bb["y"] + bb["h"] + CONTAIN_MARGIN):
                    contained_elems[other["id"]] = eid

            for ci_other, other_cluster in enumerate(table_clusters):
                if ci_other == ci_main or ci_other in contained_cluster_idx:
                    continue
                all_inside = all(
                    elem_map[oid]["bbox"]["x"] >= bb["x"] - CONTAIN_MARGIN and
                    elem_map[oid]["bbox"]["y"] >= bb["y"] - CONTAIN_MARGIN and
                    elem_map[oid]["bbox"]["x"] + elem_map[oid]["bbox"]["w"] <= bb["x"] + bb["w"] + CONTAIN_MARGIN and
                    elem_map[oid]["bbox"]["y"] + elem_map[oid]["bbox"]["h"] <= bb["y"] + bb["h"] + CONTAIN_MARGIN
                    for oid in other_cluster
                )
                if all_inside:
                    contained_cluster_idx[ci_other] = eid

    # 포함된 요소 → embedded_content 정리
    cell_embedded = {}
    for oid, container_eid in contained_elems.items():
        oe = elem_map[oid]
        if container_eid not in cell_embedded:
            cell_embedded[container_eid] = []
        cell_embedded[container_eid].append((oe["bbox"]["y"], {
            "type": "paragraph",
            "text": oe["text"],
            "style": oe.get("style", {}),
        }))

    for ci_other, container_eid in contained_cluster_idx.items():
        other_cluster = table_clusters[ci_other]
        other_elems = sorted([elem_map[oid] for oid in other_cluster],
                            key=lambda x: (x["bbox"]["y"], x["bbox"]["x"]))
        min_y = other_elems[0]["bbox"]["y"]
        if container_eid not in cell_embedded:
            cell_embedded[container_eid] = []
        cell_embedded[container_eid].append((min_y, {
            "type": "sub_table",
            "elements": other_elems,
        }))

    for key in cell_embedded:
        cell_embedded[key].sort(key=lambda x: x[0])

    # --- 5) 전체 sections 조합 (Y좌표 순) ---
    sections = []
    section_items = []

    if title_rows:
        ta_rows = [make_title_row(r) for r in title_rows]
        min_y = min(e["bbox"]["y"] for r in title_rows for e in r)
        section_items.append((min_y, {"type": "title_area", "rows": ta_rows}))

    # 인접한 non-table 요소를 테이블 클러스터에 병합
    post_table_ids_used = set()
    all_contained_ids = set(contained_elems.keys())
    for ci_other in contained_cluster_idx:
        all_contained_ids |= table_clusters[ci_other]

    for ci, cluster in enumerate(table_clusters):
        if ci in contained_cluster_idx:
            continue
        cluster_elems = [elem_map[eid] for eid in cluster]
        c_min_y = min(e["bbox"]["y"] for e in cluster_elems)
        c_max_y = max(e["bbox"]["y"] + e["bbox"]["h"] for e in cluster_elems)
        c_min_x = min(e["bbox"]["x"] for e in cluster_elems)

        for row in post_table_rows:
            for e in row:
                if e["id"] in all_contained_ids:
                    continue
                ey = e["bbox"]["y"]
                ex_end = e["bbox"]["x"] + e["bbox"]["w"]
                if (c_min_y - 5 <= ey <= c_max_y + 5 and ex_end <= c_min_x + 5
                        and e["id"] not in cluster):
                    cluster.add(e["id"])
                    post_table_ids_used.add(e["id"])

    # 흡수/포함된 요소 제거
    used_ids = post_table_ids_used | all_contained_ids
    if used_ids:
        post_table_rows = [
            [e for e in row if e["id"] not in used_ids]
            for row in post_table_rows
        ]
        post_table_rows = [row for row in post_table_rows if row]

    # table clusters → section_items
    for ci, cluster in enumerate(table_clusters):
        if ci in contained_cluster_idx:
            continue
        min_y = min(elem_map[eid]["bbox"]["y"] for eid in cluster)
        tbl = cluster_to_table(cluster)

        # embedded content 처리
        for cell_data in tbl.get("table", {}).get("cells", []):
            for eid in cluster:
                e = elem_map[eid]
                if eid in cell_embedded:
                    paras = []
                    for _, content_item in cell_embedded[eid]:
                        if content_item["type"] == "paragraph":
                            text = content_item["text"]
                            style = content_item.get("style", {})
                            for line in text.split("\n"):
                                paras.append({
                                    "text": line,
                                    "bold": style.get("bold", False),
                                    "text_color": style.get("text_color", "#000000"),
                                    "font_size_pt": style.get("font_size_pt", 10),
                                    "align": style.get("align", "LEFT"),
                                })
                        elif content_item["type"] == "sub_table":
                            sub_elems = content_item["elements"]
                            sub_rows_map = {}
                            for se in sub_elems:
                                ry = round(se["bbox"]["y"])
                                if ry not in sub_rows_map:
                                    sub_rows_map[ry] = []
                                sub_rows_map[ry].append(se)
                            paras.append({"text": "", "bold": False, "text_color": "#000000",
                                         "font_size_pt": 10, "align": "LEFT"})
                            for ry in sorted(sub_rows_map.keys()):
                                row_texts = [se["text"] for se in
                                           sorted(sub_rows_map[ry], key=lambda x: x["bbox"]["x"])]
                                line = " | ".join(row_texts)
                                is_header = any(se.get("style", {}).get("bold") for se in sub_rows_map[ry])
                                paras.append({
                                    "text": line,
                                    "bold": is_header,
                                    "text_color": "#000000",
                                    "font_size_pt": 9,
                                    "align": "LEFT",
                                })
                            paras.append({"text": "", "bold": False, "text_color": "#000000",
                                         "font_size_pt": 10, "align": "LEFT"})

                    if e["text"].strip() == "" and cell_data.get("text", "").strip() == "":
                        if cell_data.get("row") is not None:
                            cell_data["cell_paragraphs"] = paras
                            break

        section_items.append((min_y, tbl))

    # post_table non-table 요소들
    for row in post_table_rows:
        row_y = min(e["bbox"]["y"] for e in row)
        row_data = make_title_row(row)
        section_items.append((row_y, row_data))

    # Y좌표 순 정렬
    section_items.sort(key=lambda x: x[0])
    sections = [item[1] for item in section_items]

    # 문서 제목 추출
    title = ""
    for s in sections:
        if s.get("type") == "title_area":
            for r in s.get("rows", []):
                if r.get("type") == "paragraph":
                    t = r.get("content", "")
                    if len(t) > len(title) and "이내" not in t:
                        title = t
                elif r.get("type") == "inline_row":
                    for el in r.get("elements", []):
                        if el.get("type") == "text":
                            t = el.get("content", "")
                            if len(t) > len(title):
                                title = t

    return {
        "document": {"title": title, "page_width_hu": 42520, "description": title},
        "sections": sections
    }


def postprocess_structure(doc_structure):
    """Gemini 분석 결과 후처리 - 제목부를 borderless table로 병합"""
    sections = doc_structure.get("sections", [])
    if not sections:
        return doc_structure

    title_elements = []
    rest_start = 0
    for i, sec in enumerate(sections):
        if sec.get("type") == "table":
            rest_start = i
            break
        title_elements.append(sec)
        rest_start = i + 1

    if len(title_elements) < 2:
        return doc_structure

    rows = []
    for elem in title_elements:
        etype = elem.get("type", "paragraph")
        if etype == "inline_row":
            rows.append({"type": "inline_row", "data": elem})
        elif etype == "paragraph":
            rows.append({
                "type": "paragraph",
                "content": elem.get("content", ""),
                "align": elem.get("align", "CENTER"),
                "style": elem.get("style", {})
            })
        elif etype == "label_box":
            rows.append({"type": "label_box", "data": elem})

    title_area = {"type": "title_area", "rows": rows}
    doc_structure["sections"] = [title_area] + sections[rest_start:]
    print(f"    [후처리] 제목부 {len(title_elements)}개 요소 → title_area로 병합")
    return doc_structure


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="레이아웃 JSON → HWP 구조 변환")
    parser.add_argument("layout_json", help="Gemini Vision 레이아웃 JSON")
    parser.add_argument("-o", "--output", default="structure.json", help="출력 구조 JSON 경로")
    args = parser.parse_args()

    with open(args.layout_json, 'r', encoding='utf-8') as f:
        layout = json.load(f)

    doc_structure = layout_to_structure(layout)
    doc_structure = postprocess_structure(doc_structure)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(doc_structure, f, ensure_ascii=False, indent=2)
    print(f"[OK] 구조 변환 완료: {args.output}")
