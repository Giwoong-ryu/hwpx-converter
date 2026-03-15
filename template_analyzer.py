"""
HWPX 템플릿 심층 분석 모듈
analyze_template.py (로컬 스킬)에서 포팅.

기능:
- HWPX에서 header.xml / section0.xml 추출
- 문서 구조 분석 리포트 생성 (폰트, 스타일, 테이블 레이아웃)
"""
import os
import tempfile
import shutil
import zipfile
from lxml import etree

NS = {
    'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
    'hs': 'http://www.hancom.co.kr/hwpml/2011/section',
    'hc': 'http://www.hancom.co.kr/hwpml/2011/core',
    'hh': 'http://www.hancom.co.kr/hwpml/2011/head',
}


def extract_header(hwpx_path: str, output_dir: str) -> str:
    """HWPX에서 header.xml을 추출하여 output_dir에 저장. 경로 반환."""
    with zipfile.ZipFile(hwpx_path, 'r') as zf:
        header_data = zf.read('Contents/header.xml')
    dst = os.path.join(output_dir, 'header.xml')
    with open(dst, 'wb') as f:
        f.write(header_data)
    return dst


def extract_section(hwpx_path: str, output_dir: str) -> str:
    """HWPX에서 section0.xml을 추출하여 output_dir에 저장. 경로 반환."""
    with zipfile.ZipFile(hwpx_path, 'r') as zf:
        section_data = zf.read('Contents/section0.xml')
    dst = os.path.join(output_dir, 'section0.xml')
    with open(dst, 'wb') as f:
        f.write(section_data)
    return dst


def analyze_hwpx(hwpx_path: str) -> str:
    """HWPX 파일 구조를 분석하여 사람이 읽을 수 있는 리포트 반환."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(hwpx_path, 'r') as zf:
            zf.extractall(tmpdir)

        header_path = os.path.join(tmpdir, 'Contents', 'header.xml')
        section_path = os.path.join(tmpdir, 'Contents', 'section0.xml')

        if not os.path.exists(header_path) or not os.path.exists(section_path):
            return "header.xml 또는 section0.xml이 없는 파일입니다."

        header_root = etree.parse(header_path).getroot()
        section_root = etree.parse(section_path).getroot()

        lines = []
        lines.append(f"HWPX 분석: {os.path.basename(hwpx_path)}")
        lines.append("=" * 50)

        # 폰트
        lines.append("\n[폰트]")
        for fontface in header_root.findall('.//hh:fontface', NS):
            lang = fontface.get('lang', '?')
            if lang == 'HANGUL':
                for font in fontface.findall('hh:font', NS):
                    lines.append(f"  hangul/{font.get('id')}: {font.get('face')}")

        # borderFill
        lines.append("\n[borderFill]")
        for bf in header_root.findall('.//hh:borderFill', NS):
            bid = bf.get('id')
            bg = "없음"
            fill = bf.find('.//hc:winBrush', NS)
            if fill is not None:
                fc = fill.get('faceColor', 'none')
                if fc != 'none':
                    bg = fc
            lines.append(f"  [{bid}] 배경={bg}")

        # charPr
        lines.append("\n[charPr]")
        for cp in header_root.findall('.//hh:charPr', NS):
            cid = cp.get('id')
            height = int(cp.get('height', '0'))
            pt = height / 100
            color = cp.get('textColor', '#000000')
            bold = "볼드" if cp.find('hh:bold', NS) is not None else ""
            lines.append(f"  [{cid}] {pt}pt {color} {bold}".rstrip())

        # 페이지 크기
        secpr = section_root.find('.//hp:secPr', NS)
        if secpr is not None:
            pagepr = secpr.find('hp:pagePr', NS)
            if pagepr is not None:
                w = pagepr.get('width', '?')
                h = pagepr.get('height', '?')
                lines.append(f"\n[페이지] {w} x {h}")
                margin = pagepr.find('hp:margin', NS)
                if margin is not None:
                    lines.append(f"  여백: 좌={margin.get('left')} 우={margin.get('right')} 상={margin.get('top')} 하={margin.get('bottom')}")

        # 테이블 수
        tables = section_root.findall('.//hp:tbl', NS)
        lines.append(f"\n[구조] 테이블 {len(tables)}개")
        for i, tbl in enumerate(tables):
            rows = tbl.get('rowCnt', '?')
            cols = tbl.get('colCnt', '?')
            sz = tbl.find('hp:sz', NS)
            tw = sz.get('width', '?') if sz is not None else '?'
            lines.append(f"  테이블{i+1}: {rows}행 x {cols}열 (w={tw})")

        # 문단 수
        sec = section_root.find('.//hs:sec', NS)
        if sec is None:
            sec = section_root
        paras = sec.findall('hp:p', NS)
        lines.append(f"  문단 {len(paras)}개")

        return '\n'.join(lines)
