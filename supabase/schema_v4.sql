-- ════════════════════════════════════════════
-- 汗青 HanQing — Schema v4：評分佐證加強
-- ════════════════════════════════════════════

-- ─── 1. politicians 新增量化指標欄位 ────────
ALTER TABLE politicians
  ADD COLUMN IF NOT EXISTS attendance_rate        NUMERIC(5,2),  -- 出席率 %
  ADD COLUMN IF NOT EXISTS interpellation_count   INTEGER DEFAULT 0,  -- 質詢次數
  ADD COLUMN IF NOT EXISTS vote_participation_rate NUMERIC(5,2), -- 投票參與率 %
  ADD COLUMN IF NOT EXISTS factcheck_count        INTEGER DEFAULT 0,  -- 被查核次數
  ADD COLUMN IF NOT EXISTS factcheck_false_count  INTEGER DEFAULT 0,  -- 查核為假次數
  ADD COLUMN IF NOT EXISTS bill_pass_count        INTEGER DEFAULT 0,  -- 提案通過數
  ADD COLUMN IF NOT EXISTS bill_propose_count     INTEGER DEFAULT 0;  -- 提案總數

-- ─── 2. 事實查核結果 ─────────────────────────
CREATE TABLE IF NOT EXISTS factchecks (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  politician_id   UUID        REFERENCES politicians(id) ON DELETE CASCADE,
  claim           TEXT        NOT NULL,        -- 被查核的言論
  verdict         TEXT,                        -- 正確/部分正確/錯誤/誤導/待查
  verdict_en      TEXT,                        -- true/mostly-true/false/misleading
  source_name     TEXT        DEFAULT '台灣事實查核中心',
  source_url      TEXT,
  check_date      DATE,
  summary         TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─── 3. 政見兌現分析（AI 交叉比對結果）───────
CREATE TABLE IF NOT EXISTS pledge_analyses (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  politician_id   UUID        REFERENCES politicians(id) ON DELETE CASCADE,
  pledge_id       UUID        REFERENCES election_pledges(id) ON DELETE CASCADE,
  analysis        TEXT,        -- AI 分析文字
  fulfillment     TEXT,        -- fulfilled / partial / broken / unknown
  evidence        TEXT,        -- 佐證說明
  related_bills   TEXT[],      -- 相關法案 ID
  confidence      INTEGER,     -- 0-100
  analyzed_at     TIMESTAMPTZ DEFAULT NOW()
);

-- ─── 4. 索引 ─────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_factchecks_politician ON factchecks (politician_id);
CREATE INDEX IF NOT EXISTS idx_factchecks_verdict    ON factchecks (verdict_en);
CREATE INDEX IF NOT EXISTS idx_pledge_analyses_pol   ON pledge_analyses (politician_id);
CREATE INDEX IF NOT EXISTS idx_pledge_analyses_status ON pledge_analyses (fulfillment);

-- ─── 5. RLS ──────────────────────────────────
ALTER TABLE factchecks       ENABLE ROW LEVEL SECURITY;
ALTER TABLE pledge_analyses  ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='factchecks' AND policyname='factchecks_public_read') THEN
    CREATE POLICY "factchecks_public_read" ON factchecks FOR SELECT USING (true);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='pledge_analyses' AND policyname='pledge_analyses_public_read') THEN
    CREATE POLICY "pledge_analyses_public_read" ON pledge_analyses FOR SELECT USING (true);
  END IF;
END $$;
