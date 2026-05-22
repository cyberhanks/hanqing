-- ════════════════════════════════
-- 汗青 HanQing — Schema v2 升級
-- 在 Supabase SQL Editor 執行
-- ════════════════════════════════

-- politicians 新增欄位
ALTER TABLE politicians
  ADD COLUMN IF NOT EXISTS consistency_score INTEGER DEFAULT 50,
  ADD COLUMN IF NOT EXISTS fulfill_rate      NUMERIC(5,2),
  ADD COLUMN IF NOT EXISTS response_rate     NUMERIC(5,2),
  ADD COLUMN IF NOT EXISTS total_promises    INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS fulfilled_count   INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS broken_count      INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS stalled_count     INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS total_votes       INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS absent_count      INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS data_source       TEXT,
  ADD COLUMN IF NOT EXISTS last_synced_at    TIMESTAMPTZ;

-- promises 新增欄位
ALTER TABLE promises
  ADD COLUMN IF NOT EXISTS keywords          TEXT[],
  ADD COLUMN IF NOT EXISTS verification_hint TEXT,
  ADD COLUMN IF NOT EXISTS evidence_title    TEXT,
  ADD COLUMN IF NOT EXISTS verified_at       TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS scope             TEXT;

-- 政治獻金
CREATE TABLE IF NOT EXISTS donations (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  politician_id   UUID REFERENCES politicians(id) ON DELETE CASCADE,
  donor_name      TEXT,
  donor_type      TEXT,
  donor_industry  TEXT,
  amount          NUMERIC,
  year            INTEGER,
  source_url      TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 財產申報
CREATE TABLE IF NOT EXISTS asset_declarations (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  politician_id    UUID REFERENCES politicians(id) ON DELETE CASCADE,
  year             INTEGER,
  total_assets     NUMERIC,
  total_debts      NUMERIC,
  net_assets       NUMERIC,
  change_from_prev NUMERIC,
  source_url       TEXT,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- 訂閱推播
CREATE TABLE IF NOT EXISTS subscriptions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email           TEXT NOT NULL UNIQUE,
  politician_ids  UUID[],
  topics          TEXT[],
  frequency       TEXT DEFAULT 'weekly',
  confirmed       BOOLEAN DEFAULT FALSE,
  token           TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- API 金鑰
CREATE TABLE IF NOT EXISTS api_keys (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  key_hash     TEXT UNIQUE NOT NULL,
  name         TEXT,
  email        TEXT,
  tier         TEXT DEFAULT 'free',
  daily_limit  INTEGER DEFAULT 1000,
  usage_today  INTEGER DEFAULT 0,
  last_used_at TIMESTAMPTZ,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_politicians_consistency ON politicians (consistency_score DESC);
CREATE INDEX IF NOT EXISTS idx_politicians_fulfill     ON politicians (fulfill_rate DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_donations_politician    ON donations (politician_id);
CREATE INDEX IF NOT EXISTS idx_donations_industry      ON donations (donor_industry);
CREATE INDEX IF NOT EXISTS idx_asset_politician        ON asset_declarations (politician_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_email     ON subscriptions (email);

-- RLS
ALTER TABLE donations           ENABLE ROW LEVEL SECURITY;
ALTER TABLE asset_declarations  ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions       ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys            ENABLE ROW LEVEL SECURITY;
