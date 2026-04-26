"""파일 업로드/저장/조회/정리 관리"""

import os
import shutil
import tempfile
import threading
import time
import uuid

import httpx

# HWP COM 변환은 한글 프로그램 단일 인스턴스 → 동시 호출 시 크래시 방지
_hwp_lock = threading.Lock()
_HWP_TIMEOUT = 60  # 초 (인스턴스 재사용 시 대기 시간 여유)

# 원격 HWP 변환 서버 URL (Railway 배포 시 설정)
_HWP_CONVERT_URL = os.environ.get("HWP_CONVERT_URL", "")

# 한글 인스턴스 재사용 (시작/종료 10-15초 절감)
_hwp_instance = None
_hwp_com_initialized = False


def _cleanup_hwp():
    """서버 종료 시 한글 인스턴스 정리"""
    global _hwp_instance
    if _hwp_instance is not None:
        try:
            _hwp_instance.quit()
        except Exception:
            pass
        _hwp_instance = None


import atexit
atexit.register(_cleanup_hwp)


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
        """COM 변환 공통 (Lock으로 직렬화, 인스턴스 재사용) - 로컬 Windows에서만 동작"""
        global _hwp_instance, _hwp_com_initialized

        acquired = _hwp_lock.acquire(timeout=_HWP_TIMEOUT)
        if not acquired:
            raise RuntimeError("다른 사용자가 변환 중입니다. 잠시 후 다시 시도해주세요.")
        try:
            import pythoncom
            if not _hwp_com_initialized:
                pythoncom.CoInitialize()
                _hwp_com_initialized = True

            # 기존 인스턴스 재사용 시도
            hwp = _hwp_instance
            if hwp is not None:
                try:
                    hwp.clear()  # 이전 문서 상태 정리
                    hwp.open(src_path)
                    import time as _t
                    _t.sleep(0.3)  # 파일 로드 완료 대기
                    hwp.save_as(dst_path, dst_format)
                    hwp.clear()
                    return
                except Exception:
                    # 인스턴스 죽었으면 새로 생성
                    try:
                        hwp.quit()
                    except Exception:
                        pass
                    _hwp_instance = None

            # 새 인스턴스 생성
            from pyhwpx import Hwp
            hwp = Hwp(visible=False, register_module=True)
            hwp.open(src_path)
            import time as _t
            _t.sleep(0.5)  # 파일 로드 완료 대기
            hwp.save_as(dst_path, dst_format)
            hwp.clear()
            _hwp_instance = hwp  # 재사용을 위해 종료하지 않고 유지
        except Exception:
            # 실패 시 인스턴스 정리
            if _hwp_instance is not None:
                try:
                    _hwp_instance.quit()
                except Exception:
                    pass
                _hwp_instance = None
            raise
        finally:
            _hwp_lock.release()

    def _remote_convert(self, src_path: str, dst_path: str, endpoint: str):
        """원격 HWP 변환 서버로 파일 전송 후 결과 저장"""
        url = f"{_HWP_CONVERT_URL.rstrip('/')}/{endpoint}"
        with open(src_path, "rb") as f:
            resp = httpx.post(
                url,
                files={"file": (os.path.basename(src_path), f)},
                timeout=60.0,
            )
        if resp.status_code != 200:
            if resp.status_code in (502, 503, 504, 530):
                raise RuntimeError(
                    "HWP 변환 서버가 일시적으로 점검 중입니다. "
                    "한글에서 '다른 이름으로 저장 > HWPX'로 저장 후 다시 업로드해주세요."
                )
            detail = resp.text[:200] if resp.text else "변환 서버 오류"
            raise RuntimeError(
                f"HWP 변환 서버 오류 ({resp.status_code}): {detail}"
            )
        with open(dst_path, "wb") as f:
            f.write(resp.content)

    def convert_hwp(self, file_id: str) -> str:
        """HWP -> HWPX 변환. HWP_CONVERT_URL 설정 시 원격, 아니면 로컬 COM."""
        path = self.get_path(file_id)
        if not path or not path.lower().endswith(".hwp"):
            return file_id
        try:
            hwpx_path = os.path.join(tempfile.mkdtemp(), "converted.hwpx")
            if _HWP_CONVERT_URL:
                self._remote_convert(path, hwpx_path, "convert")
            else:
                self._com_convert(path, hwpx_path, "HWPX")
            new_id = self.save(hwpx_path, self.get_name(file_id).replace(".hwp", ".hwpx"))
            return new_id
        except RuntimeError:
            raise
        except Exception as e:
            if _HWP_CONVERT_URL:
                raise RuntimeError(
                    "HWP 변환 서버가 일시적으로 점검 중입니다. "
                    "한글에서 '다른 이름으로 저장 > HWPX'로 저장 후 다시 업로드해주세요."
                )
            raise RuntimeError(
                "HWP 파일을 변환할 수 없습니다. "
                "비밀번호가 설정된 문서이거나 파일이 손상되었을 수 있습니다. "
                "한글에서 직접 '다른 이름으로 저장 > HWPX'로 저장 후 업로드해주세요."
            )

    def convert_to_hwp(self, file_id: str) -> str:
        """HWPX -> HWP 변환. HWP_CONVERT_URL 설정 시 원격, 아니면 로컬 COM."""
        path = self.get_path(file_id)
        if not path or not path.lower().endswith(".hwpx"):
            return file_id
        try:
            hwp_path = os.path.join(tempfile.mkdtemp(), "converted.hwp")
            if _HWP_CONVERT_URL:
                self._remote_convert(path, hwp_path, "convert-to-hwp")
            else:
                self._com_convert(path, hwp_path, "HWP")
            name = self.get_name(file_id)
            if name.endswith(".hwpx"):
                name = name[:-1]
            new_id = self.save(hwp_path, name)
            return new_id
        except RuntimeError:
            raise
        except Exception as e:
            if _HWP_CONVERT_URL:
                raise RuntimeError(
                    "HWP 변환 서버가 일시적으로 점검 중입니다. "
                    "한글에서 '다른 이름으로 저장 > HWPX'로 저장 후 다시 업로드해주세요."
                )
            raise RuntimeError(
                "HWP 파일을 변환할 수 없습니다. "
                "비밀번호가 설정된 문서이거나 파일이 손상되었을 수 있습니다. "
                "한글에서 직접 '다른 이름으로 저장 > HWPX'로 저장 후 업로드해주세요."
            )

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
        """DOCX → HWPX 변환. 현재 미지원 — HWP/HWPX 업로드 안내."""
        raise RuntimeError(
            "DOCX 파일은 양식으로 사용할 수 없습니다. "
            "HWP 또는 HWPX 파일을 업로드해주세요. "
            "DOCX 안의 내용을 양식에 넣으려면 AI 자동 작성에서 파일을 첨부하세요."
        )

    def cleanup_expired(self):
        """등록된 파일 TTL 정리 + orphan 임시 디렉토리 정리"""
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

        # orphan 임시 디렉토리 정리 (clone 등에서 만든 미등록 tmp)
        try:
            tmp_root = tempfile.gettempdir()
            for d in os.listdir(tmp_root):
                full = os.path.join(tmp_root, d)
                if not os.path.isdir(full) or not d.startswith("tmp"):
                    continue
                try:
                    age = now - os.path.getmtime(full)
                    if age > 3600:  # 1시간 이상
                        shutil.rmtree(full, ignore_errors=True)
                except Exception:
                    pass
        except Exception:
            pass


file_manager = FileManager()
