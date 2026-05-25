-- ════════════════════════════════════════════
-- 汗青 HanQing — Schema v5：多維度評分佐證
-- ════════════════════════════════════════════

-- ─── 1. politicians 新增多維度欄位 ──────────
ALTER TABLE politicians
  ADD COLUMN IF NOT EXISTS external_rating       NUMERIC(5,2),  -- NGO 外部評鑑分數 0-100
  ADD COLUMN IF NOT EXISTS sentiment_score       NUMERIC(5,2),  -- 媒體輿情分數 0-100
  ADD COLUMN IF NOT EXISTS vote_share_latest     NUMERIC(5,2),  -- 最近一屆得票率 %
  ADD COLUMN IF NOT EXISTS vote_share_trend      NUMERIC(5,2),  -- 得票率趨勢（正=上升）
  ADD COLUMN IF NOT EXISTS news_positive_ratio   NUMERIC(5,2),  -- 正面新聞比例 %
  ADD COLUMN IF NOT EXISTS voting_align_rate     NUMERIC(5,2),  -- 投票與黨紀一致率 %
  ADD COLUMN IF NOT EXISTS score_breakdown       JSONB;         -- 各維度分數明細

-- ─── 2. 外部評鑑（NGO）─────────────────────
CREATE TABLE IF NOT EXISTS external_ratings (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  politician_id   UUID        REFERENCES politicians(id) ON DELETE CASCADE,
  source          TEXT        NOT NULL,   -- 公督盟/廉政署/其他
  source_url      TEXT,
  score           NUMERIC(5,2),
  grade           TEXT,                   -- A/B/C/D/F 或 優/良/可/劣
  dimension       TEXT,                   -- 問政/出席/廉潔/綜合
  year            INTEGER,
  notes           TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─── 3. 完整投票紀錄（增補） ────────────────
-- votes 表原有，補充欄位
ALTER TABLE votes
  ADD COLUMN IF NOT EXISTS bill_category  TEXT,  -- 預算/法律/其他
  ADD COLUMN IF NOT EXISTS party_line     TEXT,  -- 黨團立場
  ADD COLUMN IF NOT EXISTS deviated       BOOLEAN DEFAULT FALSE;  -- 是否脫黨投票

-- ─── 4. 選舉結果歷史 ─────────────────────────
CREATE TABLE IF NOT EXISTS election_results (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  politician_id   UUID        REFERENCES politicians(id) ON DELETE CASCADE,
  election_year   INTEGER     NOT NULL,
  election_type   TEXT,       -- 立委/縣市長/總統
  constituency    TEXT,
  vote_count      INTEGER,
  vote_share      NUMERIC(5,2),  -- 得票率 %
  total_votes     INTEGER,
  result          TEXT,       -- elected/lost
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(politician_id, election_year, election_type)
);

-- ─── 5. 媒體輿情分析 ─────────────────────────
CREATE TABLE IF NOT EXISTS news_sentiment (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  politician_id   UUID        REFERENCES politicians(id) ON DELETE CASCADE,
  period          TEXT,       -- 2024-Q1 等
  positive_count  INTEGER     DEFAULT 0,
  negative_count  INTEGER     DEFAULT 0,
  neutral_count   INTEGER     DEFAULT 0,
  total_count     INTEGER     DEFAULT 0,
  positive_ratio  NUMERIC(5,2),
  sample_topics   TEXT[],     -- 主要議題標籤
  analyzed_at     TIMESTAMPTZ DEFAULT NOW()
);

-- ─── 6. 索引 ─────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_external_ratings_pol  ON external_ratings (politician_id);
CREATE INDEX IF NOT EXISTS idx_election_results_pol  ON election_results (politician_id);
CREATE INDEX IF NOT EXISTS idx_news_sentiment_pol    ON news_sentiment (politician_id);

-- ─── 7. RLS ──────────────────────────────────
ALTER TABLE external_ratings  ENABLE ROW LEVEL SECURITY;
ALTER TABLE election_results  ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_sentiment    ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='external_ratings' AND policyname='ext_ratings_public_read') THEN
    CREATE POLICY "ext_ratings_public_read" ON external_ratings FOR SELECT USING (true);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='election_results' AND policyname='election_results_public_read') THEN
    CREATE POLICY "election_results_public_read" ON election_results FOR SELECT USING (true);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='news_sentiment' AND policyname='news_sentiment_public_read') THEN
    CREATE POLICY "news_sentiment_public_read" ON news_sentiment FOR SELECT USING (true);
  END IF;
END $$;
