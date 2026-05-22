-- ════════════════════════════════════════════
-- 汗青 HanQing — Schema v3：歷史公開行為
-- 在 Supabase SQL Editor 貼上執行
-- ════════════════════════════════════════════

-- ─── 1. 法案（提案/連署）────────────────────
CREATE TABLE IF NOT EXISTS bills (
  id          UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
  bill_no     TEXT,
  title       TEXT    NOT NULL,
  bill_date   DATE,
  term        INTEGER,
  session     INTEGER,
  status      TEXT    DEFAULT 'pending',
  category    TEXT,
  source_url  TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(bill_no, term)
);

-- ─── 2. 政治人物與法案關係 ────────────────────
CREATE TABLE IF NOT EXISTS bill_politicians (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bill_id       UUID REFERENCES bills(id) ON DELETE CASCADE,
  politician_id UUID REFERENCES politicians(id) ON DELETE CASCADE,
  role          TEXT DEFAULT 'proposer',
  UNIQUE(bill_id, politician_id)
);

-- ─── 3. 選舉政見（各屆）───────────────────────
CREATE TABLE IF NOT EXISTS election_pledges (
  id              UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
  politician_id   UUID    REFERENCES politicians(id) ON DELETE CASCADE,
  election_year   INTEGER,
  election_type   TEXT,
  constituency    TEXT,
  pledge_text     TEXT    NOT NULL,
  category        TEXT,
  source          TEXT,
  source_url      TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─── 4. statements 補充欄位 ─────────────────
ALTER TABLE statements
  ADD COLUMN IF NOT EXISTS term        INTEGER,
  ADD COLUMN IF NOT EXISTS session     INTEGER,
  ADD COLUMN IF NOT EXISTS committee   TEXT,
  ADD COLUMN IF NOT EXISTS full_text   TEXT,
  ADD COLUMN IF NOT EXISTS ai_summary  TEXT,
  ADD COLUMN IF NOT EXISTS topics      TEXT[];

-- ─── 5. events 補充欄位 ──────────────────────
ALTER TABLE events
  ADD COLUMN IF NOT EXISTS source_date DATE,
  ADD COLUMN IF NOT EXISTS verified    BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS category    TEXT;

-- ─── 6. 索引 ─────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_bills_term         ON bills (term DESC);
CREATE INDEX IF NOT EXISTS idx_bill_pol_pol       ON bill_politicians (politician_id);
CREATE INDEX IF NOT EXISTS idx_bill_pol_bill      ON bill_politicians (bill_id);
CREATE INDEX IF NOT EXISTS idx_pledges_politician ON election_pledges (politician_id);
CREATE INDEX IF NOT EXISTS idx_pledges_year       ON election_pledges (election_year DESC);
CREATE INDEX IF NOT EXISTS idx_statements_term    ON statements (term DESC);
CREATE INDEX IF NOT EXISTS idx_events_category    ON events (category);

-- ─── 7. RLS ──────────────────────────────────
ALTER TABLE bills              ENABLE ROW LEVEL SECURITY;
ALTER TABLE bill_politicians   ENABLE ROW LEVEL SECURITY;
ALTER TABLE election_pledges   ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='bills' AND policyname='bills_public_read') THEN
    CREATE POLICY "bills_public_read" ON bills FOR SELECT USING (true);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='bill_politicians' AND policyname='bill_pol_public_read') THEN
    CREATE POLICY "bill_pol_public_read" ON bill_politicians FOR SELECT USING (true);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='election_pledges' AND policyname='pledges_public_read') THEN
    CREATE POLICY "pledges_public_read" ON election_pledges FOR SELECT USING (true);
  END IF;
END $$;
