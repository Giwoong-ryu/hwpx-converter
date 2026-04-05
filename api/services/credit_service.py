"""% 게이지 기반 크레딧 서비스 + 보상 시스템"""

import random
from datetime import date, timedelta
from api.services.supabase_client import get_supabase

# ═══ 내부 설정 (사용자에게 비공개) ═══

# Plus 100% = 매핑 30회 + 작성 10회
# Pro 100% = 매핑 200회 + 작성 100회 (사실상 무제한)
GAUGE_COST = {
    "plus":  {"mapping": 3.33, "generation": 10.0, "batch": 3.33},
    "pro":   {"mapping": 0.5,  "generation": 1.0,  "batch": 0.5},
}

# 무료 일일 한도
FREE_DAILY = {
    "mapping": 3,
    "generation": 1,  # +재시도 1회 = 실제 2회
}

PLAN_DEFAULTS = {
    "free": {"preset_limit": 1, "mapping_save_limit": 0, "streak_freeze_count": 0},
    "plus": {"preset_limit": 3, "mapping_save_limit": 10, "streak_freeze_count": 1},
    "pro": {"preset_limit": 9999, "mapping_save_limit": 9999, "streak_freeze_count": 2},
}

# ═══ 업적 정의 ═══
ACHIEVEMENTS = {
    "first_doc": {"condition_docs": 1, "reward": 25.0, "label": "첫 문서 완성"},
    "docs_5": {"condition_docs": 5, "reward": 50.0, "label": "문서 5건 달성"},
    "docs_10": {"condition_docs": 10, "reward": 50.0, "label": "문서 10건 달성"},
}

# ═══ 레벨 정의 ═══
LEVELS = [
    {"level": 1, "title": "새내기", "docs": 0, "reward": 0},
    {"level": 2, "title": "문서러", "docs": 5, "reward": 25.0},
    {"level": 3, "title": "자동화 전문가", "docs": 20, "reward": 50.0},
    {"level": 4, "title": "문서 마스터", "docs": 50, "reward": 50.0},
    {"level": 5, "title": "DocFlow 달인", "docs": 100, "reward": 50.0},
]

# ═══ 스트릭 보상 ═══
STREAK_REWARDS = {
    3: 10.0,
    7: 25.0,
    14: 25.0,
    30: 50.0,
}

# ═══ 럭키 보너스 ═══
LUCKY_TABLE = [
    (0.80, 0),      # 80% 없음
    (0.95, 10.0),   # 15% +10%
    (0.99, 25.0),   # 4% +25%
    (1.00, 100.0),  # 1% +100%
]


# ═══ 게이지 조회 ═══

async def get_user_status(user_id: str) -> dict:
    """사용자 전체 상태 (게이지, 레벨, 스트릭 등)"""
    sb = get_supabase()
    result = sb.table("docflow_users").select("*").eq("id", user_id).single().execute()
    if not result.data:
        return None
    u = result.data
    lvl = _get_level_info(u.get("level", 1))
    return {
        "plan": u["plan"],
        "gauge_pct": float(u.get("gauge_percent", 0)),
        "level": u.get("level", 1),
        "level_title": lvl["title"],
        "streak_days": u.get("streak_days", 0),
        "total_docs": u.get("total_docs_completed", 0),
        "preset_limit": u.get("preset_limit", 1),
        "mapping_save_limit": u.get("mapping_save_limit", 0),
        "referral_code": u.get("referral_code"),
        "first_purchase_used": u.get("first_purchase_used", False),
    }


# ═══ 게이지 사용 ═══

