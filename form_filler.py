"""
HWPX 양식 채우기 모듈
기존 .hwpx 파일의 {{플레이스홀더}}를 데이터로 치환
"""
import os
import re
import uuid
import tempfile
from pathlib import Path
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED

from lxml import etree

PLACEHOLDER_RE = re.compile(r'\{\{([^}]+)\}\}')


def analyze_template(hwpx_path: str) -> tuple[list[str], str]:
    """HWPX 파일에서 {{placeholder}} 목록 추출.

    Returns:
        (필드명 리스트, 요약 텍스트)
    """
    try:
        with ZipFile(hwpx_path, 'r') as zf:
            if 'Contents/section0.xml' not in zf.namelist():
                return [], "section0.xml이 없는 파일입니다."
            section_xml = zf.read('Contents/section0.xml').decode('utf-8')
    except Exception as e:
        return [], f"HWPX 파일 읽기 실패: {e}"

    placeholders = []
    seen = set()
    for match in PLACEHOLDER_RE.finditer(section_xml):
        name = match.group(1).strip()
        if name not in seen:
            placeholders.append(name)
            seen.add(name)

    if not placeholders:
        summary = "{{플레이스홀더}}를 찾지 못했습니다.\n"
        summary += "양식 파일에 {{이름}}, {{부서}} 등의 마커를 넣어주세요."
    else:
        summary = f"검출된 필드 {len(placeholders)}개:\n"
        summary += ", ".join(f"{{{{{p}}}}}" for p in placeholders)
        summary += "\n\n아래 JSON에 값을 입력하세요:\n"
        example = {p: "" for p in placeholders}
        import json
        summary += json.dumps(example, ensure_ascii=False, indent=2)

    return placeholders, summary


def fill_template(hwpx_path: str, values: dict) -> tuple[str, str]:
    """HWPX 파일의 {{placeholder}}를 values로 치환한 새 파일 생성.

    Returns:
        (출력 파일 경로, 로그 텍스트)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = os.path.join(tmpdir, 'work')

        # 1. Unzip
        with ZipFile(hwpx_path, 'r') as zf:
            zf.extractall(work_dir)

        # 2. section0.xml 치환
        section_path = os.path.join(work_dir, 'Contents', 'section0.xml')
        with open(section_path, 'r', encoding='utf-8') as f:
            content = f.read()

        replaced_count = 0
        for key, value in values.items():
            safe_value = _xml_escape(str(value))
            marker = f'{{{{{key}}}}}'
            count = content.count(marker)
            if count > 0:
                content = content.replace(marker, safe_value)
                replaced_count += count

        # 치환 안 된 플레이스홀더 확인
        remaining = PLACEHOLDER_RE.findall(content)

        with open(section_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # 3. XML 검증
        try:
            etree.fromstring(content.encode('utf-8'))
        except etree.XMLSyntaxError as e:
            raise RuntimeError(f"치환 후 XML 검증 실패: {e}")

        # 4. Repack
        unique = uuid.uuid4().hex[:8]
        output_name = f"filled_{unique}.hwpx"
        output_path = os.path.join(tempfile.gettempdir(), output_name)

        _pack_hwpx(Path(work_dir), Path(output_path))

        # 5. 로그
        log = f"치환 완료\n"
        log += f"  치환된 필드: {replaced_count}개\n"
        if remaining:
            log += f"  미치환 필드: {', '.join(f'{{{{{r}}}}}' for r in remaining)}\n"
        log += f"  파일: {output_name}"

        return output_path, log


def _xml_escape(text: str) -> str:
    """XML 특수문자 이스케이프"""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))


def _pack_hwpx(work_dir: Path, output_path: Path) -> None:
    """디렉토리를 HWPX로 패킹 (mimetype first, ZIP_STORED)"""
    mimetype_file = work_dir / 'mimetype'

    all_files = sorted(
        p.relative_to(work_dir).as_posix()
        for p in work_dir.rglob('*')
        if p.is_file()
    )

    with ZipFile(output_path, 'w', ZIP_DEFLATED) as zf:
        if mimetype_file.is_file():
            zf.write(mimetype_file, 'mimetype', compress_type=ZIP_STORED)
        for rel_path in all_files:
            if rel_path == 'mimetype':
                continue
            zf.write(work_dir / rel_path, rel_path, compress_type=ZIP_DEFLATED)
