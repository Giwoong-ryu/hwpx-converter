-- DocFlow 결제/크레딧 테이블 (Supabase에서 실행)
-- 기존 qt-make 테이블과 충돌 없음 (docflow_ 접두사)

-- 사용자 프로필 (Supabase auth.users와 연결)
CREATE TABLE IF NOT EXISTS docflow_users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    name TEXT DEFAULT '',
    plan TEXT DEFAULT 'free' CHECK (plan IN ('free', 'starter', 'pro')),
    mapping_credits INTEGER DEFAULT 0,
    generation_credits INTEGER DEFAULT 0,
    polar_subscription_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 사용 로그 (일일 제한 체크 + 분석용)
CREATE TABLE IF NOT EXISTS docflow_usage_log (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES docflow_users(id) ON DELETE CASCADE,
    credit_type TEXT NOT NULL CHECK (credit_type IN ('mapping', 'generation')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_docflow_usage_user_type_date
    ON docflow_usage_log (user_id, credit_type, created_at);

-- 비로그인 사용자 추적 (핑거프린트 기반)
CREATE TABLE IF NOT EXISTS docflow_anon_usage (
    id BIGSERIAL PRIMARY KEY,
    fingerprint TEXT NOT NULL,
    credit_type TEXT NOT NULL CHECK (credit_type IN ('mapping', 'generation')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_docflow_anon_fp_date
    ON docflow_anon_usage (fingerprint, credit_type, created_at);

-- RLS 활성화
ALTER TABLE docflow_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE docflow_usage_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE docflow_anon_usage ENABLE ROW LEVEL SECURITY;

-- 정책: 사용자는 자기 데이터만 읽기
CREATE POLICY docflow_users_self ON docflow_users
    FOR SELECT USING (auth.uid() = id);

-- 서비스 키(백엔드)는 모든 접근 가능 (anon 키로는 본인만)
CREATE POLICY docflow_usage_self ON docflow_usage_log
    FOR SELECT USING (auth.uid() = user_id);

-- anon_usage는 백엔드에서만 접근 (서비스 키)
CREATE POLICY docflow_anon_backend ON docflow_anon_usage
    FOR ALL USING (true);  -- 서비스 키 전용

-- updated_at 자동 갱신
CREATE OR REPLACE FUNCTION update_docflow_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER docflow_users_updated
    BEFORE UPDATE ON docflow_users
    FOR EACH ROW
    EXECUTE FUNCTION update_docflow_updated_at();
