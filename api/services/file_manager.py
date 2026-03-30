"""파일 업로드/저장/조회/정리 관리"""

import os
import shutil
import tempfile
import threading
import time
import uuid

# HWP COM 변환은 한글 프로그램 단일 인스턴스 → 동시 호출 시 크래시 방지
_hwp_lock = threading.Lock()
_HWP_TIMEOUT = 30  # 초


class FileManager:
    def __init__(self, ttl_seconds=10800):  # 3시간
        self._files: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._ttl = ttl_seconds

    def save(self, src_path: str, original_name: str = "") -> str:
        file_id = uuid.uuid4().hex[:12]
        ext = os.path.splitext(original_name or src_path)[1]
        dest_dir = tempfile.mkdtemp()
        dest = os.path.join(dest_dir, f"{file_id}{ext}")
        shutil.copy2(src_path, dest)
        with self._lock:
            self._files[file_id] = {
                "path": dest,
                "name": original_name or os.path.basename(src_path),
                "created": time.time(),
            }
        return file_id

    async def save_upload(self, upload_file) -> str:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(upload_file.filename)[1])
        content = await upload_file.read()
        tmp.write(content)
        tmp.close()
        file_id = self.save(tmp.name, upload_file.filename)
        os.unlink(tmp.name)
        return file_id

    def get_path(self, file_id: str) -> str | None:
        with self._lock:
            entry = self._files.get(file_id)
        if not entry:
            return None
        # touch: 접근 시 TTL 갱신
        entry["created"] = time.time()
        return entry["path"]

    def get_name(self, file_id: str) -> str:
        with self._lock:
            entry = self._files.get(file_id)
        return entry["name"] if entry else ""

    def _com_convert(self, src_path, dst_path, dst_format):
        """COM 변환 공통 (Lock으로 직렬화)"""
        acquired = _hwp_lock.acquire(timeout=_HWP_TIMEOUT)
        if not acquired:
            raise RuntimeError("다른 사용자가 변환 중입니다. 잠시 후 다시 시도해주세요.")
        try:
            import pythoncom
            pythoncom.CoInitialize()
            try:
                from pyhwpx import Hwp
                hwp = Hwp(visible=False, register_module=True)
                hwp.open(src_path)
                hwp.save_as(dst_path, dst_format)
                hwp.clear()
                hwp.quit()
            finally:
                pythoncom.CoUninitialize()
        finally:
            _hwp_lock.release()

    def convert_hwp(self, file_id: str) -> str:
        """HWP → HWPX 변환 (보안 팝업 자동 처리, 동시 요청 직렬화)"""
        path = self.get_path(file_id)
        if not path or not path.lower().endswith(".hwp"):
            return file_id
        try:
            hwpx_path = os.path.join(tempfile.mkdtemp(), "converted.hwpx")
            self._com_convert(path, hwpx_path, "HWPX")
            new_id = self.save(hwpx_path, self.get_name(file_id).replace(".hwp", ".hwpx"))
            return new_id
        except Exception as e:
            raise RuntimeError(f"HWP 변환 실패: {e}")

    def convert_to_hwp(self, file_id: str) -> str:
        """HWPX → HWP 변환 (구버전 한글 호환용, 동시 요청 직렬화)"""
        path = self.get_path(file_id)
        if not path or not path.lower().endswith(".hwpx"):
            return file_id
        try:
            hwp_path = os.path.join(tempfile.mkdtemp(), "converted.hwp")
            self._com_convert(path, hwp_path, "HWP")
            name = self.get_name(file_id)
            if name.endswith(".hwpx"):
                name = name[:-1]
            new_id = self.save(hwp_path, name)
            return new_id
        except Exception as e:
            raise RuntimeError(f"HWP 변환 실패: {e}")

    def convert_to_docx(self, file_id: str) -> str:
        """HWPX → DOCX 변환 (python-docx, COM 불필요)"""
        path = self.get_path(file_id)
        if not path or not path.lower().endswith(".hwpx"):
            return file_id
        try:
            from hwpx_to_docx import convert_hwpx_to_docx
            docx_path = os.path.join(tempfile.mkdtemp(), "converted.docx")
            convert_hwpx_to_docx(path, docx_path)
            name = self.get_name(file_id).replace(".hwpx", ".docx")
            new_id = self.save(docx_path, name)
            return new_id
        except Exception as e:
            raise RuntimeError(f"DOCX 변환 실패: {e}")

    def convert_docx(self, file_id: str) -> str:
        """DOCX → HWPX 변환 (python-docx + build_hwpx, COM 불필요)"""
        path = self.get_path(file_id)
        if not path or not path.lower().endswith(".docx"):
            return file_id
        try:
            from docx_converter import parse_docx
            from core.build_hwpx import build_hwpx

            doc_json = parse_docx(path)
            hwpx_path = os.path.join(tempfile.mkdtemp(), "converted.hwpx")
            build_hwpx(doc_json, hwpx_path)
            name = self.get_name(file_id).replace(".docx", ".hwpx")
            new_id = self.save(hwpx_path, name)
            return new_id
        except Exception as e:
            raise RuntimeError(f"DOCX 변환 실패: {e}")

    def cleanup_expired(self):
        now = time.time()
        expired = []
        with self._lock:
            for fid, entry in self._files.items():
                if now - entry["created"] > self._ttl:
                    expired.append(fid)
            for fid in expired:
                entry = self._files.pop(fid)
                try:
                    d = os.path.dirname(entry["path"])
                    shutil.rmtree(d, ignore_errors=True)
                except Exception:
                    pass


file_manager = FileManager()