async def use_gauge(user_id: str, action: str) -> dict:
    """게이지 차감 (overview Part C 차감 흐름 준수).

    Returns:
        성공: {"ok": True, "gauge_pct": N, "plan": "...", "cost": N}
        실패: {"ok": False, "error_code": "...", "detail": "...", "plan": "...", "gauge_pct": N}
    """
    sb = get_supabase()
    user = sb.table("docflow_users").select(
        "plan, gauge_percent, streak_days, streak_last_date, streak_freeze_count"
    ).eq("id", user_id).single().execute()

    if not user.data:
        return {"ok": False, "error_code": "USER_NOT_FOUND",
                "detail": "사용자를 찾을 수 없습니다."}

    plan = user.data["plan"]
    gauge = float(user.data.get("gauge_percent", 0))

    # ── Free: 일일 한도 (gauge 사용 안 함) ──
    if plan == "free":
        return await _check_free_daily(user_id, action)

    # ── Pro: 주간 리셋 체크 ──
    if plan == "pro":
        _check_pro_reset(sb, user_id)
        refreshed = sb.table("docflow_users").select("gauge_percent").eq("id", user_id).single().execute()
        gauge = float(refreshed.data.get("gauge_percent", 0)) if refreshed.data else 0

    # ── Plus / Pro 공통: 게이지 차감 ──
    cost_table = GAUGE_COST.get(plan)
    if not cost_table:
        return {"ok": False, "error_code": "UNKNOWN_PLAN", "detail": "알 수 없는 플랜입니다."}

    cost = cost_table.get(action, cost_table.get("mapping", 3.33))

    # 비정상 감지 (Pro만, 주 100회+)
    if plan == "pro":
        weekly = await _get_weekly_usage(user_id)
        if weekly >= 100:
            return {"ok": False, "error_code": "ABUSE_DETECTED",
                    "detail": "비정상적인 사용이 감지되었습니다. 본인 사용이 맞다면 고객센터로 문의해주세요."}

    # 엣지케이스: gauge=0.0이면 거부, gauge>0이면 항상 허용 (마지막 1회 보장)
    if gauge <= 0:
        if plan == "plus":
            return {"ok": False, "error_code": "GAUGE_EMPTY", "plan": "plus",
                    "gauge_pct": 0,
                    "detail": "게이지가 부족합니다. Plus를 추가 구매하거나 Pro로 업그레이드하세요."}
        else:
            return {"ok": False, "error_code": "GAUGE_EMPTY", "plan": "pro",
                    "gauge_pct": 0,
                    "detail": "이번 주 게이지를 모두 사용했습니다. 월요일에 리셋됩니다."}

    # 차감 (동시성 방어: GREATEST로 음수 방지)
    new_gauge = round(max(gauge - cost, 0), 1)
    sb.table("docflow_users").update({"gauge_percent": new_gauge}).eq("id", user_id).execute()
    _log_usage(user_id, action, cost)

    # 스트릭 갱신
    _update_streak(sb, user_id, user.data)

    return {"ok": True, "gauge_pct": new_gauge, "plan": plan, "cost": cost}


# ═══ 게이지 충전 (결제 시) ═══

async def refund_gauge(user_id: str, amount: float):
    """AI 호출 실패 시 차감된 게이지 복구"""
    sb = get_supabase()
    user = sb.table("docflow_users").select("gauge_percent").eq("id", user_id).single().execute()
    if not user.data:
        return
    current = float(user.data.get("gauge_percent", 0))
    sb.table("docflow_users").update({
        "gauge_percent": round(current + amount, 1),
    }).eq("id", user_id).execute()


async def charge_gauge(user_id: str, plan: str):
    """결제 완료 후 게이지 충전"""
    sb = get_supabase()
    user = sb.table("docflow_users").select(
        "gauge_percent, first_purchase_used"
    ).eq("id", user_id).single().execute()

    if not user.data:
        return

    current = float(user.data.get("gauge_percent", 0))
    first = user.data.get("first_purchase_used", False)

    if plan == "plus":
        add = 200.0 if not first else 100.0  # 첫 구매 2배
        defaults = PLAN_DEFAULTS["plus"]
        sb.table("docflow_users").update({
            "plan": "plus",
            "gauge_percent": round(current + add, 1),
            "first_purchase_used": True,
            **defaults,
        }).eq("id", user_id).execute()

    elif plan == "pro":
        defaults = PLAN_DEFAULTS["pro"]
        sb.table("docflow_users").update({
            "plan": "pro",
            "gauge_percent": 100.0,
            **defaults,
        }).eq("id", user_id).execute()


# ═══ 문서 완성 처리 (보상 트리거) ═══

