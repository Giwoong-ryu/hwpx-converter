"""Supabase 클라이언트 싱글톤"""

import os
from supabase import create_client, Client

_client: Client | None = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL, SUPABASE_KEY 환경변수 필요")
        _client = create_client(url, key)
    return _client
