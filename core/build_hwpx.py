"""
HWPX 빌드 모듈
템플릿 기반 HWPX 파일 생성 + 검증
"""
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

from lxml import etree

# fix_namespaces 자동 호출용
try:
    import importlib.util
    _fn_path = Path(__file__).resolve().parent.parent / "fix_namespaces.py"
    if _fn_path.exists():
        _fn_spec = importlib.util.spec_from_file_location("fix_namespaces", str(_fn_path))
        _fn_mod = importlib.util.module_from_spec(_fn_spec)
        _fn_spec.loader.exec_module(_fn_mod)
        fix_hwpx_namespaces = _fn_mod.fix_hwpx_namespaces
        _HAS_FIX_NS = True
    else:
        _HAS_FIX_NS = False
except Exception:
    _HAS_FIX_NS = False

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
TEMPLATES_DIR = PROJECT_DIR / "templates"
BASE_DIR = TEMPLATES_DIR / "base"

AVAILABLE_TEMPLATES = ["auto", "gonmun", "report", "minutes", "proposal"]


def validate_xml(filepath: Path) -> None:
    """XML well-formedness 검증"""
    try:
        etree.parse(str(filepath))
    except etree.XMLSyntaxError as e:
        raise SystemExit(f"Malformed XML in {filepath.name}: {e}")


def update_metadata(content_hpf: Path, title: str | None, creator: str | None) -> None:
    """content.hpf 메타데이터 업데이트"""
    if not title and not creator:
        return

    tree = etree.parse(str(content_hpf))
    root = tree.getroot()
    ns = {"opf": "http://www.idpf.org/2007/opf/"}

    if title:
        title_el = root.find(".//opf:title", ns)
        if title_el is not None:
            title_el.text = title

    now = datetime.now(timezone.utc)
    iso_now = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    for meta in root.findall(".//opf:meta", ns):
        name = meta.get("name", "")
        if creator and name == "creator":
            meta.text = creator
        elif creator and name == "lastsaveby":
            meta.text = creator
        elif name == "CreatedDate":
            meta.text = iso_now
        elif name == "ModifiedDate":
            meta.text = iso_now
        elif name == "date":
            meta.text = now.strftime("%Y년 %m월 %d일")

    etree.indent(root, space="  ")
    tree.write(
        str(content_hpf),
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    )


def pack_hwpx(input_dir: Path, output_path: Path) -> None:
    """HWPX 아카이브 생성 (mimetype first, ZIP_STORED)"""
    mimetype_file = input_dir / "mimetype"
    if not mimetype_file.is_file():
        raise SystemExit(f"Missing 'mimetype' in {input_dir}")

    all_files = sorted(
        p.relative_to(input_dir).as_posix()
        for p in input_dir.rglob("*")
        if p.is_file()
    )

    with ZipFile(output_path, "w", ZIP_DEFLATED) as zf:
        zf.write(mimetype_file, "mimetype", compress_type=ZIP_STORED)
        for rel_path in all_files:
            if rel_path == "mimetype":
                continue
            zf.write(input_dir / rel_path, rel_path, compress_type=ZIP_DEFLATED)


def validate_hwpx(hwpx_path: Path) -> list[str]:
    """HWPX 구조 검증"""
    errors: list[str] = []
    required = [
        "mimetype",
        "Contents/content.hpf",
        "Contents/header.xml",
        "Contents/section0.xml",
    ]

    try:
        from zipfile import BadZipFile
        zf = ZipFile(hwpx_path, "r")
    except BadZipFile:
        return [f"Not a valid ZIP: {hwpx_path}"]

    with zf:
        names = zf.namelist()
        for r in required:
            if r not in names:
                errors.append(f"Missing: {r}")

        if "mimetype" in names:
            content = zf.read("mimetype").decode("utf-8").strip()
            if content != "application/hwp+zip":
                errors.append(f"Bad mimetype content: {content}")
            if names[0] != "mimetype":
                errors.append("mimetype is not the first ZIP entry")
            info = zf.getinfo("mimetype")
            if info.compress_type != ZIP_STORED:
                errors.append("mimetype is not ZIP_STORED")

        for name in names:
            if name.endswith(".xml") or name.endswith(".hpf"):
                try:
                    etree.fromstring(zf.read(name))
                except etree.XMLSyntaxError as e:
                    errors.append(f"Malformed XML: {name}: {e}")

    return errors


def build(
    template: str | None,
    header_override: Path | None,
    section_override: Path | None,
    title: str | None,
    creator: str | None,
    output: Path,
) -> list[str]:
    """메인 빌드 로직. 오류 목록 반환 (빈 리스트 = 성공)"""

    if not BASE_DIR.is_dir():
        return [f"Base template not found: {BASE_DIR}"]

    with tempfile.TemporaryDirectory() as tmpdir:
        work = Path(tmpdir) / "build"
        shutil.copytree(BASE_DIR, work)

        if template:
            overlay_dir = TEMPLATES_DIR / template
            if overlay_dir.is_dir():
                for overlay_file in overlay_dir.iterdir():
                    if overlay_file.is_file() and overlay_file.suffix == ".xml":
                        dest = work / "Contents" / overlay_file.name
                        shutil.copy2(overlay_file, dest)

        if header_override:
            if not header_override.is_file():
                return [f"Header file not found: {header_override}"]
            shutil.copy2(header_override, work / "Contents" / "header.xml")

        if section_override:
            if not section_override.is_file():
                return [f"Section file not found: {section_override}"]
            shutil.copy2(section_override, work / "Contents" / "section0.xml")

        update_metadata(work / "Contents" / "content.hpf", title, creator)

        for xml_file in work.rglob("*.xml"):
            validate_xml(xml_file)
        for hpf_file in work.rglob("*.hpf"):
            validate_xml(hpf_file)

        pack_hwpx(work, output)

    # Namespace fix (한컴 뷰어 호환)
    if _HAS_FIX_NS:
        try:
            fix_hwpx_namespaces(str(output))
        except Exception:
            pass

    errors = validate_hwpx(output)
    return errors