async def on_doc_complete(user_id: str) -> list:
    """문서 완성 시 호출 → 업적/레벨/럭키/스트릭 체크 → 보상 목록 반환"""
    sb = get_supabase()
    rewards = []

    # 완성 카운트 +1
    user = sb.table("docflow_users").select(
        "total_docs_completed, level, streak_days, streak_last_date, gauge_percent, plan"
    ).eq("id", user_id).single().execute()

    if not user.data:
        return rewards

    u = user.data
    total = u.get("total_docs_completed", 0) + 1
    gauge = float(u.get("gauge_percent", 0))
    update = {"total_docs_completed": total}

    # 사용 로그
    _log_usage(user_id, "doc_complete", 0)

    # 1. 업적 체크
    for key, ach in ACHIEVEMENTS.items():
        if total >= ach["condition_docs"]:
            if not _has_achievement(user_id, key):
                _grant_achievement(user_id, key, ach["reward"])
                gauge += ach["reward"]
                rewards.append({"type": "achievement", "label": ach["label"], "reward": ach["reward"]})

    # 2. 레벨 체크
    current_level = u.get("level", 1)
    for lvl in LEVELS:
        if total >= lvl["docs"] and lvl["level"] > current_level:
            update["level"] = lvl["level"]
            if lvl["reward"] > 0:
                ach_key = f"level_{lvl['level']}"
                if not _has_achievement(user_id, ach_key):
                    _grant_achievement(user_id, ach_key, lvl["reward"])
                    gauge += lvl["reward"]
                    rewards.append({"type": "level_up", "label": f"Lv.{lvl['level']} {lvl['title']}", "reward": lvl["reward"]})

    # 3. 스트릭 체크
    today = date.today()
    last = u.get("streak_last_date")
    streak = u.get("streak_days", 0)

    if last:
        last_date = date.fromisoformat(str(last))
        if last_date == today:
            pass  # 오늘 이미 카운트
        elif last_date == today - timedelta(days=1):
            streak += 1
        else:
            # 스트릭 끊김 → 프리즈 체크는 별도
            streak = 1
    else:
        streak = 1

    update["streak_days"] = streak
    update["streak_last_date"] = today.isoformat()

    # 스트릭 보상
    if streak in STREAK_REWARDS:
        reward = STREAK_REWARDS[streak]
        ach_key = f"streak_{streak}"
        if not _has_achievement(user_id, ach_key):
            _grant_achievement(user_id, ach_key, reward)
            gauge += reward
            rewards.append({"type": "streak", "label": f"{streak}일 연속 사용", "reward": reward})

    # 4. 럭키 보너스 (Plus/Pro만)
    if u.get("plan") in ("plus", "pro"):
        roll = random.random()
        for threshold, bonus in LUCKY_TABLE:
            if roll <= threshold:
                if bonus > 0:
                    gauge += bonus
                    rewards.append({"type": "lucky", "label": f"럭키 보너스!", "reward": bonus})
                break

    # 업데이트
    update["gauge_percent"] = round(gauge, 1)
    sb.table("docflow_users").update(update).eq("id", user_id).execute()

    return rewards


# ═══ 매핑 공개 보상 ═══

async def on_mapping_shared(user_id: str) -> dict:
    """매핑 공개 시 +25% 보상"""
    sb = get_supabase()
    user = sb.table("docflow_users").select("gauge_percent").eq("id", user_id).single().execute()
    if not user.data:
        return {}
    gauge = float(user.data.get("gauge_percent", 0)) + 25.0
    sb.table("docflow_users").update({"gauge_percent": round(gauge, 1)}).eq("id", user_id).execute()
    return {"type": "share", "label": "매핑 공개 보상", "reward": 25.0}


# ═══ 추천인 보상 ═══

async def on_referral(referrer_id: str, new_user_id: str):
    """추천인 보상: 추천한 사람 +50%, 받은 사람 +50%"""
    sb = get_supabase()
    for uid, reward in [(referrer_id, 50.0), (new_user_id, 50.0)]:
        user = sb.table("docflow_users").select("gauge_percent").eq("id", uid).single().execute()
        if user.data:
            gauge = float(user.data.get("gauge_percent", 0)) + reward
            sb.table("docflow_users").update({"gauge_percent": round(gauge, 1)}).eq("id", uid).execute()


# ═══ 프로 주간 리셋 ═══

def _check_pro_reset(sb, user_id: str):
    """Pro 유저: 이번 주 월요일 이후 리셋 안 됐으면 자동 리셋 (cron 불필요)"""
    user = sb.table("docflow_users").select(
        "plan, gauge_last_reset"
    ).eq("id", user_id).single().execute()
    if not user.data or user.data["plan"] != "pro":
        return

    today = date.today()
    monday = today - timedelta(days=today.weekday())
    last_reset = user.data.get("gauge_last_reset")

    if last_reset:
        if isinstance(last_reset, str):
            last_reset = date.fromisoformat(last_reset)
        if last_reset >= monday:
            return  # 이미 이번 주 리셋됨

    sb.table("docflow_users").update({
        "gauge_percent": 100.0,
        "streak_freeze_count": 2,
        "gauge_last_reset": monday.isoformat(),
    }).eq("id", user_id).execute()


# ═══ 내부 헬퍼 ═══

