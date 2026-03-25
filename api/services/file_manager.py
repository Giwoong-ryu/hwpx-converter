"""파일 업로드/저장/조회/정리 관리"""

import os
import shutil
import tempfile
import threading
import time
import uuid


class FileManager:
    def __init__(self, ttl_seconds=3600):
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
        return entry["path"]

    def get_name(self, file_id: str) -> str:
        with self._lock:
            entry = self._files.get(file_id)
        return entry["name"] if entry else ""

    def convert_hwp(self, file_id: str) -> str:
        """HWP → HWPX 변환 (pyhwpx 사용, 보안 팝업 자동 처리)"""
        path = self.get_path(file_id)
        if not path or not path.lower().endswith(".hwp"):
            return file_id
        try:
            import pythoncom
            pythoncom.CoInitialize()
            try:
                from pyhwpx import Hwp
                hwp = Hwp(visible=False, register_module=True)
                hwp.open(path)
                hwpx_path = os.path.join(tempfile.mkdtemp(), "converted.hwpx")
                hwp.save_as(hwpx_path, "HWPX")
                hwp.clear()
                hwp.quit()
            finally:
                pythoncom.CoUninitialize()
            new_id = self.save(hwpx_path, self.get_name(file_id).replace(".hwp", ".hwpx"))
            return new_id
        except Exception as e:
            raise RuntimeError(f"HWP 변환 실패: {e}")

    def convert_to_hwp(self, file_id: str) -> str:
        """HWPX → HWP 변환 (구버전 한글 호환용)"""
        path = self.get_path(file_id)
        if not path or not path.lower().endswith(".hwpx"):
            return file_id
        try:
            import pythoncom
            pythoncom.CoInitialize()
            try:
                from pyhwpx import Hwp
                hwp = Hwp(visible=False, register_module=True)
                hwp.open(path)
                hwp_path = os.path.join(tempfile.mkdtemp(), "converted.hwp")
                hwp.save_as(hwp_path, "HWP")
                hwp.clear()
                hwp.quit()
            finally:
                pythoncom.CoUninitialize()
            name = self.get_name(file_id)
            if name.endswith(".hwpx"):
                name = name[:-1]  # .hwpx → .hwp
            new_id = self.save(hwp_path, name)
            return new_id
        except Exception as e:
            raise RuntimeError(f"HWP 변환 실패: {e}")

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
