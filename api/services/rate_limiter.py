"""봇 방지 - 분당 2회 rate limit"""

import time
from collections import defaultdict

_requests: dict[str, list[float]] = defaultdict(list)
WINDOW = 60  # 1분
MAX_PER_MINUTE = 2


def check_rate_limit(user_id: str) -> bool:
    """True = 통과, False = 제한됨"""
    now = time.time()
    # 오래된 기록 제거
    _requests[user_id] = [t for t in _requests[user_id] if now - t < WINDOW]

    if len(_requests[user_id]) >= MAX_PER_MINUTE:
        return False

    _requests[user_id].append(now)
    return True
