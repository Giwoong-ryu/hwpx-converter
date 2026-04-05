-- DocFlow v2 스키마 (게임 메커니즘 + % 게이지)
-- 기존 v1 테이블 삭제 후 재생성

DROP TABLE IF EXISTS docflow_anon_usage CASCADE;
DROP TABLE IF EXISTS docflow_usage_log CASCADE;
DROP TABLE IF EXISTS docflow_users CASCADE;
DROP FUNCTION IF EXISTS update_docflow_updated_at CASCADE;

-- ═══ 사용자 ═══
CREATE TABLE docflow_users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    name TEXT DEFAULT '',
    plan TEXT DEFAULT 'free' CHECK (plan IN ('free', 'plus', 'pro')),

    -- % 게이지 (소수점 1자리, 100.0 = 100%)
    gauge_percent NUMERIC(6,1) DEFAULT 0,

    -- 프리셋
    preset_limit INTEGER DEFAULT 1,  -- free=1, plus=3, pro=무제한(9999)
    mapping_save_limit INTEGER DEFAULT 0,  -- free=0, plus=10, pro=무제한(9999)

    -- 스트릭
    streak_days INTEGER DEFAULT 0,
    streak_last_date DATE,
    streak_freeze_count INTEGER DEFAULT 0,  -- free=0, plus=1, pro=2

    -- 레벨
    level INTEGER DEFAULT 1,
    total_docs_completed INTEGER DEFAULT 0,

    -- 추천
    referral_code TEXT UNIQUE,
    referred_by TEXT,  -- 추천인 코드

    -- Polar
    polar_customer_id TEXT,
    polar_subscription_id TEXT,

    -- 첫 구매 여부
    first_purchase_used BOOLEAN DEFAULT FALSE,

    -- Pro 주간 리셋 추적 (cron 없이 API 호출 시 체크)
    gauge_last_reset DATE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ═══ 사용 로그 ═══
CREATE TABLE docflow_usage_log (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES docflow_users(id) ON DELETE CASCADE,
    action TEXT NOT NULL,  -- 'mapping', 'generation', 'batch', 'doc_complete'
    gauge_cost NUMERIC(4,1) DEFAULT 0,  -- 차감된 %
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_usage_user_date ON docflow_usage_log (user_id, created_at);
CREATE INDEX idx_usage_user_action_date ON docflow_usage_log (user_id, action, created_at);

-- ═══ 비로그인 사용 추적 ═══
CREATE TABLE docflow_anon_usage (
    id BIGSERIAL PRIMARY KEY,
    fingerprint TEXT NOT NULL,
    action TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_anon_fp_date ON docflow_anon_usage (fingerprint, action, created_at);

-- ═══ 프리셋 (내 정보) ═══
CREATE TABLE docflow_presets (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES docflow_users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,  -- "본사 정보", "대표 개인정보" 등
    data JSONB NOT NULL DEFAULT '{}',  -- {회사명: "...", 대표자: "...", ...}
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_preset_user ON docflow_presets (user_id);

-- ═══ 양식 매핑 저장 ═══
CREATE TABLE docflow_saved_mappings (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES docflow_users(id) ON DELETE CASCADE,
    form_name TEXT NOT NULL,  -- "사업계획서_양식.hwpx"
    form_field_count INTEGER DEFAULT 0,
    mappings JSONB NOT NULL DEFAULT '{}',  -- {원본텍스트: 치환텍스트}
    is_public BOOLEAN DEFAULT FALSE,
    likes INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_mapping_user ON docflow_saved_mappings (user_id);
CREATE INDEX idx_mapping_public ON docflow_saved_mappings (is_public, likes DESC);

-- ═══ 업적/보상 기록 ═══
CREATE TABLE docflow_achievements (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES docflow_users(id) ON DELETE CASCADE,
    achievement_key TEXT NOT NULL,  -- 'first_doc', 'docs_5', 'level_2', 'streak_3', 'lucky_10', etc
    gauge_reward NUMERIC(5,1) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 1회성 업적만 중복 방지 (반복 업적은 허용)
CREATE UNIQUE INDEX idx_ach_onetime ON docflow_achievements (user_id, achievement_key)
    WHERE achievement_key IN (
        'first_purchase', 'first_doc', 'docs_5', 'docs_10',
        'level_2', 'level_3', 'level_4', 'level_5'
    );

-- ═══ 좋아요 기록 ═══
CREATE TABLE docflow_likes (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES docflow_users(id) ON DELETE CASCADE,
    mapping_id BIGINT REFERENCES docflow_saved_mappings(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, mapping_id)
);

-- ═══ RLS ═══
ALTER TABLE docflow_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE docflow_usage_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE docflow_anon_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE docflow_presets ENABLE ROW LEVEL SECURITY;
ALTER TABLE docflow_saved_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE docflow_achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE docflow_likes ENABLE ROW LEVEL SECURITY;

-- 정책
CREATE POLICY users_self ON docflow_users FOR SELECT USING (auth.uid() = id);
CREATE POLICY usage_self ON docflow_usage_log FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY preset_self ON docflow_presets FOR ALL USING (auth.uid() = user_id);
CREATE POLICY mapping_self ON docflow_saved_mappings FOR ALL USING (auth.uid() = user_id);
CREATE POLICY mapping_public_read ON docflow_saved_mappings FOR SELECT USING (is_public = true);
CREATE POLICY achievement_self ON docflow_achievements FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY likes_self ON docflow_likes FOR ALL USING (auth.uid() = user_id);
CREATE POLICY anon_backend ON docflow_anon_usage FOR ALL USING (true);

-- ═══ updated_at 트리거 ═══
CREATE OR REPLACE FUNCTION update_docflow_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER docflow_users_updated BEFORE UPDATE ON docflow_users
    FOR EACH ROW EXECUTE FUNCTION update_docflow_updated_at();
CREATE TRIGGER docflow_presets_updated BEFORE UPDATE ON docflow_presets
    FOR EACH ROW EXECUTE FUNCTION update_docflow_updated_at();
CREATE TRIGGER docflow_mappings_updated BEFORE UPDATE ON docflow_saved_mappings
    FOR EACH ROW EXECUTE FUNCTION update_docflow_updated_at();