async def _check_free_daily(user_id: str, action: str) -> dict:
    """무료 사용자 일일 한도"""
    sb = get_supabase()
    today = date.today().isoformat()
    result = sb.table("docflow_usage_log").select("id").eq(
        "user_id", user_id
    ).eq("action", action).gte("created_at", f"{today}T00:00:00").execute()

    used = len(result.data) if result.data else 0
    limit = FREE_DAILY.get(action, 1)

    # 작성은 재시도 1회 추가
    if action == "generation":
        limit = 2

    if used >= limit:
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        return {
            "ok": False,
            "error_code": "DAILY_LIMIT",
            "plan": "free",
            "detail": f"오늘의 무료 {action} 횟수({limit}회)를 모두 사용했습니다.",
            "reset_at": f"{tomorrow}T00:00:00+09:00",
        }

    _log_usage(user_id, action, 0)

    # 스트릭 갱신
    user_data = sb.table("docflow_users").select(
        "streak_days, streak_last_date, streak_freeze_count, gauge_percent"
    ).eq("id", user_id).single().execute()
    if user_data.data:
        _update_streak(sb, user_id, user_data.data)

    return {"ok": True, "gauge_pct": 0, "plan": "free", "remaining_today": limit - used - 1}


async def _get_weekly_usage(user_id: str) -> int:
    """이번 주 총 사용 횟수 (프로 비정상 감지용)"""
    sb = get_supabase()
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    result = sb.table("docflow_usage_log").select("id").eq(
        "user_id", user_id
    ).gte("created_at", f"{monday.isoformat()}T00:00:00").execute()
    return len(result.data) if result.data else 0


async def check_anon(fingerprint: str, action: str) -> dict:
    """비로그인 사용자 맛보기 체크. 하루 1회만 허용."""
    sb = get_supabase()
    today = date.today().isoformat()

    result = sb.table("docflow_anon_usage").select("id").eq(
        "fingerprint", fingerprint
    ).eq("action", action).gte("created_at", f"{today}T00:00:00").execute()

    used = len(result.data) if result.data else 0

    if used >= 1:
        return {"ok": False, "error_code": "LOGIN_REQUIRED",
                "detail": "AI 기능을 사용하려면 로그인이 필요합니다. 무료 가입으로 하루 3회 사용 가능합니다."}

    sb.table("docflow_anon_usage").insert({
        "fingerprint": fingerprint, "action": action,
    }).execute()

    return {"ok": True}


def _update_streak(sb, user_id: str, user_data: dict):
    """사용일 기준 스트릭 갱신"""
    today_str = date.today().isoformat()
    last_date = user_data.get("streak_last_date")
    streak = user_data.get("streak_days", 0)
    freeze = user_data.get("streak_freeze_count", 0)

    if last_date == today_str:
        return  # 이미 오늘 갱신됨

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    if last_date == yesterday:
        streak += 1
    elif last_date and last_date < yesterday and freeze > 0:
        # 프리즈 사용 (하루 빠졌지만 프리즈로 유지)
        freeze -= 1
    else:
        streak = 1  # 리셋

    update = {
        "streak_days": streak,
        "streak_last_date": today_str,
        "streak_freeze_count": freeze,
    }

    # 스트릭 보상 체크
    reward = STREAK_REWARDS.get(streak, 0)
    if reward > 0:
        gauge = float(user_data.get("gauge_percent", 0))
        update["gauge_percent"] = round(gauge + reward, 1)
        _grant_achievement(user_id, f"streak_{streak}", reward)

    sb.table("docflow_users").update(update).eq("id", user_id).execute()


def _log_usage(user_id: str, action: str, cost: float):
    sb = get_supabase()
    sb.table("docflow_usage_log").insert({
        "user_id": user_id,
        "action": action,
        "gauge_cost": cost,
    }).execute()


# 1회성 업적 (중복 불가)
_ONETIME_ACHIEVEMENTS = {
    "first_purchase", "first_doc", "docs_5", "docs_10",
    "level_2", "level_3", "level_4", "level_5",
}


def _has_achievement(user_id: str, key: str) -> bool:
    """1회성 업적만 중복 체크. 반복 업적(streak, lucky, referral 등)은 항상 False 반환."""
    if key not in _ONETIME_ACHIEVEMENTS:
        return False  # 반복 업적 → 중복 허용
    sb = get_supabase()
    result = sb.table("docflow_achievements").select("id").eq(
        "user_id", user_id
    ).eq("achievement_key", key).execute()
    return bool(result.data)


def _grant_achievement(user_id: str, key: str, reward: float):
    sb = get_supabase()
    try:
        sb.table("docflow_achievements").insert({
            "user_id": user_id,
            "achievement_key": key,
            "gauge_reward": reward,
        }).execute()
    except Exception:
        pass  # DB UNIQUE 위반 시 무시 (1회성 중복 방어)


def _get_level_info(level: int) -> dict:
    for lvl in LEVELS:
        if lvl["level"] == level:
            return lvl
    return LEVELS[0]


# ═══ 추천 코드 생성 ═══

def generate_referral_code() -> str:
    import string
    chars = string.ascii_uppercase + string.digits
    return "EAZY-" + "".join(random.choices(chars, k=6))
