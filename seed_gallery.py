# -*- coding: utf-8 -*-
"""Gallery seed script - register government form templates (one-time)"""

import os
import json
import uuid

from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
BUCKET = "shared-forms"
SEED_USER_ID = "00000000-0000-0000-0000-000000000000"
SEED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed-forms")


def main():
    with open(os.path.join(os.path.dirname(__file__), "seed_forms.json"), "r", encoding="utf-8") as f:
        seed_forms = json.load(f)

    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    existing = sb.table("docflow_shared_forms").select("id, title, file_path").eq(
        "user_id", SEED_USER_ID
    ).execute()
    if existing.data:
        print(f"[DELETE] 기존 시드 {len(existing.data)}개 삭제 중...")
        for row in existing.data:
            # Storage에서 파일 삭제
            try:
                sb.storage.from_(BUCKET).remove([row["file_path"]])
            except Exception as e:
                print(f"  [WARN] Storage 삭제 실패: {row['file_path']} - {e}")
            # 좋아요 삭제
            try:
                sb.table("docflow_form_likes").delete().eq("form_id", row["id"]).execute()
            except Exception:
                pass
        # DB에서 전체 삭제
        sb.table("docflow_shared_forms").delete().eq("user_id", SEED_USER_ID).execute()
        print(f"[DELETE] 완료")

    success = 0
    for form in seed_forms:
        path = os.path.join(SEED_DIR, form["file"])
        if not os.path.exists(path):
            print(f"[FAIL] File not found: {path}")
            continue

        with open(path, "rb") as f:
            content = f.read()

        ext = os.path.splitext(path)[1].lower()
        storage_path = f"forms/seed/{uuid.uuid4().hex}{ext}"

        try:
            sb.storage.from_(BUCKET).upload(
                storage_path, content,
                file_options={"content-type": "application/octet-stream"}
            )
        except Exception as e:
            print(f"[FAIL] Storage: {form['title']} - {e}")
            continue

        # 필드 수 추출
        field_count = 0
        doc_type = None
        try:
            import tempfile as _tf
            tmp2 = _tf.NamedTemporaryFile(delete=False, suffix=ext)
            tmp2.write(content)
            tmp2.close()
            analyze_path = tmp2.name

            if ext == ".hwp":
                try:
                    import subprocess, shutil
                    hwpx_path = tmp2.name.replace(".hwp", "_conv.hwpx")
                    result_conv = subprocess.run(
                        ["python", "-c",
                         f"from api.services.file_manager import file_manager; "
                         f"fid = file_manager.save(r'{tmp2.name}', 'seed_tmp.hwp'); "
                         f"cid = file_manager.convert_hwp(fid); "
                         f"p = file_manager.get_path(cid); "
                         f"print(p)"],
                        capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__))
                    )
                    converted = result_conv.stdout.strip()
                    if converted and os.path.exists(converted):
                        analyze_path = converted
                except Exception as ce:
                    print(f"  [WARN] HWP 변환 실패: {ce}")

            if analyze_path.lower().endswith(".hwpx") and os.path.exists(analyze_path):
                import sys
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                from clone_form import extract_texts
                from api.services.doc_type_detector import detect_doc_type
                fields = extract_texts(analyze_path)
                field_count = len(fields)
                doc_info = detect_doc_type(fields)
                doc_type = doc_info.get("type")

            try:
                os.unlink(tmp2.name)
            except Exception:
                pass
        except Exception as fe:
            print(f"  [WARN] 필드 추출 실패: {fe}")

        try:
            sb.table("docflow_shared_forms").insert({
                "user_id": SEED_USER_ID,
                "title": form["title"],
                "category": form["category"],
                "file_path": storage_path,
                "file_size": len(content),
                "field_count": field_count,
                "doc_type": doc_type,
                "likes": 0,
                "downloads": 0,
            }).execute()
            print(f"[OK] {form['title']} (필드: {field_count}개, 타입: {doc_type})")
            success += 1
        except Exception as e:
            print(f"[FAIL] DB: {form['title']} - {e}")
            try:
                sb.storage.from_(BUCKET).remove([storage_path])
            except:
                pass

    print(f"\nDone: {success}/{len(seed_forms)} seeded")


if __name__ == "__main__":
    main()
